from celery import Celery

celery_app = Celery(
    "expense_forecast",
    broker="redis://redis:6379/0",  # or whatever broker you use
    backend="redis://redis:6379/0",  # optional: result backend
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer='json',
)

#tasks is the name of the folder in the same directory as this file
# celery_app.autodiscover_tasks(['tasks'])
import tasks.submit_forecast
