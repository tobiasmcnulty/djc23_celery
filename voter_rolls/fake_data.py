from faker import Faker
from faker_education import SchoolProvider

from .models import PollingCenter, Voter, VoterRegistration
from .utils import dirichlet_random_choices, grouper

GROUP_SIZE = 2000
VOTERS_PER_CENTER = 1000


def fake_voters(n):
    """Generates n unsaved Voter objects."""
    fake = Faker()
    for _ in range(n):
        yield Voter(
            voter_id=fake.unique.random_int(min=10_000_000, max=99_999_999),
            voter_name=fake.name(),
        )


def fake_polling_centers(n):
    """Generates n unsaved PollingCenter objects."""
    fake = Faker()
    fake.add_provider(SchoolProvider)
    for _ in range(n):
        yield PollingCenter(
            center_id=fake.unique.random_int(min=10000, max=99999),
            center_name=fake.school_name(),
        )


def fake_voter_registrations(voters, center_pk_generator):
    """Generates unsaved VoterRegistrations for voters."""
    for voter in voters:
        yield VoterRegistration(voter=voter, center_id=next(center_pk_generator))


def create_fake_data(num_voters):
    """
    Creates fake polling centers, voters, and voter registrations using
    the given num_centers and num_voters.
    """
    PollingCenter.objects.all().delete()
    Voter.objects.all().delete()
    VoterRegistration.objects.all().delete()

    num_centers = int(num_voters / VOTERS_PER_CENTER)
    print(f"Creating {num_centers} fake centers")

    for group in grouper(fake_polling_centers(num_centers), GROUP_SIZE):
        PollingCenter.objects.bulk_create(group)

    center_pks = PollingCenter.objects.values_list("pk", flat=True)
    center_pk_generator = dirichlet_random_choices(center_pks)

    print(f"Creating {num_voters} fake voters and registrations")
    for i, group in enumerate(grouper(fake_voters(num_voters), GROUP_SIZE)):
        voters = Voter.objects.bulk_create(group)
        registrations = fake_voter_registrations(voters, center_pk_generator)
        VoterRegistration.objects.bulk_create(registrations)
        if i > 0 and i % 50 == 0:
            print(f"{i*GROUP_SIZE} voters created")
