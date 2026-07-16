from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.graph.workflow import graph
from app.models.chat_models import ChatRequest, ChatResponse
from app.services.chat_service import handle_chat, reset_session, stream_chat_events

app = FastAPI(title="AI Travel Planner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "ok", "message": "AI Travel Planner API is running"}


@app.get("/demo")
def run_demo():
    initial_state = {
        "user_query": (
            "Plan a 7 day trip from Delhi to Japan "
            "for 2 people with a budget of 3000 dollars. travel style is anime "
            "will want to travel via plan , want 3 start hotel and like indian food only"
        ),
        "requirements": {},
        "missing_fields": [],
        "research_data": {},
        "travel_plan": {},
        "final_response": "",
    }

    return graph.invoke(initial_state)


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    message = request.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    result = handle_chat(message, request.session_id)

    return ChatResponse(**result)


@app.post("/chat/stream")
def chat_stream(request: ChatRequest):
    message = request.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    return StreamingResponse(
        stream_chat_events(message, request.session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.delete("/chat/{session_id}")
def delete_chat_session(session_id: str):
    if not reset_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    return {"status": "ok"}
