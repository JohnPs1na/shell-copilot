import json
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional

import pika
import torch
from temporalio import activity
from transformers import BertTokenizer, BertForSequenceClassification

from temporal_stuff.Chatbot import Chatbot
from temporal_stuff.shared import RabbitMqQueueParams, SuggestionInfo, ExplanationInfo


@dataclass
class NonRetriableError(Exception):
    """Exception class for errors that should not be retried."""
    
    message: str
    
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class Activities:
    """Class containing all Temporal activity implementations for shell copilot.
    
    This class implements activities for:
    - Intent detection
    - Information analysis
    - Suggestion generation
    - Explanation generation
    - Message publishing
    """
    
    def __init__(self, intent_classifier_path: str = "../classifier/text_classifier.pt") -> None:
        """Initialize activities with required components.
        
        Args:
            intent_classifier_path: Path to the pre-trained intent classifier model
        """
        self.client_llm = Chatbot()
        self.predicted_label = ""
        
        # Initialize intent classification components
        self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        self.intent_classifier = BertForSequenceClassification.from_pretrained(
            'bert-base-uncased',
            num_labels=3
        )
        self.intent_classifier.load_state_dict(torch.load(intent_classifier_path))
        self.intent_classifier.eval()
        
        self.label2idx = {"Explain": 0, "Suggest": 1, "Out Of Scope": 2}
        self.idx2label = {0: "explanation", 1: "suggestion", 2: "Out Of Scope"}
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.intent_classifier.to(self.device)

    async def get_llm_response(self, message: str, base_prompt: str, model_version: str = "") -> str:
        """Get a response from the LLM.
        
        Args:
            message: User message
            base_prompt: Base prompt for the LLM
            model_version: Version of the model to use
            
        Returns:
            LLM response as string
        """
        # TODO: Implement actual LLM response logic
        return "salut :^)"
    
    @activity.defn
    async def detect_intent(self, msg_obj: Dict[str, Any]) -> Dict[str, str]:
        """Detect the intent of a user message.
        
        Detects whether the message is asking for a suggestion, 
        an explanation, or is out of scope.
        
        Args:
            msg_obj: Dictionary containing the user message
            
        Returns:
            Dictionary with the detected intent
            
        Raises:
            NonRetriableError: If intent detection fails
        """
        message = msg_obj["message"].lower()
        
        # Simple keyword-based intent detection
        suggestion_keywords = ['how to', 'how do i', 'what command', 'what is the command', 
                              'can you help me', 'show me', "suggest"]
        explanation_keywords = ['what does', 'explain', 'what is', 'what are', 'why', 
                               'meaning of', 'what means', "explain"]
        
        if any(keyword in message for keyword in suggestion_keywords):
            self.predicted_label = "suggestion"
            return {"intent": self.predicted_label}
            
        if any(keyword in message for keyword in explanation_keywords):
            self.predicted_label = "explanation"
            return {"intent": self.predicted_label}
            
        # Model-based intent detection
        encoding = self.tokenizer.encode_plus(
            msg_obj["message"],
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

        try:
            with torch.no_grad():
                outputs = self.intent_classifier(input_ids=input_ids, attention_mask=attention_mask)
                predicted_label = torch.argmax(outputs.logits, dim=1).item()
                activity.logger.info(f"Predicted label: {self.idx2label[predicted_label]}")

            self.predicted_label = self.idx2label[predicted_label]
            return {"intent": self.predicted_label}
        except Exception as e:
            activity.logger.exception("Intent detection failed")
            raise NonRetriableError(f"Intent detection failed: {str(e)}")

    @activity.defn
    async def analyze_info(self, message_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze message context to determine next actions.
        
        Determines whether disambiguation is needed and what type of 
        response to generate.
        
        Args:
            message_context: Context of the user message
            
        Returns:
            Dictionary with analysis results including:
            - disambiguate: Whether disambiguation is needed
            - intent: Detected intent
            - message: Context information
            - suggestion_type/explanation_type: Type of response to generate
            - suggestion_prompt/explanation_prompt: Prompt for response generation
        """
        # TODO: Implement actual analysis logic
        mock_response_obj = {
            "disambiguate": False,
            "intent": self.predicted_label,
            "message": message_context,
            "suggestion_type": "shell",
            "suggestion_prompt": "USE: ls -al",
            "explanation_type": "tech",
            "explanation_prompt": "",
        }
        return mock_response_obj

    @activity.defn
    async def get_suggestion(self, response: Dict[str, Any], user_message: str) -> SuggestionInfo:
        """Generate a suggestion based on user message.
        
        Uses the LLM to generate a command suggestion based on the user's request.
        
        Args:
            response: Response object from analyze_info
            user_message: Original user message
            
        Returns:
            SuggestionInfo object with generated suggestion
            
        Raises:
            NonRetriableError: If suggestion generation fails
        """
        try:
            suggestion = self.client_llm.generate_suggestion(
                user_message
            ).replace("response:", "").strip()

            return SuggestionInfo(
                suggestion_type=response["suggestion_type"],
                suggestion_prompt=suggestion,
            )
        except Exception as e:
            activity.logger.exception("Suggestion generation failed")
            raise NonRetriableError(f"Suggestion generation failed: {str(e)}")

    @activity.defn
    async def get_explanation(self, response: Dict[str, Any], user_message: str) -> ExplanationInfo:
        """Generate an explanation based on user message.
        
        Uses the LLM to generate an explanation for a shell command or concept.
        
        Args:
            response: Response object from analyze_info
            user_message: Original user message
            
        Returns:
            ExplanationInfo object with generated explanation
            
        Raises:
            NonRetriableError: If explanation generation fails
        """
        try:
            explanation = self.client_llm.generate_explanation(
                user_message
            ).replace("response:", "").strip()

            return ExplanationInfo(
                explanation_type=response["explanation_type"],
                explanation_prompt=explanation,
            )
        except Exception as e:
            activity.logger.exception("Explanation generation failed")
            raise NonRetriableError(f"Explanation generation failed: {str(e)}")

    @activity.defn
    async def publish_message(self, queue_params: RabbitMqQueueParams) -> None:
        """Publish a message to RabbitMQ.
        
        Sends a message to the specified RabbitMQ queue.
        
        Args:
            queue_params: Parameters for the RabbitMQ queue
            
        Raises:
            NonRetriableError: If message publishing fails
        """
        connection = None
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()
            channel.queue_declare(queue_params.queue_name, durable=True)
            
            message_body = json.dumps({
                "terminal_id": queue_params.terminal_id,
                "message": queue_params.message
            })
            
            channel.basic_publish(
                exchange=queue_params.exchange,
                routing_key=queue_params.queue_name,
                body=message_body
            )
        except Exception as e:
            activity.logger.exception("Message publishing failed")
            raise NonRetriableError(f"Failed to publish message: {str(e)}")
        finally:
            if connection and connection.is_open:
                connection.close()