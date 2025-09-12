#!/bin/sh

# Exit on error
set -e

# Wait for Postgres (optional, see below)
echo "Waiting for postgres..."
until nc -z account_db 5432; do
  sleep 1
done

echo "Postgres is up - continuing..."


#mkdir -p /root/.config/sops/age
#ln -s /run/secrets/sops_age_key /root/.config/sops/age/keys.txt
#echo "SOPS key linked to /root/.config/sops/age/keys.txt"

# `enc.server_configurations.yaml` should probably be in secrets also
sops -d /app/enc.server_configurations.yaml > /app/server_configurations.yaml

# Run migrations
python manage.py migrate --noinput

# Apply custom CA certificate if provided
python manage.py apply_ca
# Start server
exec "$@"
