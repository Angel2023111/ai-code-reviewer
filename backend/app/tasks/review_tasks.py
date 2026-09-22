from app.celery_app import celery_app


@celery_app.task
def health_check_task() -> str:
    return "worker is working"