import asyncio

from app.intraservice_client import intraservice_client
from app.task_ingestion import ingest_task
from app.config import settings


PAGE_SIZE = 50


async def poll_intraservice_once() -> None:
    page = 1

    while True:
        tasks = await intraservice_client.get_tasks(
            changed_more_than=None,
            executor_ids=settings.INTRASERVICE_EXECUTOR_IDS,
            service_name="",
            executor_group="",
            page=page,
            page_size=PAGE_SIZE,
        )

        if not tasks:
            print(f"[poller] page={page}: no tasks")
            break

        print(f"[poller] page={page}: received {len(tasks)} tasks")

        for task in tasks:
            if task.get("Closed"):
                continue

            try:
                await ingest_task(task)
            except Exception as e:
                print(f"[poller] error processing task {task.get('Id')}: {e}")

        if len(tasks) < PAGE_SIZE:
            break

        page += 1


async def poll_intraservice_forever() -> None:
    if settings.POLLER_INTERVAL_SECONDS == 0:
        print("[poller] POLLER_INTERVAL_SECONDS=0, running once and stopping")
        try:
            await poll_intraservice_once()
        except Exception as e:
            print(f"[poller] error: {e}")
        print("[poller] single run finished")
        return

    print("[poller] start (recurring mode)")
    while True:
        try:
            await poll_intraservice_once()
        except Exception as e:
            print(f"[poller] error: {e}")

        await asyncio.sleep(settings.POLLER_INTERVAL_SECONDS)