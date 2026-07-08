import asyncio

from app.intraservice_client import intraservice_client
from app.llm_client import ask_llm_for_clarification

TASK_ID = 125713


async def main():
    task = await intraservice_client.get_task_by_id(TASK_ID)

    if not task:
        print(f"Задача {TASK_ID} не найдена")
        return

    print("=" * 60)
    print("ЗАДАЧА:")
    print("Id:", task.get("Id"))
    print("Name:", task.get("Name"))
    print("Description:", task.get("Description"))
    print("=" * 60)

    description = task.get("Description") or task.get("Name") or ""
    question = await ask_llm_for_clarification(description)

    print("ОТВЕТ НЕЙРОСЕТИ:")
    print(question)
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())