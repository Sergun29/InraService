from fastapi import APIRouter
from app.intraservice_client import intraservice_client
from app.config import settings

router = APIRouter()


@router.post("/debug/send-comment/{task_id}")
async def debug_send_comment(task_id: int, comment: str = "Тестовый комментарий от нейросети"):
    task = await intraservice_client.get_task_by_id(task_id)
    if not task:
        return {"error": "task not found"}

    status, text = await intraservice_client.post_task_update(
        task=task,
        comment=comment,
        creator_id=settings.INTRASERVICE_CREATOR_ID,
    )
    return {"status_code": status, "response_body": text[:1000], "task_snapshot": task}


@router.get("/debug/task-comments/{task_id}")
async def debug_task_comments(task_id: int):
    expenses = await intraservice_client.get_task_expenses_with_comments(task_id)

    comments_only = [
        {
            "Id": e.get("Id"),
            "UserName": e.get("UserName"),
            "Date": e.get("Date"),
            "EditorName": e.get("EditorName"),
            "Comments": e.get("Comments"),
        }
        for e in expenses
    ]

    has_comments = any((c.get("Comments") or "").strip() for c in comments_only)

    return {
        "task_id": task_id,
        "raw_expenses_count": len(expenses),
        "comments": comments_only,
        "has_comments": has_comments,
    }