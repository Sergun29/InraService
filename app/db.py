import json
import asyncpg

from app.config import settings


_pool: asyncpg.Pool | None = None


async def init_db() -> None:
    global _pool
    _pool = await asyncpg.create_pool(
        dsn=settings.DATABASE_URL,
        min_size=1,
        max_size=5,
        ssl=False,
    )

    async with _pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS task_dialogs (
                id SERIAL PRIMARY KEY,
                task_id BIGINT UNIQUE NOT NULL,
                original_text TEXT,
                dialog_history JSONB,
                iteration_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
            """
        )

    print("[db] PostgreSQL pool initialized, table task_dialogs ready")


async def close_db() -> None:
    global _pool
    if _pool:
        await _pool.close()


async def get_dialog(task_id: int) -> dict | None:
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM task_dialogs WHERE task_id = $1",
            task_id,
        )
        return dict(row) if row else None


async def create_dialog(task_id: int, original_text: str, history: list, status: str = "new") -> None:
    async with _pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO task_dialogs (task_id, original_text, dialog_history, iteration_count, status)
            VALUES ($1, $2, $3, 0, $4)
            """,
            task_id,
            original_text,
            json.dumps(history, ensure_ascii=False),
            status,
        )


async def update_dialog(task_id: int, history: list, iteration_count: int, status: str) -> None:
    async with _pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE task_dialogs
            SET dialog_history = $1, iteration_count = $2, status = $3, updated_at = NOW()
            WHERE task_id = $4
            """,
            json.dumps(history, ensure_ascii=False),
            iteration_count,
            status,
            task_id,
        )