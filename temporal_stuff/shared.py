from dataclasses import dataclass 
from typing import List,Optional 

ASSISTANT_QUEUE = "ASSISTANT_QUEUE"

@dataclass
class Message:
    message: str
    response: str 

@dataclass
class MessageRequest:
    workflow_id: str
    message: str
    context: Optional[dict] = None

@dataclass
class MessageContext:
    message_info: dict
    context: Optional[dict] = None 
    previous_response: Optional[dict] = None

@dataclass
class WorkflowState:
    intent_detection: dict 
    disambiguate: bool
    system_output: dict
    oos_output: str
    current_message: Message
    chat_history: List
    workflow_id: str
    context: dict
    terminal_id: str
@dataclass
class SuggestionInfo:
    suggestion_type: str
    suggestion_prompt: str

@dataclass
class ExplanationInfo:
    explanation_type: str
    explanation_prompt: str

@dataclass
class RabbitMqQueueParams:
    queue_name: str 
    exchange: str
    message: str
    terminal_id: str

