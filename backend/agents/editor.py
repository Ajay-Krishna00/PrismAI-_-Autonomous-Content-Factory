import os
from langchain_google_genai import ChatGoogleGenerativeAI
from .state import GraphState

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))

def run_editor(state:GraphState):
    print("---AGENT 3: EDITOR RUNNING---")
    blog = state.get("draft_copy", "")
    social = state.get("social_draft", "")
    email = state.get("email_draft", "")
    facts=state["source_of_truth"]
    
    prompt=f"""
    You are the Editor-in-Chief. Check these campaign drafts against the Facts.
    If any draft invents any feature not in the facts, REJECT and explain what to fix.
    If all are accurate and safe, APPROVE.
    Start your response with either "APPROVE" or "REJECT".
    
    Facts:
    {facts}

    Blog Draft:
    {blog}

    Social Draft:
    {social}

    Email Draft:
    {email}
    """
    response=llm.invoke(prompt).content
    print(f"Editor response: {response}")
    
    if response.strip().upper().startswith("APPROVE"):
        return {"is_approved": True, "editor_feedback": ""}
    else:
        return {"is_approved": False, "editor_feedback": response}