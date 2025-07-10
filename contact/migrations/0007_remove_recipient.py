from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0006_notice'),  # replace with correct filename
    ]

    operations = [
        migrations.RunSQL("ALTER TABLE contact_notice DROP COLUMN recipient_id;")
    ]
