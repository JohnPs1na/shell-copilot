import pika 

from temporalio import activity 
from temporal_stuff.shared import Message, MessageContext, RabbitMqQueueParams, SuggestionInfo, ExplanationInfo
from dataclasses import dataclass
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from temporal_stuff.Chatbot import Chatbot

@dataclass 
class NonRetriableError(Exception):

    def __init__(self,message) -> None:
        self.message: str = message
        super().__init__(self.message)


class Activities:
    
    def __init__(self, intent_classifier = None) -> None:
        self.client_llm = Chatbot()

        self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        self.intent_classifier = BertForSequenceClassification.from_pretrained(
            'bert-base-uncased',
            num_labels=3
        )
        self.intent_classifier.load_state_dict(torch.load("../classifier/text_classifier.pt"))
        self.intent_classifier.eval()
        
        self.label2idx = {"Explain": 0, "Suggest": 1, "Out Of Scope": 2}
        self.idx2label = {0: "Explain", 1: "Suggest", 2: "Out Of Scope"}
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.intent_classifier.to(self.device)

    async def get_llm_response(self, message, base_prompt, model_version=""):
        
        return "salut :^)"
    

    @activity.defn
    async def detect_intent(self,msgOBJ):

        encoding = self.tokenizer.encode_plus(
            msgOBJ["message"],
            add_special_tokens=True,
            max_length=128,
            return_token_type_ids=False,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)

        with torch.no_grad():
            outputs = self.intent_classifier(input_ids=input_ids, attention_mask=attention_mask)
            predicted_label = torch.argmax(outputs.logits, dim=1).item()
            print("Predicted label:", self.idx2label[predicted_label])

        response_obj = {
            "intent":self.idx2label[predicted_label]
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