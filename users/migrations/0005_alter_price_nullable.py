from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_favorite'),  # replace with your actual last migration
    ]

    operations = [
        migrations.AlterField(
            model_name='krisshakprofile',
            name='price',
            field=models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2),
        ),
    ]
