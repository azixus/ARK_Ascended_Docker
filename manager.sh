#!/bin/bash
# Simple wrapper for docker commands to make life easier. 
sudo_cmd=( sudo )
if [[ "$EUID" -eq 0 ]] || id -nGz "$USER" | grep -qzxF "docker"; then
	sudo_cmd=()
fi

# Get the container id first. This is somewhat necessary since the next command
# does not use docker compose.
container=$($sudo_cmd docker compose ps -q)

# Use docker exec, instead of docker compose exec as the latter does not
# override env variables.
$sudo_cmd docker exec -it --env-file .env "$container" manager "${@}"
