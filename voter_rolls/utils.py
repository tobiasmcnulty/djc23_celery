import itertools

import numpy as np


def grouper(iterable, n):
    """
    Collects chunks of n items from iterable. Handy for grouping lists of
    objects into batches suitable for bulk_create().
    """
    # In case iterable is not an iterator (but is, e.g., a list), islice()
    # will return the first group indefinitely, so ensure iterable is an
    # iterator first.
    iterable = iter(iterable)
    while True:
        group = list(itertools.islice(iterable, n))
        if not group:
            break
        yield group


def dirichlet_random_choices(values):
    """
    Chooses endless random values according to a Dirichlet distribution, e.g., to
    provide some randomness in the number of voters assigned to a given center.

    sqlite> select c.center_id, count(*) as registration_count
            from voter_rolls_voterregistration r
            join voter_rolls_pollingcenter c on (r.center_id = c.id)
            group by c.center_id
            limit 10;
    10025|877
    10043|241
    10222|1326
    10268|1325
    10351|2
    10355|635
    10362|1093
    10482|33
    10511|250
    10529|1458
    """
    rng = np.random.default_rng()
    dist = rng.dirichlet(np.ones(len(values)))
    while True:
        yield rng.choice(values, p=dist)
