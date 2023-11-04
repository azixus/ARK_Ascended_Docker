#!/bin/bash

#exit on error
set -ex

# Create steam directory and set variables
mkdir -p /home/arkuser/.steam/steam/steamapps/compatdata/${ASA_APPID}

# Install or update ASA server + verify installation
/opt/steamcmd/steamcmd.sh +force_install_dir /opt/arkserver +login anonymous +app_update ${ASA_APPID} validate +quit

# Remove unnecessary files (saves 6.4GB.., that will be re-downloaded next update)
if [[ -n "${REDUCE_IMAGE_SIZE}" ]]; then 
    rm -rf /opt/arkserver/ShooterGame/Binaries/Win64/ArkAscendedServer.pdb
    rm -rf /opt/arkserver/ShooterGame/Content/Movies/
fi

#Create file for showing server logs
mkdir -p /opt/arkserver/ShooterGame/Saved/Logs && echo "" > /opt/arkserver/ShooterGame/Saved/Logs/ShooterGame.log

# Start server through manager
manager start &

tail -f "/opt/arkserver/ShooterGame/Saved/Logs/ShooterGame.log"