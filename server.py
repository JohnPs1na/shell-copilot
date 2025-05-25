import json
from http import HTTPStatus
from http.client import HTTPResponse
import uuid

import uvicorn
from fastapi import FastAPI, Body, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
import os

from models.schemas import *
from temporal_stuff.shared import Message, MessageRequest, ASSISTANT_QUEUE
from temporal_stuff.temporal_client import get_temporal_client
from temporal_stuff.workflows import AssistantWorkflow
from database.database import engine, SessionLocal
from sqlalchemy.orm import Session as SqlAlchemySession
from typing import Annotated
from database.models import *

app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_origins=["*"],
)


def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[SqlAlchemySession, Depends(get_db_session)]


class ChatResponse(BaseModel):
    user_message: Message
    intent_detection: dict
    system_output: dict

@app.get("/health")
async def health():
    return "OK"


@app.post("/sayhello")
async def sayhello(request:HelloRequest) -> Response:
    return Response(status_code=HTTPStatus.OK, content=json.dumps({"message":"HELLO WORLD"}))


@app.post("/start_workflow")
async def start_workflow(body: MessageRequest, db: db_dependency) -> ChatResponse:
    active_session = db.query(Session).filter(Session.is_active).first() 

    if "new session" in body.message.lower():
        if active_session:
            active_session.is_active = False
            db.commit()

        session_id = str(uuid.uuid4())
        session = Session(session_id=session_id)
        db.add(session)
        db.commit()
        active_session = session

        chat = Chat(
            session_id=session_id,
            user_message=body.message,
            assistant_response="Starting new session",
            intent="new session",
        )
        db.add(chat)
        db.commit()

        return ChatResponse(
            user_message=Message(message=body.message,response="Starting new session"),
            intent_detection={"intent": "new session"},
            system_output={},
        )

    elif not active_session:
        session_id = str(uuid.uuid4())
        session = Session(session_id=session_id)
        db.add(session)
        db.commit()
        active_session = session

    client = await get_temporal_client()
    result = await client.execute_workflow(
        AssistantWorkflow.run,
        body,
        id=body.workflow_id,
        task_queue=ASSISTANT_QUEUE
    )

    system_intent = result.intent_detection["intent"]
    response = ChatResponse(
        user_message=Message(message=result.current_message.message,response=""),
        intent_detection={"intent":system_intent},
        system_output=result.system_output
    )

    chat = Chat(
        session_id=active_session.session_id,
        user_message=result.current_message.message,
        assistant_response=result.system_output["suggestion_prompt"] if system_intent == "suggestion" else result.system_output["explanation_prompt"],
        intent=result.intent_detection["intent"],
    )
    db.add(chat)
    db.commit()

    return response 


@app.post("/send_signal/{workflow_id}")
async def send_signal(workflow_id:str, body: dict=Body(...)):
    client = await get_temporal_client()
    handle = client.get_workflow_handle(workflow_id)
    await handle.signal("submit_user_input",body["user_input"])
    return {"message": "signal sent successfully"}


if __name__ == "__main__":
    uvicorn.run(app="server:app",host='0.0.0.0', port=12345, reload=True)