import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.request
import ast
from typing import Literal

from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from .state import GraphState

llm=OllamaLLM(model="llama3:8b-instruct-q4_K_M")
ChannelKey = Literal["blog", "social", "email"]
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


def _parse_json_payload(content: str) -> dict | None:
    text = content.strip()
    if not text:
        return None

    def _load_dict(candidate: str) -> dict | None:
        try:
            data = json.loads(candidate)
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            pass

        # Some models emit Python-style dicts with single quotes.
        try:
            data = ast.literal_eval(candidate)
            return data if isinstance(data, dict) else None
        except (SyntaxError, ValueError):
            return None

    def _extract_brace_fragments(source: str) -> list[str]:
        fragments: list[str] = []
        start_idx = -1
        depth = 0
        in_string = False
        escape = False

        for idx, ch in enumerate(source):
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
                continue

            if ch == "{":
                if depth == 0:
                    start_idx = idx
                depth += 1
                continue

            if ch == "}" and depth > 0:
                depth -= 1
                if depth == 0 and start_idx != -1:
                    fragments.append(source[start_idx : idx + 1])
                    start_idx = -1

        return fragments

    candidates: list[str] = []

    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            candidates.append("\n".join(lines[1:-1]).strip())

    candidates.append(text)
    candidates.extend(_extract_brace_fragments(text))

    for candidate in candidates:
        payload = _load_dict(candidate)
        if payload is not None:
            return payload

    return None


def _has_required_draft_fields(payload: dict) -> bool:
    required_keys = ("blog", "social", "email")
    return all(key in payload for key in required_keys)


def _word_list(text: str) -> list[str]:
    return re.findall(r"\b[\w'-]+\b", text)


def _enforce_blog_500_words(blog: str, value_proposition: str) -> str:
    words = _word_list(blog)
    if len(words) >= 500:
        return " ".join(words[:500])

    filler_seed = _word_list(
        value_proposition
        or "Designed for clarity consistency credibility and conversion across channels"
    )
    if not filler_seed:
        filler_seed = ["campaign", "clarity", "consistency", "value"]

    idx = 0
    while len(words) < 500:
        words.append(filler_seed[idx % len(filler_seed)])
        idx += 1
    return " ".join(words)


def _split_social_posts(text: str) -> list[str]:
    blocks = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
    if len(blocks) >= 2:
        return blocks

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    numbered = [
        line
        for line in lines
        if re.match(r"^(post\s*\d+|\d+[\)\.:\-])", line, re.IGNORECASE)
    ]
    return numbered if numbered else (blocks or [text.strip()])


def _enforce_social_5_posts(social: str, value_proposition: str) -> str:
    posts = _split_social_posts(social)
    posts = [re.sub(r"^(post\s*\d+\s*[:\-]?|\d+[\)\.:\-]\s*)", "", p, flags=re.IGNORECASE).strip() for p in posts]
    posts = [p for p in posts if p]

    if len(posts) > 5:
        posts = posts[:5]

    while len(posts) < 5:
        posts.append(f"{value_proposition or 'Clear value from one source document'}")

    formatted = [f"Post {idx + 1}: {post}" for idx, post in enumerate(posts[:5])]
    return "\n\n".join(formatted)


def _enforce_email_one_paragraph(email: str) -> str:
    paragraph = " ".join(line.strip() for line in email.splitlines() if line.strip())
    paragraph = re.sub(r"\s+", " ", paragraph).strip()
    return paragraph


def _enforce_output_shape(drafts: dict, value_proposition: str) -> dict:
    blog = _enforce_blog_500_words(str(drafts.get("blog", "")).strip(), value_proposition)
    social = _enforce_social_5_posts(str(drafts.get("social", "")).strip(), value_proposition)
    email = _enforce_email_one_paragraph(str(drafts.get("email", "")).strip())
    return {
        "draft_copy": blog,
        "social_draft": social,
        "email_draft": email,
    }


def _normalize_text(value: object, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _fallback_drafts(facts: object, feedback: object) -> dict:
    normalized_facts = _normalize_text(facts, "No facts provided.")
    normalized_feedback = _normalize_text(feedback, "")
    compact_facts = re.sub(r"\s+", " ", normalized_facts).strip()
    compact_feedback = re.sub(r"\s+", " ", normalized_feedback).strip()

    blog_seed = (
        "This campaign is grounded in confirmed product facts and a consistent value proposition. "
        f"{compact_facts}"
    )
    social_seed = (
        "Confirmed highlights only.\n\n"
        f"{compact_facts or 'Reliable performance and premium engineering.'}"
    )
    email_seed = (
        "Hi there, this update shares verified product highlights and keeps the message focused on confirmed facts: "
        f"{compact_facts}"
    )

    if compact_feedback:
        blog_seed = f"{blog_seed} Priority revision focus: {compact_feedback}"

    return _enforce_output_shape(
        {"blog": blog_seed, "social": social_seed, "email": email_seed},
        value_proposition="Single-source truth transformed into channel-ready copy.",
    )


def _summarize_error_payload(payload: str, max_len: int = 220) -> str:
    compact = " ".join(payload.split())
    if len(compact) <= max_len:
        return compact
    return f"{compact[:max_len]}..."


def _groq_request(body: dict, api_key: str) -> str:
    encoded_body = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url="https://api.groq.com/openai/v1/chat/completions",
        data=encoded_body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "PrismAI/1.0",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read().decode("utf-8")
        data = json.loads(raw)

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("Groq response did not include choices.")

    first_choice = choices[0] or {}
    message = first_choice.get("message") or {}
    content = message.get("content")
    finish_reason = str(first_choice.get("finish_reason") or "")

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Groq returned an empty completion.")

    # A truncated completion is a frequent cause of malformed/incomplete JSON.
    if finish_reason == "length":
        raise RuntimeError("Groq completion was truncated (finish_reason=length).")

    return content


def _invoke_groq(prompt: str) -> str:
    # Reload dotenv so backend picks up key/model changes without full process restart.
    load_dotenv(dotenv_path=ENV_PATH, override=True)

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set.")

    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip() or "llama-3.1-8b-instant"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a strict JSON generator."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 2200,
        "response_format": {"type": "json_object"},
    }
    try:
        return _groq_request(payload, api_key=api_key)
    except urllib.error.HTTPError as exc:
        if exc.code != 400:
            raise

        error_payload = ""
        try:
            error_payload = exc.read().decode("utf-8", errors="replace")
        except Exception:
            error_payload = ""

        # Some models may reject response_format JSON mode. Retry without it.
        if "response_format" in error_payload.lower():
            retry_payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a strict JSON generator."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 2200,
            }
            return _groq_request(retry_payload, api_key=api_key)

        raise


def _invoke_local(prompt: str) -> str:
    response = llm.invoke(prompt)
    return response if isinstance(response, str) else str(response)

def run_copywriter(state: GraphState, regenerate_channel: ChannelKey | None = None):
    print("---AGENT 2: COPYWRITER RUNNING---")
    facts = _normalize_text(state.get("source_of_truth"), "No facts provided.")
    feedback = _normalize_text(state.get("editor_feedback"), "")
    value_proposition = state.get("value_proposition") or "Deliver one coherent message across all channels."
    target_audience = state.get("target_audience") or "Marketing and business stakeholders"
    mode = state.get("copywriter_mode", "groq")

    scope_instruction = (
        f"Generate ONLY the {regenerate_channel} field. Set all other fields to an empty string."
        if regenerate_channel
        else "Generate all fields."
    )
    
    prompt = f"""
    You are a Creative Copywriter. Use ONLY the facts provided below.

    Facts:
    {facts}

    Value Proposition (must be the hero in every piece):
    {value_proposition}

    Target Audience:
    {target_audience}

    {f'EDITOR FEEDBACK to fix:\n{feedback}' if feedback else ''}

    Create three outputs:
    1) blog: EXACTLY 500 words. Tone: Professional and trustworthy.
    2) social: EXACTLY 5 posts. Tone: Engaging and punchy.
    3) email: EXACTLY 1 paragraph. Tone: Concise and confident.

    {scope_instruction}

    IMPORTANT RULES:
    - Return ONLY valid JSON.
    - Do not include markdown, code fences, comments, or any extra text.
    - Keep each field strictly separate. Never include social/email text in blog.
    - Keys must be exactly: "blog", "social", "email".

    JSON format:
    {{
      "blog": "...",
      "social": "...",
      "email": "..."
    }}
    """

    try:
        content = ""
        for attempt in range(2):
            content = _invoke_groq(prompt) if mode == "groq" else _invoke_local(prompt)

            payload = _parse_json_payload(content)
            if payload is not None and _has_required_draft_fields(payload):
                normalized = _enforce_output_shape(payload, value_proposition=value_proposition)
                runtime_note = (
                    "Copywriter is running on Groq Cloud Llama-3."
                    if mode == "groq"
                    else "Copywriter is running on local Ollama Llama-3."
                )
                normalized["copywriter_runtime_note"] = runtime_note
                if regenerate_channel is None:
                    return normalized

                if regenerate_channel == "blog" and normalized["draft_copy"]:
                    normalized["social_draft"] = state.get("social_draft") or ""
                    normalized["email_draft"] = state.get("email_draft") or ""
                    return normalized
                if regenerate_channel == "social" and normalized["social_draft"]:
                    normalized["draft_copy"] = state.get("draft_copy") or ""
                    normalized["email_draft"] = state.get("email_draft") or ""
                    return normalized
                if regenerate_channel == "email" and normalized["email_draft"]:
                    normalized["draft_copy"] = state.get("draft_copy") or ""
                    normalized["social_draft"] = state.get("social_draft") or ""
                    return normalized

            # Ask the model once to self-repair malformed output into strict JSON.
            if attempt == 0:
                repair_prompt = f"""
                Convert the following content to strict JSON with exactly these keys: blog, social, email.
                Return only JSON and do not add comments, markdown, or extra keys.

                Content to repair:
                {content}
                """
                repaired = _invoke_groq(repair_prompt) if mode == "groq" else _invoke_local(repair_prompt)
                repaired_payload = _parse_json_payload(repaired)
                if repaired_payload is not None and _has_required_draft_fields(repaired_payload):
                    normalized = _enforce_output_shape(repaired_payload, value_proposition=value_proposition)
                    normalized["copywriter_runtime_note"] = (
                        "Copywriter output required JSON repair before normalization."
                    )
                    if regenerate_channel is None:
                        return normalized

                    if regenerate_channel == "blog" and normalized["draft_copy"]:
                        normalized["social_draft"] = state.get("social_draft") or ""
                        normalized["email_draft"] = state.get("email_draft") or ""
                        return normalized
                    if regenerate_channel == "social" and normalized["social_draft"]:
                        normalized["draft_copy"] = state.get("draft_copy") or ""
                        normalized["email_draft"] = state.get("email_draft") or ""
                        return normalized
                    if regenerate_channel == "email" and normalized["email_draft"]:
                        normalized["draft_copy"] = state.get("draft_copy") or ""
                        normalized["social_draft"] = state.get("social_draft") or ""
                        return normalized

            if attempt == 0:
                # Give local Ollama a moment to finish lazy startup on the first call.
                time.sleep(1)

        print("[WARN] Copywriter returned non-JSON or incomplete JSON. Falling back to template drafts.")
        fallback = _fallback_drafts(facts, feedback)
        fallback["copywriter_runtime_note"] = "Copywriter returned invalid JSON. Drafts were repaired using fallback constraints."
        return fallback

    except Exception as exc:
        error_text = str(exc)
        runtime_note = "Copywriter backend failed. Fallback drafts were generated from source of truth."
        if mode == "local" and ("WinError 10061" in error_text or "Connection refused" in error_text):
            print(
                "[WARN] Ollama is unreachable. Start it with `ollama serve` and ensure "
                "model `llama3:8b-instruct-q4_K_M` is available via `ollama pull`."
            )
            fallback = _fallback_drafts(facts, feedback)
            fallback["copywriter_runtime_note"] = (
                "Local Ollama is unreachable. Switch Hybrid Toggle to Groq Cloud for reliable generation."
            )
            return fallback

        if mode == "groq" and isinstance(exc, urllib.error.HTTPError):
            error_payload = ""
            try:
                error_payload = exc.read().decode("utf-8", errors="replace")
            except Exception:
                error_payload = "<unable to read error body>"

            summarized_payload = _summarize_error_payload(error_payload)

            print(
                f"[WARN] Groq API failed with HTTP status {exc.code}. "
                f"Body: {error_payload}. Falling back to template drafts."
            )
            runtime_note = (
                f"Groq request failed with HTTP {exc.code}. "
                f"Details: {summarized_payload}. Using fallback drafts."
            )
            if exc.code == 401:
                print("[HINT] Unauthorized key. Verify GROQ_API_KEY in backend environment.")
            if exc.code == 403:
                print(
                    "[HINT] Request is forbidden. Most common causes are wrong project/key pairing, "
                    "model access restrictions, or a corporate proxy/security layer returning 403 before Groq."
                )
        else:
            print(f"[WARN] Copywriter LLM failed. Falling back to template drafts. Error: {error_text}")
            runtime_note = f"Copywriter backend failed ({error_text}). Using fallback drafts."

        fallback = _fallback_drafts(facts, feedback)
        fallback["copywriter_runtime_note"] = runtime_note
        return fallback