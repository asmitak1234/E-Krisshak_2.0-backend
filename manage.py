#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

if "runserver" in sys.argv or "migrate" in sys.argv or "collectstatic" in sys.argv:
    try:
        from django.contrib.sites.models import Site
        Site.objects.update_or_create(
            id=1,
            defaults={
                "domain": "web-production-f62a7.up.railway.app",
                "name": "Production"
            }
        )
    except Exception as e:
        print(f"⚠️ Failed to update Site object: {e}")


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ekrisshak2.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
