import asyncio
import asyncpg

from app.config import settings


async def main():
    conn = await asyncpg.connect(settings.DATABASE_URL, ssl=False)

    try:
        deleted = await conn.execute("DELETE FROM task_dialogs;")
        await conn.execute("ALTER SEQUENCE task_dialogs_id_seq RESTART WITH 1;")
        print(f"[clean_db] done: {deleted}")
        print("[clean_db] sequence task_dialogs_id_seq restarted to 1")
    finally:
        await conn.close()
async def get_active_dialog(task_id: int) -> dict | None:
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM task_dialogs
            WHERE task_id = $1
              AND status NOT IN ('closed', 'completed')
            """,
            task_id,
        )
        return dict(row) if row else None

if __name__ == "__main__":
    asyncio.run(main())