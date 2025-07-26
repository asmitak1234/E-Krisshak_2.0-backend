# users/management/commands/load_data.py

from django.core.management.base import BaseCommand
from users.models import State, District
from users.constants.state_district_data import states_and_districts
from django.db import transaction

class Command(BaseCommand):
    help = 'Load states and districts into the database'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview insertions without saving')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        added_states = 0
        added_districts = 0

        with transaction.atomic():
            for state_name, district_list in states_and_districts.items():
                state_obj, created = State.objects.get_or_create(name=state_name.strip())
                if created:
                    added_states += 1

                # Existing districts for this state
                existing_districts = set(
                    d.lower().strip()
                    for d in District.objects.filter(state=state_obj).values_list("name", flat=True)
                )

                new_district_objs = [
                    District(name=district_name.strip(), state=state_obj)
                    for district_name in district_list
                    if district_name.lower().strip() not in existing_districts
                ]

                if new_district_objs:
                    if dry_run:
                        self.stdout.write(f"Would insert {len(new_district_objs)} districts for {state_name}")
                    else:
                        District.objects.bulk_create(new_district_objs)
                        added_districts += len(new_district_objs)

        if added_states == 0 and added_districts == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Nothing new to insert. All {State.objects.count()} states and {District.objects.count()} districts already exist 🎉"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Loaded states and districts FAST: {added_states} states, {added_districts} new districts"
                )
            )