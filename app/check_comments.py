import asyncio

import httpx

from app.config import settings


TASK_ID = 122795  # нужный Id заявки


async def main():
    base_url = settings.INTRASERVICE_BASE_URL.rstrip("/") + "/api"
    url = f"{base_url}/tasklifetime"

    params = {
        "taskid": TASK_ID,
        "lastcommentsontop": "true",
        "pagesize": 100,
        "page": 1,
        # при необходимости можно добавить include, но для комментариев не обязательно
        # "include": "status,priority,service",
    }

    async with httpx.AsyncClient(
        timeout=30,
        follow_redirects=True,
        auth=(settings.INTRASERVICE_LOGIN, settings.INTRASERVICE_PASSWORD),
    ) as client:
        resp = await client.get(url, params=params)
        print("[check_comments] LIFETIME URL:", str(resp.request.url))
        resp.raise_for_status()
        data = resp.json()

    # В твоём ответе структура такая:
    # {
    #   "TaskLifetimes": [...],
    #   "Priorities": [],
    #   "Services": [],
    #   "Statuses": [],
    #   "Paginator": {...}
    # }
    if not isinstance(data, dict) or not isinstance(data.get("TaskLifetimes"), list):
        print("=== Ошибка: нет массива TaskLifetimes в ответе ===")
        print(data)
        return

    lifetimes = data["TaskLifetimes"]
    print(f"=== Жизненный цикл задачи {TASK_ID} ===")
    print(f"Всего записей: {len(lifetimes)}")

    has_comments = False

    for i, item in enumerate(lifetimes, start=1):
        comments = (item.get("Comments") or "").strip()
        date = item.get("Date")
        editor = item.get("Editor")
        status_id = item.get("StatusId")

        print("-" * 60)
        print(f"Запись #{i}")
        if date:
            print("Date:     ", date)
        if editor:
            print("Editor:   ", editor)
        if status_id is not None:
            print("StatusId: ", status_id)
        print("Comments: ", comments if comments else "<ПУСТО>")

        if comments:
            has_comments = True

    print("=" * 60)
    print("has_comments:", has_comments)


if __name__ == "__main__":
    asyncio.run(main())