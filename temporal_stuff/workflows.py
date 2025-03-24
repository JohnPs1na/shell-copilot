import asyncio 
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from temporal_stuff.activities import Activities
    from temporal_stuff.shared import Message, MessageRequest, MessageContext, WorkflowState, RabbitMqQueueParams, ASSISTANT_QUEUE


@workflow.defn
class AssistantWorkflow:

    def __init__(self) -> None:
        self.pending_message_queue: asyncio.Queue[str] = asyncio.Queue()
        self._exit = False 
        self.workflow_state = WorkflowState(
            intent_detection={},
            disambiguate={},
            oos_output="",
            system_output="",
            current_message=None,
            chat_history=[],
            workflow_id=None,
            context={}
        )
    
    @workflow.query(name="get_status")
    def get_status(self) -> WorkflowState:
        return self.workflow_state
    
    @workflow.signal
    async def submit_user_input(self,m:str) -> None:
        await self.pending_message_queue.put(m)
    

    @workflow.signal
    def exit(self) -> None:
        self._exit = True

    @workflow.run
    async def run(self, request: MessageRequest) -> WorkflowState:
        print("Start Workflow...")
        self.workflow_state.current_message = Message(message=request.message,response="")
        self.workflow_state.workflow_id = request.workflow_id
        self.workflow_state.context = request.context

        retry_policy = RetryPolicy(
            maximum_attempts=3,
            maximum_interval=timedelta(seconds=2)
        )

        user_input:str = None # used to receive signals on different stages of the workflow state

        
        # ACTIVITY INTENT
        message_info = await workflow.execute_activity_method(
            Activities.detect_intent,
            self.workflow_state.current_message,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=retry_policy
        )

        self.workflow_state.intent_detection = message_info

        print(f"message info:{message_info}")

        # HANDLE OOS 
        if message_info['intent'] == "out-of-scope":
            print(self.workflow_state)
            self.workflow_state.current_message.response = "I can't help you"
            print("Terminating...")
            return self.workflow_state
        

        message_context = MessageContext(
            message_info=message_info,
            context=self.workflow_state.context
        )


        response = await workflow.execute_activity_method(
            Activities.analyze_info,
            message_context,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=retry_policy
        )

        print(f"response: {response}")

        self.workflow_state.disambiguate = response["disambiguate"]

        while self.workflow_state.disambiguate:

            history_query = Message(
                message=self.workflow_state.current_message.message,
                response=self.workflow_state.current_message.response
            )

            queue_params = RabbitMqQueueParams(
                queue_name=self.workflow_state.workflow_id,
                exchange="",
                message=response["message"]
            )

            await workflow.execute_activity_method(
                Activities.publish_message,
                queue_params,
                start_to_close_timeout=timedelta(seconds=5),
                retry_policy=retry_policy
            )

            self.workflow_state.chat_history.append(history_query)
            await workflow.wait_condition(
                lambda: not self.pending_message_queue.empty() or self._exit
            )

            while not self.pending_message_queue.empty():
                message = self.pending_message_queue.get_nowait()
                print(f"User input for clarification: {message}")

                self.workflow_state.current_message.message=message

                clarifying_message_info = await workflow.execute_activity_method(
                    Activities.detect_intent,
                    self.workflow_state.current_message,
                    start_to_close_timeout=timedelta(seconds=10),
                    retry_policy=retry_policy
                )

                self.workflow_state.intent_detection = clarifying_message_info
                clarifying_message_context = MessageContext(
                    message_info=clarifying_message_info,
                    context=self.workflow_state.context,
                    previous_response=response
                )

                print(f"clarifying message context: {clarifying_message_context}")

                clarifying_response = await workflow.execute_activity_method(
                    Activities.analyze_info,
                    clarifying_message_context,
                    start_to_close_timeout=timedelta(seconds=10),
                    retry_policy=retry_policy
                )

                self.workflow_state.current_message.response=clarifying_response["message"]
                self.workflow_state.disambiguate = clarifying_response["disambiguate"]
                print(f"clarifying response: {clarifying_response}")

                response = clarifying_response
                if self._exit:
                    break

        if response['intent'] == "suggestion":
            suggestion = await workflow.execute_activity_method(
                Activities.get_suggestion,
                args=[response,self.workflow_state.current_message.message],
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=retry_policy
            )

            self.workflow_state.system_output=suggestion
            print(f"suggestion: {suggestion}")

            request = Message(
                message=self.workflow_state.current_message.message,
                response=response["message"]
            )

            self.workflow_state.chat_history.append(request)

        elif response["intent"] == "explanation":
            explanation = await workflow.execute_activity_method(
                Activities.get_explanation,
                response,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=retry_policy
            )

            self.workflow_state.system_output=explanation
            print(f"explanation: {explanation}")

            request = Message(
                message=self.workflow_state.current_message.message,
                response=response["message"]
            )

            self.workflow_state.chat_history.append(request)

        else:
            response = "I dont understand what are you saying"
            message = Message(
                message=self.workflow_state.current_message.message,
                response=response
            )

            self.workflow_state.chat_history.append(message)
        
        print(f"FINAL workflow state: {self.workflow_state}")
        print("Closing...")
        return self.workflow_state
        