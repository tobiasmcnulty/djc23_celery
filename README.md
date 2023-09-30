# DjangoCon 2023 Celery Setup

This repo contains the code accompanying the talk [How to Schedule Tasks with Celery and Django](https://2023.djangocon.us/talks/how-to-schedule-tasks-with-celery-and-django/) from DjangoCon 2023. It's based on Django 4.2 and Celery 5.3.

## Prerequisites

- [Python 3.11](https://www.python.org/downloads/)
- [direnv](https://direnv.net/docs/installation.html)
- A local checkout of this repository (`djc23_celery`)
- A terminal (shell) open in the local checkout of this repository

## Getting started

1. Create a Python 3.11 virtualenv:

   ```sh
   echo "layout python python3.11" > .envrc
   direnv allow
   ```

2. Install requirements:

   ```sh
   python -m pip install -r requirements.txt
   ```

3. Run migrations:

   ```sh
   python manage.py migrate
   ```

4. Start broker (RabbitMQ):

   ```sh
   docker-compose up -d
   ```

## Generating fake data

Generate 100,000 fake voters and voter registrations in the database:

```sh
python manage.py create_fake_voter_data 100000
```

## Starting Celery processes

### `worker`

In one terminal, start the Celery worker with a concurrency of 8 (or another number of your choosing):

```sh
celery -A djc23_celery worker -l INFO -c 8
```

### `beat`

If testing `beat` (not needed for the management commands below), start the process in another terminal

```sh
celery -A djc23_celery beat -l INFO
```

## Testing tasks with management commands

These commands should be run in another terminal. You can watch the log output in the Celery `worker` terminal.

### Option 1: All in one

```sh
python manage.py queue_task all_in_one
```

In the celery worker terminal, you should see a single task kick off, and iterate through the centers one by one:

```
[2023-10-04 15:18:46,535: INFO/MainProcess] Task voter_rolls.tasks.task_all_in_one[5b3cdfef-234a-4202-9e7c-e9c5fb19fe89] received
[2023-10-04 15:18:46,547: WARNING/ForkPoolWorker-7] Writing center list for SUWANNEE MIDDLE SCHOOL (88282)
[2023-10-04 15:18:46,564: WARNING/ForkPoolWorker-7] Assigning stations for 88282 (SUWANNEE MIDDLE SCHOOL)
<snip>
[2023-10-04 15:19:35,894: WARNING/ForkPoolWorker-7] Total pages written: 263
[2023-10-04 15:19:35,900: INFO/ForkPoolWorker-7] Task voter_rolls.tasks.task_all_in_one[5b3cdfef-234a-4202-9e7c-e9c5fb19fe89] succeeded in 49.36396820799564s: None
```

### Option 2:

```sh
python manage.py queue_task parallelize_tasks_by_center_with_join
```

This time, you'll see a number of tasks kick off all at once (one for each center), and then the parent task will terminate with a `RuntimeError`:

```
[2023-10-04 15:20:36,676: INFO/MainProcess] Task voter_rolls.tasks.task_parallelize_tasks_by_center_with_join[43988c5a-f145-4e13-acf7-b1413eab813b] received
[2023-10-04 15:20:36,698: INFO/MainProcess] Task voter_rolls.tasks.task_generate_lists_for_one_center[6ff5d8fe-f80b-4511-9394-92537cb4ae67] received
[2023-10-04 15:20:36,699: INFO/MainProcess] Task voter_rolls.tasks.task_generate_lists_for_one_center[5dcfe255-67ef-4e08-a296-cc7b84481a25] received
<snip>
RuntimeError: Never call result.get() within a task!
```

The other tasks have already been queued, however, so you'll see them continue to execute.

### Option 3: Queue tasks by center with chord

```sh
python manage.py queue_task queue_tasks_by_center_with_chord
```

This time, the output should look similar to Option 2, but without the exception. Once all the center-level tasks have been executed, you'll see the `task_sum_pages` task get queued and immediately return the sum of the results from the previous tasks:

```
[2023-10-04 15:23:59,002: INFO/MainProcess] Task voter_rolls.tasks.task_sum_pages[a132f8cc-e3ba-49a9-aa8c-595842df9912] received
[2023-10-04 15:23:59,002: WARNING/ForkPoolWorker-7] sum_pages: Total pages written: 263
[2023-10-04 15:23:59,005: INFO/ForkPoolWorker-7] Task voter_rolls.tasks.task_sum_pages[a132f8cc-e3ba-49a9-aa8c-595842df9912] succeeded in 0.0030205770017346367s: None
```

## Option 4: Assign all stations in parallel

```sh
python manage.py queue_task assign_all_stations_in_parallel
```

When this task is executed, you should see one instance of `task_assign_stations_for_one_center` get kicked off for every center in the database. While the performance implications aren't noticeable for our test database size, it will become inefficient with a larger database and more queries. As noted in the talk, this is a type of database-intensive work that is better optimized through the database queries themselves, rather than trying to do more things at once.

```
[2023-10-04 15:25:46,769: INFO/MainProcess] Task voter_rolls.tasks.task_assign_all_stations_in_parallel[6fcd7ce3-7784-4de5-9c1e-1dce39b905b8] received
[2023-10-04 15:25:46,826: INFO/MainProcess] Task voter_rolls.tasks.task_assign_stations_for_one_center[36b66ad9-f6b4-4472-a133-531f14c86b78] received
[2023-10-04 15:25:46,827: INFO/MainProcess] Task voter_rolls.tasks.task_assign_stations_for_one_center[596c4efd-afc9-4ea0-8b58-9ac70a266eb5] received
```

## Option 5A: Assign stations and generate lists with starmap

```sh
python manage.py queue_task assign_stations_and_generate_lists_with_starmap
```

When this task is executed, you will see Celery queue and begin to execute a single task that iterates through all the `(center_id, station_id)` pairs in order:

```
[2023-10-04 15:28:52,035: INFO/ForkPoolWorker-7] Task voter_rolls.tasks.task_assign_stations_and_generate_lists_with_starmap[61616618-bb2a-4c0a-a09f-bf7c74e88821] succeeded in 0.37203644499822985s: None
[2023-10-04 15:28:52,040: WARNING/ForkPoolWorker-1] Writing center list for Mayville Middle (24915), station 1 with 500 voters
[2023-10-04 15:28:54,516: WARNING/ForkPoolWorker-1] Writing center list for Mayville Middle (24915), station 2 with 500 voters
[2023-10-04 15:28:56,834: WARNING/ForkPoolWorker-1] Writing center list for Mayville Middle (24915), station 3 with 186 voters
<snip>
[2023-10-04 15:29:40,687: INFO/ForkPoolWorker-1] Task celery.starmap[1142f715-66f5-4376-bbd6-58a1e23a3ec2] succeeded in 48.653234126992174s: [13, 13, 5, 13, 13, 13, 13, 4, 3, 9, 13, 2, 9, 13, 5, 13, 12, 13, 13, 13, 13, 13, 3, 13, 13, 3]
```

The performance is relatively similar to Option 1 (48 vs 49 seconds).

## Option 5B: Assign stations and generate lists with group

```sh
python manage.py queue_task assign_stations_and_generate_lists_with_chord
```

With this option, you will see a task for each `(center_id, station_id)` pair queued immediately, which are executed in parallel by all configured workers.

```
[2023-10-04 15:31:19,003: INFO/MainProcess] Task voter_rolls.tasks.task_generate_lists_for_one_station[e7e738b1-92f8-449f-899b-9ccd6a8c3e10] received
<snip>
[2023-10-04 15:31:38,402: INFO/ForkPoolWorker-4] Task voter_rolls.tasks.task_generate_lists_for_one_station[f40367a2-27da-4b25-a013-d5551e7622e5] succeeded in 4.487195311012329s: 13
```

Since all the work is done in smaller tasks, there is not a total time taken printed anywhere, but you can compare the timestamps of the first and last task to calculate the time taken (in this case, about 19 seconds).

When all the tasks in the group have been completed, `task_sum_pages` is queued and executed again to tally the results:

```
[2023-10-04 15:31:38,403: INFO/MainProcess] Task voter_rolls.tasks.task_sum_pages[e09cba55-a1f4-45f9-9a4e-57739d149f93] received
[2023-10-04 15:31:38,405: WARNING/ForkPoolWorker-7] sum_pages: Total pages written: 263
[2023-10-04 15:31:38,407: INFO/ForkPoolWorker-7] Task voter_rolls.tasks.task_sum_pages[e09cba55-a1f4-45f9-9a4e-57739d149f93] succeeded in 0.002908542999648489s: None
```
