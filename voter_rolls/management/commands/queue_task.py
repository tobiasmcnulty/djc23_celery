from django.core.management.base import BaseCommand

from ...tasks import (
    task_all_in_one,
    task_assign_all_stations_in_parallel,
    task_assign_stations_and_generate_lists_with_chord,
    task_assign_stations_and_generate_lists_with_starmap,
    task_parallelize_tasks_by_center_with_join,
    task_queue_tasks_by_center_with_chord,
)


class Command(BaseCommand):
    help = "Queues the specified task in tasks.py"

    TASK_MAP = {
        "all_in_one": task_all_in_one,
        "parallelize_tasks_by_center_with_join": (
            task_parallelize_tasks_by_center_with_join
        ),
        "queue_tasks_by_center_with_chord": task_queue_tasks_by_center_with_chord,
        "assign_all_stations_in_parallel": task_assign_all_stations_in_parallel,
        "assign_stations_and_generate_lists_with_starmap": (
            task_assign_stations_and_generate_lists_with_starmap
        ),
        "assign_stations_and_generate_lists_with_chord": (
            task_assign_stations_and_generate_lists_with_chord
        ),
    }

    def add_arguments(self, parser):
        parser.add_argument("task_name", choices=self.TASK_MAP.keys())

    def handle(self, *args, **options):
        self.TASK_MAP.get(options["task_name"]).delay()
