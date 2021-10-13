#!/bin/bash

set -o nounset -o errexit

# Apply compilemessages local files
echo "Apply compilemessages local files"
python manage.py compilemessages

# Collect static files
# echo "Collect static files"
# python manage.py collectstatic --noinput

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate --noinput

exec "$@"