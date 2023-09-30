from django.core.management.base import BaseCommand

from ...fake_data import create_fake_data


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def add_arguments(self, parser):
        parser.add_argument("num_voters", type=int)

    def handle(self, *args, **options):
        create_fake_data(num_voters=options["num_voters"])
