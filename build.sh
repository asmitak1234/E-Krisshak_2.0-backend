#!/usr/bin/env bash
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate --noinput

echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='asmita').exists() or User.objects.create_superuser('asmita', 'asmita2275@gmail.com', 'Asmita#132')" | python manage.py shell

