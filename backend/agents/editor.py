import os
from langchain_google_genai import ChatGoogleGenerativeAI
from .state import GraphState

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))

def run_editor(state:GraphState):
    print("---AGENT 3: EDITOR RUNNING---")
    draft=state["draft_copy"]
    facts=state["source_of_truth"]
    
    prompt=f"""
    You are the Editor-in-Chief. Check this Draft against the Facts.
    If the draft invents any features not in the facts, REJECT it and explain what to fix.
    If it is accurate, APPROVE it.
    Start your response with either "APPROVE" or "REJECT".
    
    Facts: {facts}
    Draft: {draft}
    """
    response=llm.invoke(prompt).content
    print(f"Editor response: {response}")
    
    if response.startswith("APPROVE"):
        return {"is_approved": True, "editor_feedback": ""}
    else:
        return {"is_approved": False, "editor_feedback": response}