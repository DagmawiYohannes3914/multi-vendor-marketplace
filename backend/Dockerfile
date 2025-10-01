FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps for psycopg2 and other builds
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev gcc git curl && \
    rm -rf /var/lib/apt/lists/*

# copy only requirements first for layer caching
COPY ./requirements.txt /app/requirements.txt

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# copy app code (mounted in dev via docker-compose volumes)
COPY . /app

# create non-root user
RUN adduser --disabled-password --gecos "" appuser || true
USER appuser

EXPOSE 8000

# default runtime command (overridden by compose where needed)
CMD ["sh", "-c", "python manage.py migrate --noinput && daphne -b 0.0.0.0 -p 8000 marketplace.asgi:application"]
