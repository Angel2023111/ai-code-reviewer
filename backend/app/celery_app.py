from celery import Celery

from app.config import REDIS_URL

celery_app = Celery(
    "ai_code_reviewer",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.tasks.review_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)