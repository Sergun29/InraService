import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://intraservice_user:123!@10.47.4.173:5432/intraservice_db")
    rows = await conn.fetch("SELECT * FROM task_dialogs ORDER BY id DESC LIMIT 10;")
    for row in rows:
        print(dict(row))
    await conn.close()

asyncio.run(main())