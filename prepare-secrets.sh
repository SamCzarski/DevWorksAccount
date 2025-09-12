#!/bin/bash
set -euo pipefail

# Decrypt just the DB_PASS from your encrypted config
sops -d --extract '["DB_PASS"]' enc.server_configurations.yaml > db_password

# Start the stack
docker compose up -d
