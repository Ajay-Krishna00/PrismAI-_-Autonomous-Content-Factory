import os
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from .state import GraphState

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))

def run_editor(state: GraphState):
    print("---AGENT 3: EDITOR RUNNING---")
    blog = state.get("draft_copy", "")
    social = state.get("social_draft", "")
    email = state.get("email_draft", "")
    facts = state["source_of_truth"]

    prompt = f"""You are the Editor-in-Chief for a professional marketing agency. Your job is to audit campaign drafts for quality, accuracy, and structure.

Review these campaign drafts against the Source of Truth below.

=== SOURCE OF TRUTH ===
{facts}

=== BLOG DRAFT ===
{blog}

=== SOCIAL DRAFT (LinkedIn Posts) ===
{social}

=== EMAIL DRAFT ===
{email}

=== QUALITY CHECKLIST ===

1.FACTUAL ACCURACY: Reject only for clear hallucinations or contradictions with the Source of Truth.
2. COMPLETENESS: Reject only if a whole channel is missing or unusable.
3. REPETITION: Reject only for repetition that harms readability.
4. STRUCTURE/TONE: Minor structure or tone issues are acceptable and should be noted as improvements, not automatic rejection.

=== YOUR RESPONSE ===
Start with either "APPROVE" or "REJECT".
If REJECT, provide a specific numbered list of issues that need fixing, referencing which channel (Blog/Social/Email) each issue belongs to.
If APPROVE, briefly confirm all checks passed.
"""
    response = llm.invoke(prompt).content
    print(f"Editor response: {response}")

    decision_match = re.search(r"(?mi)^\s*(APPROVE|REJECT)\b", response or "")
    decision = decision_match.group(1).upper() if decision_match else "REJECT"

    if decision == "APPROVE":
        return {"is_approved": True, "editor_feedback": ""}
    else:
        return {"is_approved": False, "editor_feedback": response}