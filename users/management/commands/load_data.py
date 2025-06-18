# users/management/commands/load_data.py

from django.core.management.base import BaseCommand
from users.models import State, District
from users.constants.state_district_data import states_and_districts

class Command(BaseCommand):
    help = 'Load states and districts into the database'

    def handle(self, *args, **kwargs):
        for state_name, district_list in states_and_districts.items():
            state_obj, _ = State.objects.get_or_create(name=state_name)
            for district_name in district_list:
                District.objects.get_or_create(name=district_name, state=state_obj)
        self.stdout.write(self.style.SUCCESS('✅ Successfully loaded states and districts'))

