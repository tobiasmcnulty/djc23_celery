from celery import group, shared_task

from .models import PollingCenter, StationAssignment
from .rollgen import split_voters_into_stations, write_station_list


def get_center_ids():
    "All center_ids in the database."
    return PollingCenter.objects.values_list("center_id", flat=True)


def get_center_station_id_pairs():
    "All (center_id, station_id) pairs in the database."
    return list(
        StationAssignment.objects.values_list("center__center_id", "station_id")
        .order_by("center__center_id", "station_id")
        .distinct()
    )


def refresh_station_assignment():
    "Deletes and recreates station assignments for registered voters."
    # Pattern: Keep database-intensive work sequential
    # (without a separate task for each center)
    StationAssignment.objects.all().delete()
    for center in PollingCenter.objects.all():
        split_voters_into_stations(center, delete=False)


# Option 1: All work done in a single task: Short, but brittle and not scalable
@shared_task
def task_all_in_one():
    total_pages = 0
    for center in PollingCenter.objects.all():
        print(f"Writing center list for {center.center_name} ({center.center_id})")
        split_voters_into_stations(center)
        for station_id in center.station_ids:
            total_pages += write_station_list(center, station_id)
    print(f"Total pages written: {total_pages}")


# Option 2: A second task to orchestrate and collect the results
@shared_task
def task_parallelize_tasks_by_center_with_join():
    result = group(
        task_generate_lists_for_one_center.s(center_id)
        for center_id in get_center_ids()
    ).delay()
    # Don't do this! It will die an exception:
    # "RuntimeError: Never call result.get() within a task!"
    counts = result.join()
    print(f"group_task: Total pages written: {sum(counts)}")


# Option 2: A task to generate lists for a single center
@shared_task
def task_generate_lists_for_one_center(center_id):
    center = PollingCenter.objects.get(center_id=center_id)
    split_voters_into_stations(center)
    print(f"Writing center list for {center.center_name} ({center.center_id})")
    total_pages = 0
    for station_id in center.station_ids:
        total_pages += write_station_list(center, station_id)
    return total_pages


# Option 3: Instead of waiting for results, queue a chord task
# upon completion of all tags in the group to sum pages written
@shared_task
def task_queue_tasks_by_center_with_chord():
    (
        # chord() does the same thing, but I find the pipe (|) syntax more explicit
        group(
            task_generate_lists_for_one_center.s(center_id)
            for center_id in get_center_ids()
        )
        # This task gets queued only once all results are in, and this task does
        # not need to wait around for the results.
        | task_sum_pages.s()
    ).delay()


# Option 3: Sum and print results
@shared_task
def task_sum_pages(page_counts):
    print(f"sum_pages: Total pages written: {sum(page_counts)}")


# Option 4: (don't do this)
#   - Instead of splitting voters into stations one by one, we could
#     parallelize that work up front.
#   - This turns out to be a bad idea, because work is fast anyways
#     (it might be slower with all of Celery's messaging overhead), and
#     we don't want to pummel our database with too many queries at once.
@shared_task
def task_assign_all_stations_in_parallel():
    StationAssignment.objects.all().delete()
    group(
        task_assign_stations_for_one_center.s(center_id)
        for center_id in get_center_ids()
    ).delay()


@shared_task
def task_assign_stations_for_one_center(center_id):
    center = PollingCenter.objects.get(center_id=center_id)
    split_voters_into_stations(center)


# Option 5: Create each station's list in its own task
@shared_task
def task_generate_lists_for_one_station(center_id, station_id):
    center = PollingCenter.objects.get(center_id=center_id)
    voter_count = center.stationassignment_set.filter(station_id=station_id).count()
    print(
        f"Writing center list for {center.center_name} ({center_id}), "
        f"station {station_id} with {voter_count} voters"
    )
    return write_station_list(center, station_id)


# Option 5A: Use starmap() to run the tasks for each station.
@shared_task
def task_assign_stations_and_generate_lists_with_starmap():
    refresh_station_assignment()

    # What is the point? starmap() starts a single tasks and executes
    # each task sequentially.
    (
        task_generate_lists_for_one_station.starmap(get_center_station_id_pairs())
        | task_sum_pages.s()
    ).delay()


# Option 5B:
#    - Like Option 5A, but use a group() again instead of starmap()
#    - This option gets the database work out of the way quickly,
#      and then parallelizes the CPU-intensive work at an appropriate and
#      consistent granularity (roughly 7 seconds per task).
@shared_task
def task_assign_stations_and_generate_lists_with_chord():
    refresh_station_assignment()

    # Pattern: Parallelize CPU-intensive work
    (
        group(
            task_generate_lists_for_one_station.s(center_id, station_id)
            for center_id, station_id in get_center_station_id_pairs()
        )
        | task_sum_pages.s()
    ).delay()


# Bonus: Error handling
@shared_task
def raising_task():
    raise Exception("Task failed.")


@shared_task
def on_chord_error(request, exc, traceback):
    print("Task {0!r} raised error: {1!r}".format(request.id, exc))


@shared_task
def task_group_with_error_in_sub_task():
    sub_tasks = [
        task_generate_lists_for_one_station.s(center_id, station_id)
        for center_id, station_id in get_center_station_id_pairs()
    ] + [raising_task.s()]
    (group(sub_tasks) | task_sum_pages.s().on_error(on_chord_error.s())).delay()
