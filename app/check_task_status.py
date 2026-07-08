import os
import sys
import asyncio
import json
import httpx

BASE_URL = os.getenv("INTRASERVICE_BASE_URL", "https://ap1711.intraservice.ru/api").rstrip("/")
LOGIN = os.getenv("INTRASERVICE_LOGIN")
PASSWORD = os.getenv("INTRASERVICE_PASSWORD")
TASK_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 126072


async def main():
    if not LOGIN or not PASSWORD:
        raise SystemExit(
            "Нужно задать переменные окружения INTRASERVICE_LOGIN и INTRASERVICE_PASSWORD"
        )

    if not BASE_URL.endswith("/api"):
        api_base = f"{BASE_URL}/api"
    else:
        api_base = BASE_URL

    url = f"{api_base}/task/{TASK_ID}"

    async with httpx.AsyncClient(
        auth=(LOGIN, PASSWORD),
        timeout=20.0,
        follow_redirects=True,
        headers={"Accept": "application/json"},
    ) as client:
        resp = await client.get(url)
        print("REQUEST URL:", resp.request.url)
        resp.raise_for_status()
        data = resp.json()

    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())