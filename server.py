import json
from http import HTTPStatus
from http.client import HTTPResponse

import uvicorn
from fastapi import FastAPI, Body, Response
from fastapi.middleware.cors import CORSMiddleware
import os

from models.schemas import *

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


@app.post("/suggest")
async def suggest(request:SuggestRequest) -> Response:
    return Response(status_code=HTTPStatus.OK, content=json.dumps({"message": "example suggestion"}))


if __name__ == "__main__":
    uvicorn.run(app="server:app",host='0.0.0.0', port=8080, reload=True)