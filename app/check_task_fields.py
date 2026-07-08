import asyncio
import json

from app.intraservice_client import intraservice_client


TASK_ID = 122795  # можно менять перед запуском


TEXT_KEYS_HINT = (
    "Description",
    "CreatorComments",
    "Comment",
    "LastComment",
    "Data",
)


async def main():
    task = await intraservice_client.get_task_by_id(TASK_ID)
    if not task:
        print(f"Задача {TASK_ID} не найдена")
        return

    print(f"=== Поля заявки {TASK_ID} ===")
    for key, value in task.items():
        if isinstance(value, str):
            trimmed = value.strip()
            if trimmed:
                print(f"{key}: {trimmed[:500]}")
        else:
            # отдельный блок для полей, которые могут содержать структуру
            if key in TEXT_KEYS_HINT:
                print(f"{key}: {json.dumps(value, ensure_ascii=False)[:500]}")

    print("=== ВСЕ ПОЛЯ RAW ===")
    print(json.dumps(task, ensure_ascii=False, indent=2)[:4000])


if __name__ == "__main__":
    asyncio.run(main())