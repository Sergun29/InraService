import asyncio

from app.intraservice_client import intraservice_client
from app.dialog_service import process_task_dialog
from app.config import settings

DEBUG_TASK_ID = 125713


async def poll_single_task_once() -> None:
    task = await intraservice_client.get_task_by_id(DEBUG_TASK_ID)

    if not task:
        print(f"[poller1] task {DEBUG_TASK_ID} not found")
        return

    print(f"[poller1] processing only task {DEBUG_TASK_ID}")
    try:
        await process_task_dialog(DEBUG_TASK_ID, task)
    except Exception as e:
        print(f"[poller1] error processing task {DEBUG_TASK_ID}: {e}")


async def poll_single_task_forever() -> None:
    print(f"[poller1] start, watching only task {DEBUG_TASK_ID}")
    while True:
        try:
            await poll_single_task_once()
        except Exception as e:
            print(f"[poller1] error: {e}")
        await asyncio.sleep(settings.POLLER_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(poll_single_task_forever())