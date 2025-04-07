# tasks/worker.py
from celery import Celery
from core.logic import add_numbers

celery_app = Celery("worker", broker="redis://localhost:6379/0", backend="rpc://")


@celery_app.task
def run_task(x, y):
    return add_numbers(x, y)
