import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "marketplace.settings")

app = Celery("marketplace")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'cleanup-expired-reservations': {
        'task': 'orders.tasks.cleanup_expired_reservations',
        'schedule': 300.0,  # Run every 5 minutes
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")