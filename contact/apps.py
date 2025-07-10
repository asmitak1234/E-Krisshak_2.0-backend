from django.apps import AppConfig
from django.db import connection

class ContactConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'contact'

    def ready(self):
        try:
            with connection.cursor() as cursor:
                cursor.execute("ALTER TABLE contact_notice MODIFY COLUMN recipient_id BIGINT NULL;")
        except Exception as e:
            print("⚠️ Could not patch recipient_id:", e)
