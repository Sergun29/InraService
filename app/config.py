import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    INTRASERVICE_BASE_URL = (
        os.getenv("INTRASERVICE_BASE_URL", "http://ap1711.intraservice.ru")
        .replace("https://", "http://")
        .rstrip("/")
    )
    INTRASERVICE_LOGIN = os.getenv("INTRASERVICE_LOGIN")
    INTRASERVICE_PASSWORD = os.getenv("INTRASERVICE_PASSWORD")

    INTRASERVICE_EXECUTOR_IDS = os.getenv("INTRASERVICE_EXECUTOR_IDS", "927,945,1638,1664")
    INTRASERVICE_CREATOR_ID = int(os.getenv("INTRASERVICE_CREATOR_ID", "1664"))

    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://intraservice_user:123!@10.47.4.173:5432/intraservice_db")

    POLLER_INTERVAL_SECONDS = int(os.getenv("POLLER_INTERVAL_SECONDS", 15))


settings = Settings()