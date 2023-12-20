#!/bin/bash
set -euo pipefail

script_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

# Simple wrapper for docker commands to make life easier.
sudo_cmd=( sudo )
if [[ "$EUID" -eq 0 ]] || id -nGz "$USER" | grep -qzxF "docker"; then
	sudo_cmd=()
fi

# Short-circuit the logs command since we don't want to run it through the container's manager binary
if [[ "$1" == logs ]]
then
  shift
  ${sudo_cmd[@]} docker compose -f "$script_dir/docker-compose.yml" logs "${@}"
  exit 0
fi

# Get the container id first. This is somewhat necessary since the next command
# does not use docker compose.
container=$(${sudo_cmd[@]} docker compose -f "$script_dir/docker-compose.yml" ps -q asa_server)

# Use docker exec, instead of docker compose exec as the latter does not
# override env variables.
${sudo_cmd[@]} docker exec -it --env-file "$script_dir/.env" "$container" manager "${@}"
