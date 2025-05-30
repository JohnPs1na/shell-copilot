import asyncio

from temporalio.worker import Worker 
from temporal_stuff.activities import Activities
from temporal_stuff.shared import ASSISTANT_QUEUE
from temporal_stuff.temporal_client import get_temporal_client
from temporal_stuff.workflows import AssistantWorkflow


async def main() -> None:
    client = await get_temporal_client()

    activities = Activities()
    worker: Worker = Worker(
        client,
        task_queue=ASSISTANT_QUEUE,
        workflows=[AssistantWorkflow],
        activities=[
            activities.detect_intent,
            activities.analyze_info,
            activities.get_suggestion,
            activities.get_explanation,
            activities.publish_message,
            activities.save_chat
        ]
    )

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
