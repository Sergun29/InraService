
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException

from app.db import init_db, close_db
from app.poller import poll_intraservice_forever
from app.intraservice_client import intraservice_client
from app.dialog_service import process_task_dialog


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    task = asyncio.create_task(poll_intraservice_forever())
    yield
    task.cancel()
    await close_db()


app = FastAPI(title="IntraService Task Corrector", lifespan=lifespan)


@app.get("/")
async def root():
    return {"status": "ok"}


@app.get("/debug/task/{task_id}")
async def debug_task(task_id: int):
    task = await intraservice_client.get_task_by_id(task_id)
    if task is None:
        return {"error": "task not found or empty response"}
    return task


@app.get("/debug/tasks")
async def debug_tasks(page: int = 1, page_size: int = 50):
    tasks = await intraservice_client.get_tasks(page=page, page_size=page_size)
    return {"count": len(tasks), "tasks": tasks}


@app.post("/webhook/new-task")
async def new_task_webhook(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    task_id = body.get("Id")
    if not task_id:
        raise HTTPException(status_code=422, detail="Missing task Id")

    await process_task_dialog(task_id, body)
    return {"status": "ok", "task_id": task_id}
