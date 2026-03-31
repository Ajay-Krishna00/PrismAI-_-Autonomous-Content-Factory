import os
import json
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from .state import GraphState

llm=ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
)


def _parse_json_payload(content: str) -> dict | None:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        fragment = text[start : end + 1]
        try:
            data = json.loads(fragment)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            return None

    return None


def _build_source_of_truth(core_facts: list[str], value_proposition: str, target_audience: str) -> str:
    facts_text = "\n".join(f"- {fact}" for fact in core_facts) if core_facts else "- No core facts extracted"
    return (
        "SOURCE OF TRUTH\n"
        f"Value Proposition: {value_proposition or 'Not specified'}\n"
        f"Target Audience: {target_audience or 'Not specified'}\n"
        "Core Facts:\n"
        f"{facts_text}"
    )


def _extract_ambiguity_flags(raw_material: str) -> list[str]:
    flags: list[str] = []
    patterns = [
        (r"\b(best|fastest|revolutionary|ultimate|perfect)\b", "Contains broad marketing claim that may need evidence."),
        (r"\bsoon|coming soon|TBD|to be announced\b", "Contains timeline ambiguity."),
        (r"\baffordable|premium pricing|competitive price\b", "Price/value statement is ambiguous without numeric detail."),
    ]
    lowered = raw_material.lower()
    for pattern, message in patterns:
        if re.search(pattern, lowered, re.IGNORECASE):
            flags.append(message)
    return list(dict.fromkeys(flags))


def _fallback_research_result(raw_material: str) -> dict:
    lines = [line.strip(" -\t") for line in raw_material.splitlines() if line.strip()]
    normalized = " ".join(lines) if lines else raw_material.strip()
    if not normalized:
        normalized = "No source material provided."

    core_facts = [normalized]
    ambiguity_flags = _extract_ambiguity_flags(normalized)
    source_of_truth = _build_source_of_truth(
        core_facts=core_facts,
        value_proposition="Reliable, consistent multi-channel campaign output from one source document.",
        target_audience="Marketing teams launching technical products.",
    )

    return {
        "source_of_truth": source_of_truth,
        "ambiguity_flags": ambiguity_flags,
        "value_proposition": "Reliable, consistent multi-channel campaign output from one source document.",
        "target_audience": "Marketing teams launching technical products.",
    }

def run_researcher(state:GraphState):
    print("---AGENT 1: RESEARCHER RUNNING---")
    print(f"Input URL: {state['source_material']}")
    raw_material=state['source_material']
    
    prompt=f"""
    You are an analytical Lead Researcher.
        Your task is to extract core features, facts, and specifications from the following source material.
    If it is a URL, extract the main content, title, and key points.

        Return ONLY valid JSON with this exact shape:
        {{
            "core_facts": ["fact 1", "fact 2"],
            "target_audience": "...",
            "value_proposition": "...",
            "ambiguity_flags": ["flag 1", "flag 2"]
        }}

        Rules:
        - ambiguity_flags must list potentially unclear claims, missing numbers, vague timelines, or unspecified pricing.
        - If no ambiguity exists, return an empty array.
        - Do not output markdown or explanatory text.
    
    Source Material:
    {raw_material}
    
    Return the extracted information in a structured format.
    """
    try:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        payload = _parse_json_payload(content)
        if payload is None:
            print("[WARN] Researcher output was not valid JSON. Falling back to local extraction.")
            return _fallback_research_result(raw_material)

        core_facts_raw = payload.get("core_facts", [])
        core_facts = [str(item).strip() for item in core_facts_raw if str(item).strip()]
        if not core_facts:
            core_facts = [raw_material[:240] if raw_material else "No extractable facts found."]

        value_proposition = str(payload.get("value_proposition", "")).strip()
        target_audience = str(payload.get("target_audience", "")).strip()

        ambiguity_raw = payload.get("ambiguity_flags", [])
        ambiguity_flags = [str(item).strip() for item in ambiguity_raw if str(item).strip()]

        source_of_truth = _build_source_of_truth(
            core_facts=core_facts,
            value_proposition=value_proposition,
            target_audience=target_audience,
        )

        return {
            "source_of_truth": source_of_truth,
            "ambiguity_flags": ambiguity_flags,
            "value_proposition": value_proposition,
            "target_audience": target_audience,
        }
    except Exception as exc:
        error_text = str(exc)
        if "UNEXPECTED_EOF_WHILE_READING" in error_text or "SSL" in error_text:
            print(
                "[WARN] Gemini connection failed (TLS/SSL). "
                "Check network, proxy, firewall, and API reachability. Falling back to local extraction."
            )
        else:
            print(f"[WARN] Researcher LLM failed. Falling back to local extraction. Error: {error_text}")

        return _fallback_research_result(raw_material)
