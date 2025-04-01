#!/bin/bash

# Read and clean the environment variable
USE_EXTERNAL_CLIENT=$(grep -E '^USE_EXTERNAL_CLIENT=' .env | awk -F '=' '{print tolower($2)}' | tr -d '[:space:]')

echo "========================="
echo "USE_EXTERNAL_CLIENT is set to '$USE_EXTERNAL_CLIENT'"
echo "========================="

# Check the condition correctly
if [ "$USE_EXTERNAL_CLIENT" = "false" ]; then
  echo "Running: docker compose -f docker-compose.yaml down"
  docker compose -f docker-compose.yaml down
else
  echo "Running: docker compose -f docker-compose.yaml -f docker-compose.override.yaml down"
  docker compose -f docker-compose.yaml -f docker-compose.override.yaml down
fi
