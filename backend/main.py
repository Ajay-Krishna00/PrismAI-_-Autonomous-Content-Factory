from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents.graph import app_graph
import traceback
app=FastAPI(title="PrismAI Content Factory API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CampaignRequest(BaseModel):
    source_material: str

@app.get("/")
def read_root():
    return {"status": "Welcome to PrismAI\nBackend is running!"}

@app.post("/api/generate")
async def generate_campaign(request:CampaignRequest):
    try:
        initial_state={
            "source_material":request.source_material,
            "source_of_truth":None,
            "draft_copy":None,
            "editor_feedback":None,
            "is_approved":False
        }
        print("starting LangGraph Flow")

        final_state=app_graph.invoke(initial_state)

        return {
            "success":True,
            "facts":final_state.get("source_of_truth"),
            "blog_draft":final_state.get("draft_copy"),
            "approved":final_state.get("is_approved"),
            "editor_notes":final_state.get("editor_feedback")
        }
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500,detail=str(e))