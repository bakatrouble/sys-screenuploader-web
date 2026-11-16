#!/bin/sh
set -e

# Wait for Postgres (DATABASE_URL) then run migrations + collectstatic.
# Compose already orders startup via depends_on/healthchecks; this is a safety net.

echo "Waiting for database..."
attempts=0
until python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connections
connections['default'].ensure_connection()
" 2>/dev/null; do
  attempts=$((attempts + 1))
  if [ "$attempts" -gt 30 ]; then
    echo "Database not reachable after 30 tries, continuing anyway (migrate will show the error)"
    break
  fi
  echo "  database unavailable, retry $attempts/30..."
  sleep 2
done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static..."
python manage.py collectstatic --noinput

echo "Starting: $@"
exec "$@"
