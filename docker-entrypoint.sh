#!/bin/bash -x

# Exit immediately if a command exits with a non-zero status
set -e

# Wait for the PostgreSQL service to be ready
until psql $DATABASE_URL -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - continuing"

python manage.py migrate --noinput && python manage.py collectstatic --noinput || exit 1
exec "$@"
