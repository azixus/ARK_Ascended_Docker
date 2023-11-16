#!/bin/bash

#exit on error
set -e

# Create steam directory and set environment variables
mkdir -p "${STEAM_COMPAT_DATA_PATH}"

# Install or update ASA server + verify installation
/opt/steamcmd/steamcmd.sh +force_install_dir /opt/arkserver +login anonymous +app_update ${ASA_APPID} validate +quit

# Remove unnecessary files (saves 6.4GB.., that will be re-downloaded next update)
if [[ -n "${REDUCE_IMAGE_SIZE}" ]]; then 
    rm -rf /opt/arkserver/ShooterGame/Binaries/Win64/ArkAscendedServer.pdb
    rm -rf /opt/arkserver/ShooterGame/Content/Movies/
fi

#Create file for showing server logs
mkdir -p "${LOG_FILE%/*}" && echo "" > "${LOG_FILE}"

# Start server through manager
echo "" > "${PID_FILE}"
manager start &

# Register SIGTERM handler to stop server gracefully
trap "manager stop --saveworld" SIGTERM

# Start tail process in the background, then wait for tail to finish.
# This is just a hack to catch SIGTERM signals, tail does not forward
# the signals.
tail -F "${LOG_FILE}" &
wait $!
