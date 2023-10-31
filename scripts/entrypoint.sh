#!/bin/bash
set -ex

# Create steam directory and set variables
mkdir -p /home/arkuser/.steam/steam/steamapps/compatdata/${ASA_APPID}

# Install ASA server
/opt/steamcmd/steamcmd.sh +force_install_dir /opt/arkserver +login anonymous +app_update ${ASA_APPID} validate +quit

# Show server logs
mkdir -p /opt/arkserver/ShooterGame/Saved/Logs && touch /opt/arkserver/ShooterGame/Saved/Logs/ShooterGame.log
tail -c0 -F /opt/arkserver/ShooterGame/Saved/Logs/ShooterGame.log
