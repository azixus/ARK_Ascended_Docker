#!/bin/bash

#exit on error
set -e

# Start the server and clean logs/pid file. Weird hack with script
# to allow python to set process group.
0<&1 script -qefc "manager start --clean" /dev/null | cat &

# Register SIGTERM handler to stop server gracefully
trap "manager stop --saveworld" SIGTERM

# Extract log file from the config
log_file=$(awk -F '=' '/^\[ark\.advanced\]/{flag=1; next} /^\[/{flag=0} flag && /log_file/{gsub(/[[:space:]"'\'']*/, "", $2); print $2}' /opt/arkserver/config.toml)

# Start tail process in the background, then wait for tail to finish.
# This is just a hack to catch SIGTERM signals, tail does not forward
# the signals.
tail -F -n 0 "${log_file}" &
wait $!
