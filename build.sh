#!/usr/bin/env bash
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py makemigrations --noinput
python manage.py migrate --noinput

python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='asmita2275@gmail.com').exists():
    User.objects.create_superuser(
        email='asmita2275@gmail.com',
        password='Asmita#132',
        name='Asmita'
    )
END

