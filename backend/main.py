from dotenv import load_dotenv
load_dotenv()

import asyncio
import io
import json
import traceback
import zipfile
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from agents.copywriter import run_copywriter
from agents.editor import run_editor
from agents.researcher import run_researcher
from agents.state import GraphState

app = FastAPI(title="PrismAI Content Factory API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CampaignRequest(BaseModel):
    source_material: str
    copywriter_mode: Literal["local", "groq"] = "groq"


class ChannelRegenerateRequest(BaseModel):
    channel: Literal["blog", "social", "email"]
    source_of_truth: str
    value_proposition: str = ""
    target_audience: str = ""
    editor_feedback: str = ""
    draft_copy: str = ""
    social_draft: str = ""
    email_draft: str = ""
    copywriter_mode: Literal["local", "groq"] = "groq"


class ExportCampaignRequest(BaseModel):
    source_of_truth: str = ""
    blog_draft: str = ""
    social_draft: str = ""
    email_draft: str = ""


def _build_initial_state(source_material: str, copywriter_mode: Literal["local", "groq"]) -> GraphState:
    return {
        "source_material": source_material,
        "source_of_truth": None,
        "ambiguity_flags": [],
        "target_audience": None,
        "value_proposition": None,
        "draft_copy": None,
        "social_draft": None,
        "email_draft": None,
        "editor_feedback": None,
        "is_approved": False,
        "revision_count": 0,
        "copywriter_mode": copywriter_mode,
        "copywriter_runtime_note": None,
    }


def _run_campaign_pipeline(initial_state: GraphState, max_revisions: int = 4):
    state: GraphState = {**initial_state}

    researcher_update = run_researcher(state)
    state.update(researcher_update)
    yield "researcher", {**state}

    while state.get("revision_count", 0) < max_revisions:
        state["revision_count"] = state.get("revision_count", 0) + 1
        print(f"---REVISION CYCLE {state['revision_count']}/{max_revisions}---")

        copywriter_update = run_copywriter(state)
        state.update(copywriter_update)
        yield "copywriter", {**state}

        editor_update = run_editor(state)
        state.update(editor_update)
        state["is_approved"] = bool(state.get("is_approved"))
        yield "editor", {**state}

        if state.get("is_approved"):
            break

    return state

@app.get("/")
def read_root():
    return {"status": "Welcome to PrismAI\nBackend is running!"}

@app.post("/api/generate")
async def generate_campaign(request:CampaignRequest):
    try:
        initial_state = _build_initial_state(request.source_material, request.copywriter_mode)
        final_state = None

        for _, state_snapshot in _run_campaign_pipeline(initial_state):
            final_state = state_snapshot

        if final_state is None:
            final_state = initial_state

        return {
            "success": True,
            "facts": final_state.get("source_of_truth"),
            "ambiguity_flags": final_state.get("ambiguity_flags", []),
            "target_audience": final_state.get("target_audience", ""),
            "value_proposition": final_state.get("value_proposition", ""),
            "blog_draft": final_state.get("draft_copy"),
            "social_draft": final_state.get("social_draft"),
            "email_draft": final_state.get("email_draft"),
            "approved": final_state.get("is_approved"),
            "editor_notes": final_state.get("editor_feedback"),
            "revisions": final_state.get("revision_count", 0),
            "copywriter_runtime_note": final_state.get("copywriter_runtime_note", ""),
        }
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/regenerate-channel")
async def regenerate_channel(request: ChannelRegenerateRequest):
    try:
        state: GraphState = {
            "source_material": "",
            "source_of_truth": request.source_of_truth,
            "ambiguity_flags": [],
            "target_audience": request.target_audience,
            "value_proposition": request.value_proposition,
            "draft_copy": request.draft_copy,
            "social_draft": request.social_draft,
            "email_draft": request.email_draft,
            "editor_feedback": request.editor_feedback,
            "is_approved": False,
            "revision_count": 0,
            "copywriter_mode": request.copywriter_mode,
            "copywriter_runtime_note": None,
        }

        drafts = run_copywriter(state, regenerate_channel=request.channel)

        channel_to_field = {
            "blog": "draft_copy",
            "social": "social_draft",
            "email": "email_draft",
        }
        field_name = channel_to_field[request.channel]

        return {
            "success": True,
            "channel": request.channel,
            "content": drafts.get(field_name, ""),
            "draft_copy": drafts.get("draft_copy", request.draft_copy),
            "social_draft": drafts.get("social_draft", request.social_draft),
            "email_draft": drafts.get("email_draft", request.email_draft),
            "copywriter_runtime_note": drafts.get("copywriter_runtime_note", ""),
        }
    except Exception as e:
        print(f"Error regenerating channel: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-stream")
async def generate_campaign_stream(request: CampaignRequest):
    async def event_stream():
        try:
            state = _build_initial_state(request.source_material, request.copywriter_mode)
            last_state = {**state}
            max_revisions = 4

            start_payload = {
                "type": "node_start",
                "node": "researcher",
                "message": "Researcher started.",
            }
            yield f"data: {json.dumps(start_payload)}\n\n"
            await asyncio.sleep(0)

            researcher_update = await asyncio.to_thread(run_researcher, state)
            state.update(researcher_update)
            last_state = {**state}
            researcher_payload = {
                "type": "node_update",
                "node": "researcher",
                "state": last_state,
            }
            yield f"data: {json.dumps(researcher_payload)}\n\n"
            await asyncio.sleep(0)

            while state.get("revision_count", 0) < max_revisions:
                state["revision_count"] = state.get("revision_count", 0) + 1

                revision_payload = {
                    "type": "revision",
                    "message": f"Revision cycle {state['revision_count']}/{max_revisions}",
                    "state": {"revision_count": state["revision_count"]},
                }
                yield f"data: {json.dumps(revision_payload)}\n\n"
                await asyncio.sleep(0)

                copywriter_start_payload = {
                    "type": "node_start",
                    "node": "copywriter",
                    "message": "Copywriter started.",
                }
                yield f"data: {json.dumps(copywriter_start_payload)}\n\n"
                await asyncio.sleep(0)

                copywriter_update = await asyncio.to_thread(run_copywriter, state)
                state.update(copywriter_update)
                last_state = {**state}
                copywriter_payload = {
                    "type": "node_update",
                    "node": "copywriter",
                    "state": last_state,
                }
                yield f"data: {json.dumps(copywriter_payload)}\n\n"
                await asyncio.sleep(0)

                editor_start_payload = {
                    "type": "node_start",
                    "node": "editor",
                    "message": "Editor started.",
                }
                yield f"data: {json.dumps(editor_start_payload)}\n\n"
                await asyncio.sleep(0)

                editor_update = await asyncio.to_thread(run_editor, state)
                state.update(editor_update)
                state["is_approved"] = bool(state.get("is_approved"))
                last_state = {**state}
                editor_payload = {
                    "type": "node_update",
                    "node": "editor",
                    "state": last_state,
                }
                yield f"data: {json.dumps(editor_payload)}\n\n"
                await asyncio.sleep(0)

                if state.get("is_approved"):
                    break

            approved = bool(last_state and last_state.get("is_approved"))
            end_payload = {
                "type": "end",
                "message": "Campaign execution completed successfully." if approved else "Campaign ended without approval after max revisions.",
            }
            yield f"data: {json.dumps(end_payload)}\n\n"
        except Exception as e:
            traceback.print_exc()
            error_payload = {
                "type": "error",
                "message": str(e),
            }
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/export-campaign")
async def export_campaign_kit(request: ExportCampaignRequest):
    try:
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("source_of_truth.md", request.source_of_truth or "")
            archive.writestr("blog_draft.md", request.blog_draft or "")
            archive.writestr("social_thread.txt", request.social_draft or "")
            archive.writestr("email_teaser.txt", request.email_draft or "")

        zip_buffer.seek(0)
        headers = {"Content-Disposition": "attachment; filename=prismai_campaign_kit.zip"}
        return StreamingResponse(zip_buffer, media_type="application/zip", headers=headers)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to export campaign kit: {e}")