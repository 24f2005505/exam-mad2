from celery import Celery
from celery.schedules import crontab

## redis is the broker (queue of jobs) for celery
celery = Celery("examination_portal", broker="redis://localhost:6379/1", include=["tasks"])
celery.conf.timezone = "Asia/Kolkata"
celery.conf.broker_connection_timeout = 2
celery.conf.task_publish_retry = False  ## fail fast if redis is not running

## scheduled jobs (run by: celery -A make_celery beat)
celery.conf.beat_schedule = {
    "daily-examination-reminder": {
        "task": "tasks.daily_reminder",
        "schedule": crontab(hour=8, minute=0),  ## every day at 8:00 AM
    },
    "monthly-examination-report": {
        "task": "tasks.monthly_report",
        "schedule": crontab(hour=9, minute=0, day_of_month=1),  ## first day of every month at 9:00 AM
    },
}
