import asyncio
import json

from app.config import settings
from app.db import get_dialogs_for_ai, update_dialog, update_status
from app.intraservice_client import intraservice_client
from app.llm_client import analyze_task_with_llm


def _extract_latest_comment(lifetimes: list[dict]) -> dict | None:
    for item in lifetimes:
        comment = (item.get("Comments") or "").strip()
        if comment:
            return item
    return None


def _is_ai_comment(item: dict) -> bool:
    editor = str(item.get("Editor") or "").strip().lower()
    editor_name = str(item.get("EditorName") or "").strip().lower()
    ai_id = str(settings.INTRASERVICE_CREATOR_ID)

    return ai_id in editor or ai_id in editor_name


async def process_one_dialog(record: dict) -> None:
    task_id = record["task_id"]
    status = record["status"]
    iteration_count = record["iteration_count"]
    task = await intraservice_client.get_task_by_id(task_id)

    if not task:
        print(f"[processor] task {task_id}: task not found in IntraService")
        return

    history = record["dialog_history"] or []
    if isinstance(history, str):
        history = json.loads(history)

    lifetimes = await intraservice_client.get_task_lifetime(task_id)
    latest_comment_item = _extract_latest_comment(lifetimes)
    latest_comment = (latest_comment_item.get("Comments") or "").strip() if latest_comment_item else ""
    latest_comment_at = latest_comment_item.get("Date") if latest_comment_item else None

    if status == "awaiting_user_response":
        if not latest_comment_item:
            print(f"[processor] task {task_id}: still waiting user response, no comments")
            return

        if _is_ai_comment(latest_comment_item):
            print(f"[processor] task {task_id}: last comment is from AI, waiting user")
            return

        if (
            record.get("last_processed_comment") == latest_comment
            and record.get("last_processed_comment_at") == latest_comment_at
        ):
            print(f"[processor] task {task_id}: user comment already processed")
            return

        history.append({"role": "user", "content": latest_comment})
        await update_status(task_id, "ready_for_ai")
        status = "ready_for_ai"

    if status in ("new", "ready_for_ai"):
        task_text = record.get("original_text") or task.get("Description") or task.get("Name") or ""
        result = await analyze_task_with_llm(task_text, history)
        ai_message = result["message"]

        history.append({"role": "assistant", "content": ai_message})
        new_count = iteration_count + 1

        if result["is_complete"] or new_count >= settings.MAX_ITERATIONS:
            new_status = "completed"
            print(f"[processor] task {task_id}: completed")
        else:
            post_status, post_text = await intraservice_client.post_task_update(
                task=task,
                comment=ai_message,
                creator_id=settings.INTRASERVICE_CREATOR_ID,
                is_private_comment=False,
            )

            if post_status >= 400:
                raise RuntimeError(
                    f"Failed to post AI comment to task {task_id}: {post_status} {post_text[:300]}"
                )

            new_status = "awaiting_user_response"
            print(f"[processor] task {task_id}: AI question posted")

        await update_dialog(
            task_id=task_id,
            history=history,
            iteration_count=new_count,
            status=new_status,
            last_processed_comment=latest_comment if latest_comment else record.get("last_processed_comment"),
            last_processed_comment_at=latest_comment_at if latest_comment_at else record.get("last_processed_comment_at"),
        )


async def process_dialogs_once() -> None:
    records = await get_dialogs_for_ai(limit=50)

    if not records:
        print("[processor] no dialogs to process")
        return

    print(f"[processor] found {len(records)} dialogs to process")

    for record in records:
        try:
            await process_one_dialog(record)
        except Exception as e:
            task_id = record.get("task_id")
            print(f"[processor] error processing task {task_id}: {e}")
            await update_status(task_id, "error")


async def process_dialogs_forever() -> None:
    print("[processor] start")
    while True:
        try:
            await process_dialogs_once()
        except Exception as e:
            print(f"[processor] loop error: {e}")

        await asyncio.sleep(settings.PROCESSOR_INTERVAL_SECONDS)