#!/bin/sh

NAME="DevWorksAccount"
CERTS="../certs/"
SERVER_PEM="$CERTS/server.pem"
SERVER_KEY="$CERTS/server.key"
IP=0.0.0.0
PORT=8000

set -e
export PYTHONUNBUFFERED=1

if [ "$1" = "dev" ]; then
  echo "🚀 Starting Django dev server with runserver_plus..."
  python manage.py runserver_plus $IP:$PORT --cert-file "$SERVER_PEM"
elif [ -z "$1" ]; then
  # Ensure we have a venv
  if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  No virtual environment is active. Please activate it first."
    exit 1
  fi

  echo "🚀 Starting Django server with gunicorn..."
  "$VIRTUAL_ENV/bin/gunicorn" \
    --certfile="$SERVER_PEM" \
    --keyfile="$SERVER_KEY" \
    --bind "$IP:$PORT" \
    "$NAME.wsgi:application"
else
  echo "❌ Error: invalid flag '$1'"
  echo "Usage: $0 [dev]"
  exit 1
fi
