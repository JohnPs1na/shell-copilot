from typing import Optional

from pydantic import BaseModel


class BasicRequest(BaseModel):
    message: str

class HelloRequest(BasicRequest):
    pass

class SuggestRequest(BasicRequest):
    pass

