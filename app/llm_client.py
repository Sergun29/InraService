import httpx

from app.config import settings


async def ask_llm_for_clarification(task_description: str) -> str:
    prompt = (
        "Ты помогаешь уточнять формулировки задач в service desk. "
        "Прочитай описание задачи и задай ОДИН короткий уточняющий вопрос постановщику, "
        "если формулировка неполная или неясная. Если всё понятно — предложи улучшенную формулировку.\n\n"
        f"Описание задачи:\n{task_description}"
    )
    return await _call_llm([{"role": "user", "content": prompt}])


async def ask_llm_continue(history: list[dict]) -> str:
    return await _call_llm(history)


async def _call_llm(messages: list[dict]) -> str:
    url = f"{settings.LLM_API_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.LLM_MODEL,
        "messages": messages,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    return data["choices"][0]["message"]["content"]