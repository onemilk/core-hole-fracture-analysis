"""Celery worker for async analysis tasks."""
from celery import Celery
import os

REDIS_URI = os.getenv("REDIS_URI", "redis://localhost:6379/0")
celery = Celery("engine", broker=REDIS_URI, backend=REDIS_URI)
