# DjangoCon 2023 Celery Setup

This repo contains the code accompanying the talk [How to Schedule Tasks with Celery and Django](https://2023.djangocon.us/talks/how-to-schedule-tasks-with-celery-and-django/) from DjangoCon 2023. It's based Django 4.2 and Celery 5.3.

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

## Celery Commands

### `worker`

```sh
celery -A djc23_celery worker -l INFO
```

### `beat`

```sh
celery -A djc23_celery beat -l INFO
```
