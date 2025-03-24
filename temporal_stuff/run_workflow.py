import asyncio 
import sys 
from temporal_stuff.shared import ASSISTANT_QUEUE, Query 
from temporal_stuff.temporal_client import get_temporal_client 
from temporal_stuff.workflows import AssistantWorflow 


async def main() -> None:
    
    client = await get_temporal_client()

    arg = sys.argv[1]

    data: Query = Query(query=arg,response="")

    result = await client.execute_workflow(
        AssistantWorflow.run,
        data,
        id="assistant-workflow-"+arg.replace(" ","_"),
        task_queue=ASSISTANT_QUEUE
    )


if __name__ == "__main__":
    asyncio.run(main())