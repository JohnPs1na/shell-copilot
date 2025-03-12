import os
from temporalio.client import Client 

async def get_temporal_client() -> Client:
    arg = os.environ.get("TEMPORAL_CONNECTION")
    print(f"Argument: {arg}")

    if arg == "local":
        print("Connecting to local server")
        client: Client = await Client.connect("localhost:7233")
    else:
        # else wath?
        pass
    
    return client