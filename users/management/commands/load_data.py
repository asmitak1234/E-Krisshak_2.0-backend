# users/management/commands/load_data.py

from django.core.management.base import BaseCommand
from users.models import State, District
from users.constants.state_district_data import states_and_districts
from django.db import transaction

class Command(BaseCommand):
    help = 'Load states and districts into the database'

    def handle(self, *args, **kwargs):
        added_states = 0
        added_districts = 0

        with transaction.atomic():
            for state_name, district_list in states_and_districts.items():
                state_obj, created = State.objects.get_or_create(name=state_name)
                if created:
                    added_states += 1

                # Existing districts for this state
                existing_districts = set(
                    District.objects.filter(state=state_obj).values_list("name", flat=True)
                )

                new_district_objs = [
                    District(name=district_name, state=state_obj)
                    for district_name in district_list
                    if district_name not in existing_districts
                ]

                if new_district_objs:
                    District.objects.bulk_create(new_district_objs)
                    added_districts += len(new_district_objs)

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Loaded states and districts FAST: {added_states} states, {added_districts} new districts"
            )
        )
