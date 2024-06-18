#!/bin/bash
# This file is called by manager.sh to start a new instance of ASA

# Server main options
cmd="${SERVER_MAP}?listen?SessionName=\"${SESSION_NAME}\"?Port=${SERVER_PORT}"
if [ -n "${MAX_PLAYERS}" ]; then
    cmd="${cmd}?MaxPlayers=${MAX_PLAYERS}"
fi

if [ -n "${SERVER_PASSWORD}" ]; then
    cmd="${cmd}?ServerPassword=${SERVER_PASSWORD}"
fi

if [ -n "${ARK_ADMIN_PASSWORD}" ]; then
    cmd="${cmd}?ServerAdminPassword=\"${ARK_ADMIN_PASSWORD}\""
fi

if [ -n "${RCON_PORT}" ]; then
    cmd="${cmd}?RCONEnabled=True?RCONPort=${RCON_PORT}"
fi

cmd="${cmd}${ARK_EXTRA_OPTS}"

# append MODS and MAP_MODS to mods, separated by comma if both are set
mods=""
if [ -n "${MAP_MODS}" ]; then
    mods="${MAP_MODS}"
fi
if [ -n "${MODS}" ]; then
    if [ -n "${mods}" ]; then
        mods="${mods},${MODS}"
    else
        mods="${MODS}"
    fi
fi

# Server dash options
# Install mods
if [ -n "${mods}" ]; then
    ark_flags="${ark_flags} -mods=${mods}"
fi

ark_flags="${ark_flags} -log"

if [ -n "${DISABLE_BATTLEYE}" ]; then
    ark_flags="${ark_flags} -NoBattlEye"
else
    ark_flags="${ark_flags} -BattlEye"
fi

if [ -n "${MAX_PLAYERS}" ]; then
    ark_flags="${ark_flags} -WinLiveMaxPlayers=${MAX_PLAYERS}"
fi

ark_flags="${ark_flags} ${ARK_EXTRA_DASH_OPTS}"

#fix for docker compose exec / docker exec parsing inconsistencies
STEAM_COMPAT_DATA_PATH=$(eval echo "$STEAM_COMPAT_DATA_PATH")

# if AUTO_RESTART is set, restart server if exit code is not 0
while true; do
    #starting server and outputting log file
    if proton run /opt/arkserver/ShooterGame/Binaries/Win64/ArkAscendedServer.exe ${cmd} ${ark_flags} > /dev/null 2>&1
    then
        echo "Server stopped"
        break
    elif [ -n "${AUTO_RESTART}" ]
    then
        echo "Server crashed, restarting in 10 seconds"
        sleep 10
    else
        echo "Server crashed"
        break
    fi
done
