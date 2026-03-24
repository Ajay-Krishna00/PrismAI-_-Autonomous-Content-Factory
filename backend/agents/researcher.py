import os
from langchain_google_genai import ChatGoogleGenerativeAI
from .state import GraphState

llm=ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
)

def run_researcher(state:GraphState):
    print("---AGENT 1: RESEARCHER RUNNING---")
    print(f"Input URL: {state['source_material']}")
    raw_material=state['source_material']
    
    prompt=f"""
    You are an analytical Lead Researcher.
    Your task is to Extract the core features, facts, and specifications from the following source material.
    If it is a URL, extract the main content, title, and key points.
    
    Source Material:
    {raw_material}
    
    Return the extracted information in a structured format.
    """
    response=llm.invoke(prompt)
    return {"source_of_truth":response.content}
