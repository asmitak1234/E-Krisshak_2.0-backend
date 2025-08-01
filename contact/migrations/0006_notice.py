# Generated by Django 5.0.7 on 2025-06-18 06:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0005_alter_contactmessage_options_and_more'),
        ('users', '0004_favorite'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author_type', models.CharField(choices=[('state_admin', 'State Admin'), ('district_admin', 'District Admin')], max_length=20)),
                ('author_name', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('district', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='district_notices', to='users.districtadminprofile')),
                ('state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='state_notices', to='users.stateadminprofile')),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ]
