#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Waiting for PostgreSQL..."
python - <<'PY'
import os, sys, time
import psycopg2

config = {
    "dbname": os.environ.get("POSTGRES_DB", "firstgame"),
    "user": os.environ.get("POSTGRES_USER", "firstgame"),
    "password": os.environ.get("POSTGRES_PASSWORD", "firstgame"),
    "host": os.environ.get("POSTGRES_HOST", "db"),
    "port": os.environ.get("POSTGRES_PORT", "5432"),
}
for _ in range(60):
    try:
        psycopg2.connect(**config).close()
        break
    except psycopg2.OperationalError:
        time.sleep(1)
else:
    print("PostgreSQL is not available.", file=sys.stderr)
    sys.exit(1)
PY

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Applying database migrations..."
python manage.py migrate

echo "Starting Gunicorn..."
exec "$@"
