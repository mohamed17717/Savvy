#!/bin/sh

# Wait for Django service to be ready
echo "Waiting for Django service..."
until curl -sS http://django:8000/; do
  sleep 5
done

# Execute the command
exec "$@"
