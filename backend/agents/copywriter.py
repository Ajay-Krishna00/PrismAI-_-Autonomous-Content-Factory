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

llm = OllamaLLM(model="llama3:8b-instruct-q4_K_M")
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


def _sentence_split(text: str) -> list[str]:
    """Split text into sentences, preserving the ending punctuation."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]

def _enforce_blog_word_range(blog: str, value_proposition: str) -> str:
    """Ensure blog is between 400-600 words. Preserve paragraph structure."""
    # Preserve paragraph breaks
    paragraphs = [p.strip() for p in blog.split("\n") if p.strip()]
    full_text = "\n\n".join(paragraphs)
    words = _word_list(full_text)
    word_count = len(words)

    # If already within range, return with clean paragraph formatting
    if 400 <= word_count <= 600:
        return full_text

    # Too long: truncate at a sentence boundary near 600 words
    if word_count > 600:
        sentences = _sentence_split(full_text)
        truncated = []
        running_count = 0
        for sentence in sentences:
            sentence_words = len(_word_list(sentence))
            if running_count + sentence_words > 600 and running_count >= 400:
                break
            truncated.append(sentence)
            running_count += sentence_words
        return " ".join(truncated)

    # Too short: append a closing paragraph (not individual word padding)
    vp = value_proposition or "this product"
    closing_additions = [
        f"\n\nIn conclusion, {vp} represents a significant step forward in its category. "
        f"The combination of thoughtful engineering and user-focused design makes it a compelling "
        f"choice for discerning buyers who refuse to compromise on quality or performance.",

        f"\n\nWhether you are a first-time buyer or an experienced enthusiast, {vp} delivers "
        f"an experience that consistently exceeds expectations. Every detail has been carefully considered "
        f"to ensure that the end result is nothing short of exceptional.",

        f"\n\nLooking ahead, the innovations showcased here set a new benchmark for the industry. "
        f"This is not just another product launch — it is a statement of intent, a promise of excellence "
        f"that will resonate with customers for years to come.",
    ]

    result = full_text
    for addition in closing_additions:
        current_words = len(_word_list(result))
        if current_words >= 400:
            break
        result += addition

    # Final trim if we overshot 600
    final_words = _word_list(result)
    if len(final_words) > 600:
        sentences = _sentence_split(result)
        trimmed = []
        running = 0
        for s in sentences:
            sw = len(_word_list(s))
            if running + sw > 600 and running >= 400:
                break
            trimmed.append(s)
            running += sw
        result = " ".join(trimmed)

    return result


def _parse_social_from_json_array(text: str) -> list[str]:
    """Try to extract post texts from a JSON array of {platform, post} objects."""
    try:
        data = json.loads(text)
        if isinstance(data, list):
            posts = []
            for item in data:
                if isinstance(item, dict):
                    post_text = item.get("post") or item.get("content") or item.get("text") or ""
                    if post_text.strip():
                        posts.append(post_text.strip())
            if posts:
                return posts
    except (json.JSONDecodeError, TypeError):
        pass

    # Also try if the text contains a JSON array embedded in other text
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            if isinstance(data, list):
                posts = []
                for item in data:
                    if isinstance(item, dict):
                        post_text = item.get("post") or item.get("content") or item.get("text") or ""
                        if post_text.strip():
                            posts.append(post_text.strip())
                if posts:
                    return posts
        except (json.JSONDecodeError, TypeError):
            pass

    return []


def _split_social_posts(text: str) -> list[str]:
    """Split social text into individual posts."""
    # First, try to parse as JSON array
    json_posts = _parse_social_from_json_array(text)
    if json_posts:
        return json_posts

    # Split by double newline
    blocks = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
    if len(blocks) >= 2:
        return blocks

    # Split by numbered patterns like "Post 1:", "1)", "1."
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    numbered = []
    current_block = []
    for line in lines:
        if re.match(r"^(post\s*\d+|^\d+[\)\.:\-])", line, re.IGNORECASE):
            if current_block:
                numbered.append(" ".join(current_block))
            current_block = [line]
        else:
            current_block.append(line)
    if current_block:
        numbered.append(" ".join(current_block))

    return numbered if len(numbered) >= 2 else (blocks or [text.strip()])


def _enforce_linkedin_posts(social: str, value_proposition: str, target_audience: str) -> str:
    """Ensure exactly 5 distinct LinkedIn posts. No duplicates."""
    posts = _split_social_posts(social)

    # Strip "Post N:" prefixes
    posts = [re.sub(r"^(post\s*\d+\s*[:\-]?\s*|\d+[\)\.:\-]\s*)", "", p, flags=re.IGNORECASE).strip() for p in posts]
    posts = [p for p in posts if p]

    if len(posts) > 5:
        posts = posts[:5]

    # Generate distinct filler posts instead of duplicating value_proposition
    vp = value_proposition or "innovative solutions for modern challenges"
    ta = target_audience or "professionals"
    filler_templates = [
        f"🚀 Exciting news for {ta}! {vp}. This changes everything about how we approach quality and performance. #Innovation #LinkedIn",
        f"💡 What if one product could redefine your expectations? {vp}. The future is here, and it's impressive. #GameChanger #Tech",
        f"🔥 Breaking new ground: {vp}. For {ta} who demand the best, this is worth paying attention to. #Excellence #Industry",
        f"✨ We're proud to showcase something truly special. {vp}. Built for {ta} who value both form and function. #Premium #Quality",
        f"🎯 Performance meets purpose. {vp}. Designed with {ta} in mind, every detail matters. #Design #Innovation",
    ]

    used_texts = set()
    unique_posts = []
    for p in posts:
        normalized = re.sub(r'\s+', ' ', p.lower().strip())
        if normalized not in used_texts:
            used_texts.add(normalized)
            unique_posts.append(p)

    filler_idx = 0
    while len(unique_posts) < 5 and filler_idx < len(filler_templates):
        filler = filler_templates[filler_idx]
        filler_idx += 1
        normalized = re.sub(r'\s+', ' ', filler.lower().strip())
        if normalized not in used_texts:
            used_texts.add(normalized)
            unique_posts.append(filler)

    formatted = [f"Post {idx + 1}: {post}" for idx, post in enumerate(unique_posts[:5])]
    return "\n\n".join(formatted)

def _enforce_email_structure(email: str, target_audience: str) -> str:
    """Ensure email has proper structure: Subject, Salutation, Body, Regards."""
    text = email.strip()
    if not text:
        return text

    # Check if email already has a subject line
    has_subject = bool(re.match(r'^subject\s*:', text, re.IGNORECASE))

    # Check if it has a salutation
    has_salutation = bool(re.search(r'^(dear|hello|hi|greetings)\b', text, re.IGNORECASE | re.MULTILINE))

    # Check if it has a sign-off
    has_regards = bool(re.search(r'(regards|sincerely|best wishes|thank you|warm regards|cheers)', text, re.IGNORECASE))

    # If all parts present, just clean up
    if has_subject and has_salutation and has_regards:
        return text

    audience = target_audience or "Valued Customer"
    parts = []

    # Add subject if missing
    if not has_subject:
        # Try to extract a subject from the first line if it looks like one
        first_line = text.split('\n')[0].strip()
        if len(first_line) < 100 and not first_line.startswith(('Dear', 'Hello', 'Hi')):
            parts.append(f"Subject: {first_line}")
            text = '\n'.join(text.split('\n')[1:]).strip()
        else:
            parts.append("Subject: An Exciting Update You Don't Want to Miss")
    else:
        # Extract existing subject
        subject_match = re.match(r'^(subject\s*:.*?)(?:\n|$)', text, re.IGNORECASE)
        if subject_match:
            parts.append(subject_match.group(1).strip())
            text = text[subject_match.end():].strip()

    # Add salutation if missing
    if not has_salutation:
        parts.append(f"\nDear {audience},")
    
    # Add body
    body = text.strip()
    if body:
        parts.append(f"\n{body}")

    # Add sign-off if missing
    if not has_regards:
        parts.append("\n\nWe look forward to hearing from you.\n\nWarm Regards,\nPrismAI Marketing Team")

    return "\n".join(parts)

def _enforce_output_shape(drafts: dict, value_proposition: str, target_audience: str = "") -> dict:
    blog = _enforce_blog_word_range(str(drafts.get("blog", "")).strip(), value_proposition)
    social = _enforce_linkedin_posts(str(drafts.get("social", "")).strip(), value_proposition, target_audience)
    email = _enforce_email_structure(str(drafts.get("email", "")).strip(), target_audience)
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


def _clip_for_prompt(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}\n\n[Truncated for model input length safety]"

def _fallback_drafts(facts: object, feedback: object, target_audience: str = "", value_proposition: str = "") -> dict:
    normalized_facts = _normalize_text(facts, "No facts provided.")
    normalized_feedback = _normalize_text(feedback, "")
    compact_facts = re.sub(r"\s+", " ", normalized_facts).strip()
    compact_feedback = re.sub(r"\s+", " ", normalized_feedback).strip()
    vp = value_proposition or "Single-source truth transformed into channel-ready copy."
    ta = target_audience or "Valued Customer"

    blog_seed = (
        "Understanding the Product\n\n"
        "This campaign is grounded in confirmed product facts and a consistent value proposition. "
        f"{compact_facts}\n\n"
        "The product represents a carefully engineered solution designed to meet the specific needs "
        "of its target audience. Every feature has been thoughtfully developed to deliver maximum value."
    )
    social_seed = (
        f"Post 1: 🚀 Exciting news! {vp} Check this out! #Innovation\n\n"
        f"Post 2: 💡 Here are the confirmed facts: {compact_facts[:150]}... #Quality\n\n"
        f"Post 3: 🔥 Looking for something exceptional? {vp} #Excellence\n\n"
        f"Post 4: ✨ Built for {ta}. {vp} #Premium\n\n"
        f"Post 5: 🎯 Performance meets purpose. {vp} #Design"
    )
    email_seed = (
        f"Subject: Exciting Product Update\n\n"
        f"Dear {ta},\n\n"
        f"We are thrilled to share some exciting updates with you. {compact_facts}\n\n"
        f"{vp}\n\n"
        f"We look forward to hearing from you.\n\n"
        f"Warm Regards,\nPrismAI Marketing Team"
    )

    if compact_feedback:
        blog_seed = f"{blog_seed}\n\nPriority revision focus: {compact_feedback}"

    return _enforce_output_shape(
        {"blog": blog_seed, "social": social_seed, "email": email_seed},
        value_proposition=vp,
        target_audience=ta,
    )


def _summarize_error_payload(payload: str, max_len: int = 220) -> str:
    compact = " ".join(payload.split())
    if len(compact) <= max_len:
        return compact
    return f"{compact[:max_len]}..."


def _coerce_positive_int(value: str | None, default: int) -> int:
    try:
        parsed = int(str(value).strip())
        return parsed if parsed > 0 else default
    except (TypeError, ValueError):
        return default


def _is_local_unreachable_error(error_text: str) -> bool:
    lowered = (error_text or "").lower()
    unreachable_signals = (
        "winerror 10061",
        "connection refused",
        "failed to connect",
        "connection error",
        "max retries exceeded",
        "errno 111",
        "ollama",
    )
    return any(signal in lowered for signal in unreachable_signals)


def _attach_runtime_metadata(payload: dict, runtime_note: str, mode: Literal["local", "groq"]) -> dict:
    payload["copywriter_runtime_note"] = runtime_note
    payload["copywriter_mode"] = mode
    return payload


def _extract_retry_after_seconds(exc: urllib.error.HTTPError, error_payload: str) -> float | None:
    header_value = exc.headers.get("Retry-After") if exc.headers else None
    if header_value:
        try:
            header_seconds = float(header_value)
            if header_seconds > 0:
                return header_seconds
        except ValueError:
            pass

    payload_match = re.search(r"try again in\s*([0-9]+(?:\.[0-9]+)?)s", error_payload, re.IGNORECASE)
    if payload_match:
        try:
            payload_seconds = float(payload_match.group(1))
            if payload_seconds > 0:
                return payload_seconds
        except ValueError:
            return None

    return None


def _groq_request_with_rate_limit_retry(body: dict, api_key: str) -> str:
    max_retries = _coerce_positive_int(os.getenv("GROQ_RATE_LIMIT_RETRIES", "1"), 1)
    min_wait_seconds = _coerce_positive_int(os.getenv("GROQ_RATE_LIMIT_WAIT_SECONDS", "40"), 40)

    attempt = 0
    while True:
        try:
            return _groq_request(body, api_key=api_key)
        except urllib.error.HTTPError as exc:
            error_payload = ""
            try:
                error_payload = exc.read().decode("utf-8", errors="replace")
            except Exception:
                error_payload = ""

            # HTTPError payload streams can only be read once; preserve for outer handlers.
            setattr(exc, "prismai_error_payload", error_payload)

            if exc.code != 429 or attempt >= max_retries:
                raise

            retry_after_seconds = _extract_retry_after_seconds(exc, error_payload)
            wait_seconds = max(float(min_wait_seconds), retry_after_seconds or 0.0)

            print(
                f"[WARN] Groq rate limit hit (HTTP 429). Waiting {wait_seconds:.1f}s "
                f"before retry {attempt + 1} of {max_retries}."
            )
            time.sleep(wait_seconds)
            attempt += 1

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

    with urllib.request.urlopen(request, timeout=60) as response:
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

    if finish_reason == "length":
        raise RuntimeError("Groq completion was truncated (finish_reason=length).")

    return content


def _invoke_groq(prompt: str) -> str:
    load_dotenv(dotenv_path=ENV_PATH, override=True)

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set.")

    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip() or "llama-3.1-8b-instant"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a strict JSON generator. Return ONLY valid JSON, no markdown, no commentary."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 3500,
        "response_format": {"type": "json_object"},
    }
    try:
        return _groq_request_with_rate_limit_retry(payload, api_key=api_key)
    except urllib.error.HTTPError as exc:
        if exc.code != 400:
            raise

        error_payload = getattr(exc, "prismai_error_payload", "")
        if not error_payload:
            try:
                error_payload = exc.read().decode("utf-8", errors="replace")
            except Exception:
                error_payload = ""

        if "response_format" in error_payload.lower():
            retry_payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a strict JSON generator. Return ONLY valid JSON, no markdown, no commentary."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 3500,
            }
            return _groq_request_with_rate_limit_retry(retry_payload, api_key=api_key)

        # HTTPError payload streams can only be read once; stash it for outer handlers.
        setattr(exc, "prismai_error_payload", error_payload)
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
    facts_for_prompt = _clip_for_prompt(facts, max_chars=14000)
    feedback_for_prompt = _clip_for_prompt(feedback, max_chars=2500)
    print(f"Copywriter received {len(facts_for_prompt)} chars of facts and {len(feedback_for_prompt)} chars of feedback for prompt.")

    scope_instruction = (
        f"Generate ONLY the {regenerate_channel} field. Set all other fields to an empty string."
        if regenerate_channel
        else "Generate all three fields."
    )

    prompt = f"""
You are a Creative Copywriter for a professional marketing agency.
Use ONLY the facts provided below. Do NOT invent or embellish any features, specs, or claims.

=== SOURCE OF TRUTH ===
{facts_for_prompt}

=== VALUE PROPOSITION (must be the hero in every piece) ===
{value_proposition}

=== TARGET AUDIENCE ===
{target_audience}

{f'=== EDITOR FEEDBACK (fix these issues) ===\\n{feedback_for_prompt}' if feedback_for_prompt else ''}

=== INSTRUCTIONS ===
{scope_instruction}

Generate three content pieces as a JSON object with keys "blog", "social", "email":

1. "blog" — A PROFESSIONAL blog article (400-600 words).
   Tone: Professional and Trustworthy.
   Structure: Start with a compelling title on the first line, then use \\n\\n between paragraphs.
   Include an introduction paragraph, 2-3 body paragraphs exploring different aspects, and a conclusion paragraph.
   Do NOT repeat the same sentence or phrase multiple times.

2. "social" — EXACTLY 5 LinkedIn posts, each on a different angle/theme.
   Tone: Engaging and Punchy.
   Format each as "Post N: <content>" separated by \\n\\n.
   Each post should be 1-3 sentences, include relevant hashtags, and feel distinct.
   Do NOT make posts identical or near-identical to each other.

3. "email" — A complete marketing email.
   Tone: Concise and Confident.
   Structure it as:
   Subject: <compelling subject line>\\n\\nDear <target audience>,\\n\\n<introduction paragraph>\\n\\n<body with key benefits>\\n\\n<conclusion with call to action>\\n\\nWarm Regards,\\nPrismAI Marketing Team

CRITICAL RULES:
- Return ONLY valid JSON. No markdown fences, no comments, no extra text.
- Keys must be exactly: "blog", "social", "email".
- Each value must be a string (not an array or object).
- Do not repeat the same sentence more than once across any single piece.

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
                normalized = _enforce_output_shape(payload, value_proposition=value_proposition, target_audience=target_audience)
                runtime_note = (
                    "Copywriter is running on Groq Cloud Llama-3."
                    if mode == "groq"
                    else "Copywriter is running on local Ollama Llama-3."
                )
                _attach_runtime_metadata(normalized, runtime_note, mode)
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

            # Ask the model to self-repair malformed output
            if attempt == 0:
                repair_prompt = f"""
Convert the following content to strict JSON with exactly these keys: blog, social, email.
Each value must be a string. Return only JSON, no comments, markdown, or extra keys.

Content to repair:
{content}
"""
                repaired = _invoke_groq(repair_prompt) if mode == "groq" else _invoke_local(repair_prompt)
                repaired_payload = _parse_json_payload(repaired)
                if repaired_payload is not None and _has_required_draft_fields(repaired_payload):
                    normalized = _enforce_output_shape(repaired_payload, value_proposition=value_proposition, target_audience=target_audience)
                    _attach_runtime_metadata(
                        normalized,
                        "Copywriter output required JSON repair before normalization.",
                        mode,
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
                time.sleep(1)

        print("[WARN] Copywriter returned non-JSON or incomplete JSON. Falling back to template drafts.")
        fallback = _fallback_drafts(facts, feedback, target_audience, value_proposition)
        _attach_runtime_metadata(
            fallback,
            "Copywriter returned invalid JSON. Drafts were repaired using fallback constraints.",
            mode,
        )
        return fallback

    except Exception as exc:
        error_text = str(exc)
        runtime_note = "Copywriter backend failed. Fallback drafts were generated from source of truth."
        if mode == "local" and _is_local_unreachable_error(error_text):
            print(
                "[WARN] Ollama is unreachable. Start it with `ollama serve` and ensure "
                "model `llama3:8b-instruct-q4_K_M` is available via `ollama pull`."
            )
            switch_note = "Local Ollama is unreachable or not installed. Automatically switched to Groq Cloud Llama."
            failover_state: GraphState = {**state, "copywriter_mode": "groq", "copywriter_runtime_note": switch_note}

            try:
                failover_result = run_copywriter(failover_state, regenerate_channel=regenerate_channel)
                existing_note = _normalize_text(failover_result.get("copywriter_runtime_note"), "")
                combined_note = f"{switch_note} {existing_note}".strip() if existing_note else switch_note
                _attach_runtime_metadata(failover_result, combined_note, "groq")
                return failover_result
            except Exception as failover_exc:
                print(f"[WARN] Groq failover after local outage failed: {failover_exc}")
                fallback = _fallback_drafts(facts, feedback, target_audience, value_proposition)
                _attach_runtime_metadata(
                    fallback,
                    f"{switch_note} Groq failover also failed; using fallback drafts.",
                    "groq",
                )
                return fallback

        if mode == "groq" and isinstance(exc, urllib.error.HTTPError):
            error_payload = getattr(exc, "prismai_error_payload", "")
            if not error_payload:
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

        fallback = _fallback_drafts(facts, feedback, target_audience, value_proposition)
        _attach_runtime_metadata(fallback, runtime_note, mode)
        return fallback