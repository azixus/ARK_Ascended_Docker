#!/bin/bash
# Simple wrapper for docker commands to make life easier.
set -euo pipefail

script_dir="$(dirname "$(realpath "$0")")"

sudo_cmd=( sudo )
if [[ "$EUID" -eq 0 ]] || id -nGz "$USER" | grep -qzxF "docker"; then
	sudo_cmd=()
fi

# Get the container id first. This is somewhat necessary since the next command
# does not use docker compose.
container=$($sudo_cmd docker compose -f "$script_dir/docker-compose.yml" ps -q asa_server)

# Use docker exec, instead of docker compose exec as the latter does not
# override env variables.
$sudo_cmd docker exec -it --env-file "$script_dir/.env" "$container" manager "${@}"
