FROM python:3.11.12-slim-bullseye

# Set environment variables for Python and Django
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    DJANGO_SETTINGS_MODULE=config.settings.dev


# Install system dependencies (optional, based on your project needs)
RUN apt-get update \
    # dependencies for building Python packages
    && apt-get install -y build-essential \
    # psycopg dependencies
    && apt-get install -y libpq-dev \
    # Translations dependencies
    && apt-get install -y gettext \
    # Additional dependencies
    && apt-get install -y git \
    # cleaning up unused files
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY ./requirements ./requirements
RUN pip install --upgrade pip && \
    pip install -r requirements/local.txt

COPY ./compose/local/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/local/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

# Copy project (optional, if not using bind mounts)
COPY . /app/

# Set work directory
WORKDIR /app

# Run Django dev server (use host=0.0.0.0 so it works inside Docker)
ENTRYPOINT ["/entrypoint"]
