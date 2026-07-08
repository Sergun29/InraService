import asyncio

from app.intraservice_client import intraservice_client
from app.llm_client import ask_llm_for_clarification
from app.config import settings

TASK_ID = 125713


async def main():
    task = await intraservice_client.get_task_by_id(TASK_ID)
    if not task:
        print(f"Задача {TASK_ID} не найдена")
        return

    print("Задача получена:", task.get("Id"), task.get("Name"))

    description = task.get("Description") or task.get("Name") or ""
    question = await ask_llm_for_clarification(description)
    print("Вопрос от нейросети:", question)

    status, text = await intraservice_client.post_task_update(
        task=task,
        comment=question,
        creator_id=settings.INTRASERVICE_CREATOR_ID,
    )

    print("=" * 60)
    print("STATUS:", status)
    print("BODY (первые 2000 симв.):")
    print(text[:2000])
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())