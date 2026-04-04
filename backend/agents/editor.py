import os
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
1. FACTUAL ACCURACY: Does any draft invent features, specs, or claims NOT in the Source of Truth? If yes, REJECT.
2. REPETITION: Are there sentences or phrases repeated multiple times within the same piece? If yes, REJECT.
3. BLOG STRUCTURE: Does the blog have a clear title, introduction, body paragraphs, and conclusion? Is the tone Professional and Trustworthy?
4. SOCIAL STRUCTURE: Are there 5 distinct LinkedIn posts with different angles? Is the tone Engaging and Punchy? Are any posts near-identical to each other?
5. EMAIL STRUCTURE: Does the email have a Subject line, Salutation, Introduction, Body, Conclusion with CTA, and Sign-off? Is the tone Concise and Confident?
6. TONE AUDIT: Is the language appropriate for each channel? Not too "salesy" or "robotic"?

=== YOUR RESPONSE ===
Start with either "APPROVE" or "REJECT".
If REJECT, provide a specific numbered list of issues that need fixing, referencing which channel (Blog/Social/Email) each issue belongs to.
If APPROVE, briefly confirm all checks passed.
"""
    response = llm.invoke(prompt).content
    print(f"Editor response: {response}")

    if response.strip().upper().startswith("APPROVE"):
        return {"is_approved": True, "editor_feedback": ""}
    else:
        return {"is_approved": False, "editor_feedback": response}