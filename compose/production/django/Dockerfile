FROM python:3.11.12-slim-bullseye

# Set environment variables for Python and Django
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    DJANGO_SETTINGS_MODULE=config.settings.prod

# set work directory early
WORKDIR /app

RUN apt-get update \
  # psycopg dependencies
  && apt-get install -y libpq-dev \
  # Translations dependencies (if not needed, remove)
  && apt-get install -y gettext \
  # Additional dependencies (if git is not required in production, remove)
  && apt-get install -y git \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*


# Copy requirements and install
COPY ./requirements ./requirements
RUN pip install --upgrade pip && \
    pip install -r requirements/production.txt

COPY ./compose/production/django/entrypoint /entrypoint
COPY ./compose/production/django/start /start
RUN dos2unix /entrypoint /start || sed -i 's/\r$//g' /entrypoint /start \
 && chmod +x /entrypoint /start

COPY ./compose/production/django/celery/worker/start /start-celeryworker
RUN sed -i 's/\r$//g' /start-celeryworker
RUN chmod +x /start-celeryworker

COPY ./compose/production/django/celery/beat/start /start-celerybeat
RUN sed -i 's/\r$//g' /start-celerybeat
RUN chmod +x /start-celerybeat

COPY ./compose/production/django/celery/flower/start /start-flower
RUN sed -i 's/\r$//g' /start-flower
RUN chmod +x /start-flower

# Copy project (optional, if not using bind mounts)
COPY . /app/

# Run Django dev server (use host=0.0.0.0 so it works inside Docker)
ENTRYPOINT ["/entrypoint"]
