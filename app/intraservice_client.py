import httpx
from base64 import b64encode

from app.config import settings


class IntraServiceClient:
    def __init__(self, base_url: str, username: str, password: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/") + "/api"
        self.timeout = timeout

        auth_str = f"{username}:{password}"
        auth_b64 = b64encode(auth_str.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {auth_b64}",
            "Accept": "application/json",
        }

    async def get_tasks(
        self,
        changed_more_than: str | None = None,
        executor_ids: str | None = None,
        service_name: str | None = "",
        executor_group: str | None = "",
        page: int = 1,
        page_size: int = 100,
    ) -> list[dict]:
        url = f"{self.base_url}/task"

        params = {
            "fields": (
                "Id,Name,Description,Changed,Created,Closed,"
                "CreatorId,Creator,StatusId,ServiceId,"
                "ExecutorIds,Executors,ExecutorGroupId,ExecutorGroup,"
                "CategoryIds,ObserverIds,CoordinatorIds,TypeId,PriorityId"
            ),
            "page": page,
            "pagesize": page_size,
            "StatusIds": "27,31,35",
        }

        if executor_group is not None:
            params["ExecutorGroup"] = executor_group
        if service_name is not None:
            params["ServiceName"] = service_name
        if executor_ids:
            params["ExecutorIds"] = executor_ids
        if changed_more_than:
            params["ChangedMoreThan"] = changed_more_than

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=self.headers, params=params)
            print("[intraservice_client] GET TASKS URL:", str(resp.request.url))
            resp.raise_for_status()
            data = resp.json()

        print("[intraservice_client] RAW TASKS RESPONSE:", data)

        if isinstance(data, dict) and isinstance(data.get("Tasks"), list):
            return data["Tasks"]
        return []

    async def get_task_by_id(self, task_id: int) -> dict | None:
        url = f"{self.base_url}/task/{task_id}"

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=self.headers)
            print("[intraservice_client] GET TASK URL:", str(resp.request.url))
            if resp.status_code != 200:
                print("[intraservice_client] GET TASK FAILED:", resp.status_code, resp.text[:500])
                return None
            data = resp.json() or {}

        return data.get("Task")

    async def get_task_lifetime(
        self,
        task_id: int,
        last_comments_on_top: bool = True,
        page: int = 1,
        page_size: int = 100,
    ) -> list[dict]:
        url = f"{self.base_url}/tasklifetime"
        params = {
            "taskid": task_id,
            "lastcommentsontop": str(last_comments_on_top).lower(),
            "page": page,
            "pagesize": page_size,
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=self.headers, params=params)
            print("[intraservice_client] LIFETIME URL:", str(resp.request.url))
            if resp.status_code != 200:
                print("[intraservice_client] LIFETIME FAILED:", resp.status_code, resp.text[:500])
                return []
            data = resp.json()

        if isinstance(data, dict) and isinstance(data.get("TaskLifetimes"), list):
            return data["TaskLifetimes"]
        return []

    async def post_task_update(
        self,
        task: dict,
        comment: str | None = None,
        status_id: int | None = None,
        creator_id: int | None = None,
        is_private_comment: bool = False,
    ) -> tuple[int, str]:
        task_id = int(task.get("Id"))
        url = f"{self.base_url}/task/{task_id}"

        payload = {
            "Id": task_id,
            "Name": task.get("Name") or "",
            "ServiceId": task.get("ServiceId"),
            "StatusId": int(status_id) if status_id is not None else task.get("StatusId"),
            "PriorityId": task.get("PriorityId"),
            "TypeId": task.get("TypeId"),
            "CreatorId": creator_id or settings.INTRASERVICE_CREATOR_ID,
            "IsPrivateComment": is_private_comment,
        }

        for k in ["ExecutorIds", "ObserverIds", "CoordinatorIds", "ServiceStageId"]:
            v = task.get(k)
            if v is not None and v != "":
                payload[k] = v

        if comment:
            payload["Comment"] = comment

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            resp = await client.post(url, headers=self.headers, json=payload)
            print("[intraservice_client] POST TASK URL:", str(resp.request.url))
            print("[intraservice_client] POST TASK PAYLOAD:", payload)
            print("[intraservice_client] POST TASK STATUS:", resp.status_code)
            print("[intraservice_client] POST TASK BODY:", resp.text[:2000])

        return resp.status_code, resp.text


if not settings.INTRASERVICE_BASE_URL:
    raise ValueError("INTRASERVICE_BASE_URL is not set")
if not settings.INTRASERVICE_LOGIN:
    raise ValueError("INTRASERVICE_LOGIN is not set")
if not settings.INTRASERVICE_PASSWORD:
    raise ValueError("INTRASERVICE_PASSWORD is not set")


intraservice_client = IntraServiceClient(
    base_url=settings.INTRASERVICE_BASE_URL,
    username=settings.INTRASERVICE_LOGIN,
    password=settings.INTRASERVICE_PASSWORD,
)