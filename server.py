import json
from http import HTTPStatus
from http.client import HTTPResponse

import uvicorn
from fastapi import FastAPI, Body, Response
from fastapi.middleware.cors import CORSMiddleware
import os

from models.schemas import *
from temporal_stuff.shared import MessageRequest, ASSISTANT_QUEUE
from temporal_stuff.temporal_client import get_temporal_client
from temporal_stuff.workflows import AssistantWorkflow
app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_origins=["*"],
)

@app.get("/health")
async def health():
    return "OK"


@app.post("/sayhello")
async def sayhello(request:HelloRequest) -> Response:
    return Response(status_code=HTTPStatus.OK, content=json.dumps({"message":"HELLO WORLD"}))


@app.post("/start_workflow")
async def start_workflow(body: MessageRequest):
    client = await get_temporal_client()
    result = await client.execute_workflow(
        AssistantWorkflow.run,
        body,
        id=body.workflow_id,
        task_queue=ASSISTANT_QUEUE
    )
    return result 


@app.post("/send_signal/{workflow_id}")
async def send_signal(workflow_id:str, body: dict=Body(...)):
    client = await get_temporal_client()
    handle = client.get_workflow_handle(workflow_id)
    await handle.signal("submit_user_input",body["user_input"])
    return {"message": "signal sent successfully"}


if __name__ == "__main__":
    uvicorn.run(app="server:app",host='0.0.0.0', port=12345, reload=True)