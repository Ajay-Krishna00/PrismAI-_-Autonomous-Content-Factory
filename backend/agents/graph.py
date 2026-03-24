from langgraph.graph import StateGraph,END
from .state import GraphState
from .researcher import run_researcher
from .editor import run_editor
from .copywriter import run_copywriter

workflow=StateGraph(GraphState)

workflow.add_node("researcher",run_researcher)
workflow.add_node("copywriter",run_copywriter)
workflow.add_node("editor",run_editor)

workflow.set_entry_point("researcher")
workflow.add_edge("researcher","copywriter")
workflow.add_edge("copywriter","editor")

def editor_decision(state:GraphState):
  if state["is_approved"]:
    return "end"
  else:
    return "regenerate"
  
workflow.add_conditional_edges(
  "editor",
  editor_decision,{
    "end":END,
    "regenerate":"copywriter"
  }
)
app_graph=workflow.compile()