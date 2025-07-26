from django.apps import AppConfig
from django.core.management import call_command
from django.db.utils import OperationalError
from .models import State

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        try:
            if not State.objects.exists():
                call_command("load_data")
                print("✅ State & District data loaded on startup")
        except OperationalError:
            print("⛔ DB not ready on first boot — skipping load")
