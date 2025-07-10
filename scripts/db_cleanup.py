from django.db import connection

with connection.cursor() as cursor:
    try:
        cursor.execute("ALTER TABLE contact_notice DROP COLUMN recipient_id;")
        print("✅ recipient_id dropped successfully")
    except Exception as e:
        print("⚠️ Skip recipient_id drop:", e)
