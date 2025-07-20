# users/management/commands/load_data.py

from django.core.management.base import BaseCommand
from users.models import State, District
from users.constants.state_district_data import states_and_districts
from django.db import transaction

class Command(BaseCommand):
    help = 'Load states and districts into the database'

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            for state_name, district_list in states_and_districts.items():
                state_obj, _ = State.objects.get_or_create(name=state_name)
                existing = District.objects.filter(state=state_obj).values_list("name", flat=True)
                new_districts = [
                    District(name=district_name, state=state_obj)
                    for district_name in district_list
                    if district_name not in existing
                ]
                District.objects.bulk_create(new_districts)
        self.stdout.write(self.style.SUCCESS('✅ Loaded states and districts FAST'))