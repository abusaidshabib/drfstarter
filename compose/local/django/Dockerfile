FROM python:3.11.12-slim-bullseye

# Set environment variables for Python and Django
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    DJANGO_SETTINGS_MODULE=config.settings.dev

# set work directory early
WORKDIR /app


RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    git || (apt-get update && apt-get install -y --fix-missing \
    build-essential \
    libpq-dev \
    gettext \
    git) && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


# Copy requirements and install
COPY ./requirements ./requirements
RUN pip install --upgrade pip && \
    pip install -r requirements/local.txt

COPY ./compose/local/django/entrypoint /entrypoint
COPY ./compose/local/django/start /start
RUN dos2unix /entrypoint /start || sed -i 's/\r$//g' /entrypoint /start \
 && chmod +x /entrypoint /start

# Copy project (optional, if not using bind mounts)
COPY . /app/

# Run Django dev server (use host=0.0.0.0 so it works inside Docker)
ENTRYPOINT ["/entrypoint"]
