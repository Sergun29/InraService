import json
import httpx

from app.config import settings


SYSTEM_PROMPT = """
Ты — консультант по 1С, работаешь только с задачами по 1С.
Твоя цель — подготовить такие описания задач, чтобы программист 1С мог начать работу сразу, без дополнительных уточнений.
Ты обязан требовать от пользователя все важные данные: номера, даты, виды документов, суммы, контрагентов, период и примеры.
Отвечай строго в формате JSON по заданной схеме. Никакого текста вне JSON, никаких комментариев, никаких списков.
""".strip()


def _build_user_prompt(task_text: str, dialog_history: list[dict]) -> str:
    return f"""
Проанализируй задачу и историю переписки.

Текст исходной задачи:
{task_text}

История диалога:
{json.dumps(dialog_history, ensure_ascii=False)}

Верни строго JSON следующего вида:
{{
  "is_complete": true,
  "message": "строка"
}}

Правила:
- Если информации для программиста 1С уже достаточно, верни:
  - "is_complete": true
  - "message": краткая, но полная формулировка задачи для программиста 1С.
- Если информации недостаточно, верни:
  - "is_complete": false
  - "message": один конкретный уточняющий вопрос пользователю.
- Не добавляй никаких других полей.
- Не добавляй markdown.
- Не добавляй пояснений.
- Верни только валидный JSON.
""".strip()


async def analyze_task_with_llm(task_text: str, dialog_history: list[dict]) -> dict:
    content = await _call_llm(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(task_text, dialog_history)},
        ]
    )

    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("LLM response is not a JSON object")

    if "is_complete" not in data or "message" not in data:
        raise ValueError("LLM response missing required keys")

    return {
        "is_complete": bool(data["is_complete"]),
        "message": str(data["message"]).strip(),
    }


async def _call_llm(messages: list[dict]) -> str:
    if not settings.LLM_API_BASE_URL:
        raise ValueError("LLM_API_BASE_URL is not set")
    if not settings.LLM_API_KEY:
        raise ValueError("LLM_API_KEY is not set")

    url = f"{settings.LLM_API_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.LLM_MODEL,
        "messages": messages,
        "temperature": 0.2,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    return data["choices"][0]["message"]["content"]