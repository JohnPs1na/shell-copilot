import pika 

from temporalio import activity 
from shared import Message, MessageContext, RabbitMqQueueParams, SuggestionInfo, ExplanationInfo
from dataclasses import dataclass 
from constants import *


@dataclass 
class NonRetriableError(Exception):

    def __init__(self,message) -> None:
        self.message: str = message
        super().__init__(self.message)


class Activities:
    
    def __init__(self, intent_classifier = None) -> None:
        self.client = "Some LLM IDK Bro"
        self.intent_classifier = intent_classifier

    async def get_llm_response(self, message, base_prompt, model_version=""):
        
        return "salut :^)"
    

    @activity.defn
    async def detect_intent(self,message):
        mock_response_obj = {
            "intent":"suggestion"
        }

        return mock_response_obj


    @activity.defn
    async def analyze_info(self,message_context):
        mock_response_obj = {
            "disambiguate": False,
            "intent":"suggestion",
            "message": message_context,
            "suggestion_type": "shell",
            "suggestion_prompt": "USE: ls -al"
        }
        return mock_response_obj


    @activity.defn
    async def get_suggestion(self, response: dict) -> SuggestionInfo:
        try:
            return SuggestionInfo(
                suggestion_type=response["suggestion_type"],
                suggestion_prompt=response["suggestion_prompt"],
            )
        except Exception as e:
            activity.logger.exception("Suggestion Info fail")
            raise


    @activity.defn
    async def get_explanation(self, response: dict) -> ExplanationInfo:
        try:
            return ExplanationInfo(
                response["explanation_type"],
                response["explanation_prompt"],
            )
        except Exception as e:
            activity.logger.exception("explanation Info fail")
            raise


    @activity.defn
    async def publish_message(self,queue_params: RabbitMqQueueParams) -> None: 
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()
            channel.queue_declare(queue_params.queue_name, True)
            channel.basic_publish(
                exchange=queue_params.exchange,
                routing_key=queue_params.queue_name,
                body=queue_params.message
            )
        except Exception as e:
            activity.logger.exception("Publish Message Failed")
            raise