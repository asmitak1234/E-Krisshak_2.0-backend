import django
import os
from django.db import connection

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ekrisshak2.settings")
django.setup()  # This boots Django properly

with connection.cursor() as cursor:
    try:
        cursor.execute("ALTER TABLE contact_notice DROP COLUMN recipient_id;")
        print("✅ recipient_id dropped successfully")
    except Exception as e:
        print(f"⚠️ Failed to drop recipient_id: {e}")
