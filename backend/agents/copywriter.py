from langchain_ollama import OllamaLLM
from .state import GraphState

llm=OllamaLLM(model="llama3:8b-instruct-q4_K_M")

def run_copywriter(state: GraphState):
    print("---AGENT 2: COPYWRITER RUNNING---")
    facts = state["source_of_truth"]
    feedback = state.get("editor_feedback", "")
    
    prompt = f"""
    You are a Creative Copywriter. Write a 200-word engaging marketing blog based ONLY on these facts:
    Facts: {facts}
    
    {f'EDITOR FEEDBACK to fix: {feedback}' if feedback else ''}
    """
    
    response = llm.invoke(prompt)
    
    return {"draft_copy": response}