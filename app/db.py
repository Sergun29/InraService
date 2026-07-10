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
                last_processed_comment TEXT,
                last_processed_comment_at TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
            """
        )

        await conn.execute(
            """
            ALTER TABLE task_dialogs
            ADD COLUMN IF NOT EXISTS last_processed_comment TEXT
            """
        )
        await conn.execute(
            """
            ALTER TABLE task_dialogs
            ADD COLUMN IF NOT EXISTS last_processed_comment_at TEXT
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


async def get_dialogs_for_ai(limit: int = 50) -> list[dict]:
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM task_dialogs
            WHERE status IN ('new', 'ready_for_ai', 'awaiting_user_response')
            ORDER BY updated_at ASC
            LIMIT $1
            """,
            limit,
        )
        return [dict(row) for row in rows]


async def create_dialog(task_id: int, original_text: str, history: list, status: str = "new") -> None:
    async with _pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO task_dialogs (
                task_id,
                original_text,
                dialog_history,
                iteration_count,
                status,
                last_processed_comment,
                last_processed_comment_at
            )
            VALUES ($1, $2, $3, 0, $4, NULL, NULL)
            """,
            task_id,
            original_text,
            json.dumps(history, ensure_ascii=False),
            status,
        )


async def update_dialog(
    task_id: int,
    history: list,
    iteration_count: int,
    status: str,
    last_processed_comment: str | None = None,
    last_processed_comment_at: str | None = None,
) -> None:
    async with _pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE task_dialogs
            SET dialog_history = $1,
                iteration_count = $2,
                status = $3,
                last_processed_comment = $4,
                last_processed_comment_at = $5,
                updated_at = NOW()
            WHERE task_id = $6
            """,
            json.dumps(history, ensure_ascii=False),
            iteration_count,
            status,
            last_processed_comment,
            last_processed_comment_at,
            task_id,
        )


async def update_status(task_id: int, status: str) -> None:
    async with _pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE task_dialogs
            SET status = $1, updated_at = NOW()
            WHERE task_id = $2
            """,
            status,
            task_id,
        )