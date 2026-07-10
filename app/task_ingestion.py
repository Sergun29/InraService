from app.db import get_dialog, create_dialog
from app.intraservice_client import intraservice_client


async def has_comments(task_id: int) -> bool:
    lifetimes = await intraservice_client.get_task_lifetime(task_id)

    for item in lifetimes:
        comments = (item.get("Comments") or "").strip()
        if comments:
            return True

    return False


async def ingest_task(task: dict) -> None:
    task_id = task.get("Id")
    if not task_id:
        print("[ingestion] skip: task without Id")
        return

    existing = await get_dialog(task_id)
    if existing:
        print(f"[ingestion] task {task_id}: already exists in DB")
        return

    if await has_comments(task_id):
        print(f"[ingestion] task {task_id}: skip, already has comments in lifetime")
        return

    description = task.get("Description") or task.get("Name") or ""
    await create_dialog(task_id, description, history=[], status="ready_for_ai")
    print(f"[ingestion] task {task_id}: saved to DB, status=ready_for_ai")