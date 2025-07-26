from django.apps import AppConfig
from django.core.management import call_command

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        try:
            call_command('load_data')
            print("✅ State & District data loaded on startup")
        except Exception as err:
            print("🚨 Failed to load startup data:", err)
