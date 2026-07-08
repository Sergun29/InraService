from app.db import get_dialog, create_dialog, update_dialog
from app.intraservice_client import intraservice_client
from app.llm_client import ask_llm_for_clarification, ask_llm_continue
from app.config import settings
import json


async def process_task_dialog(task_id: int, task_data: dict) -> None:
    record = await get_dialog(task_id)

    if not record:
        # Новая задача — проверяем, что она "чистая", без чужих комментариев
        comments = await intraservice_client.get_task_expenses_with_comments(task_id)
        has_comments = any((c.get("Comments") or "").strip() for c in comments)

        if has_comments:
            print(f"[dialog_service] task {task_id}: skip, already has comments")
            return

        description = task_data.get("Description") or task_data.get("Name") or ""
        question = await ask_llm_for_clarification(description)

        history = [{"role": "assistant", "content": question}]
        await create_dialog(task_id, description, history)

        await intraservice_client.post_task_update(
            task=task_data,
            comment=question,
            creator_id=settings.INTRASERVICE_CREATOR_ID,
            is_private_comment=False,
        )
        return

    history = record["dialog_history"]
    if isinstance(history, str):
        history = json.loads(history)

    last_comment = task_data.get("LastComment") or ""
    if last_comment:
        history.append({"role": "user", "content": last_comment})

    new_response = await ask_llm_continue(history)
    history.append({"role": "assistant", "content": new_response})

    new_count = record["iteration_count"] + 1
    status = "completed" if new_count >= settings.MAX_ITERATIONS else "awaiting_response"

    await update_dialog(task_id, history, new_count, status)

    await intraservice_client.post_task_update(
        task=task_data,
        comment=new_response,
        creator_id=settings.INTRASERVICE_CREATOR_ID,
        is_private_comment=False,
    )