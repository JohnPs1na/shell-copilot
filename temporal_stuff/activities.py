import pika 

from temporalio import activity 
from temporal_stuff.shared import Message, MessageContext, RabbitMqQueueParams, SuggestionInfo, ExplanationInfo
from dataclasses import dataclass
from classifier.model import *
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import re
from collections import Counter
from temporal_stuff.Chatbot import Chatbot

@dataclass 
class NonRetriableError(Exception):

    def __init__(self,message) -> None:
        self.message: str = message
        super().__init__(self.message)


class Activities:
    
    def __init__(self, intent_classifier = None) -> None:
        self.client_llm = Chatbot()

        with open("../classifier/vocab.pkl","rb") as f:
            self.vocab = pickle.load(f)

        self.label2idx = {"Explain": 0, "Suggest": 1, "Out Of Scope": 2}
        self.intent_classifier = TextClassifier(
            vocab_size=len(self.vocab),
            embedding_dim=embedding_dim,
            hidden_dim=hidden_dim,
            output_dim=3,
            n_layers=n_layers,
            bidirectional=bidirectional,
            dropout=dropout
        )
        self.intent_classifier.load_state_dict(torch.load("../classifier/text_classifier.pt"))
        self.intent_classifier.eval()

    async def get_llm_response(self, message, base_prompt, model_version=""):
        
        return "salut :^)"
    

    @activity.defn
    async def detect_intent(self,msgOBJ):
        test_indices = encode_sentence(msgOBJ["message"], self.vocab)
        test_tensor = torch.tensor(test_indices, dtype=torch.long)
        self.intent_classifier.eval()
        with torch.no_grad():
            output = self.intent_classifier(test_tensor)
            predicted_label = torch.argmax(output, dim=1).item()
            idx2label = {v: k for k, v in self.label2idx.items()}
            print("Predicted label:", idx2label[predicted_label])

        response_obj = {
            "intent":idx2label[predicted_label]
        }

        return response_obj


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
    async def get_suggestion(self, response: dict,user_message:str) -> SuggestionInfo:
        try:
            suggestion = self.client_llm.generate_suggestion(
                user_message
            ).replace("response:","").strip()

            return SuggestionInfo(
                suggestion_type=response["suggestion_type"],
                suggestion_prompt=f"Use: {suggestion}",
            )
        except Exception as e:
            activity.logger.exception("Suggestion Info fail")
            raise


    @activity.defn
    async def get_explanation(self, response: dict, user_message:str) -> ExplanationInfo:
        try:
            explanation = self.client_llm.generate_explanation(
                user_message
            ).replace("response:","").strip()

            return ExplanationInfo(
                explanation_type=response["suggestion_type"],
                explanation_prompt=f"{explanation}",
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