export STEAM_COMPAT_CLIENT_INSTALL_PATH="/home/arkuser/.steam/steam"
export STEAM_COMPAT_DATA_PATH="/home/arkuser/.steam/steam/steamapps/compatdata/${ASA_APPID}"

# Server main options
cmd="${SERVER_MAP}?listen?SessionName=\"${SESSION_NAME}\"?Port=${SERVER_PORT}"
if [ -n ${MAX_PLAYERS} ]; then
    cmd="${cmd}?MaxPlayers=${MAX_PLAYERS}"
fi

if [ -n ${SERVER_PASSWORD} ]; then
    cmd="${cmd}?ServerPassword=${SERVER_PASSWORD}"
fi

if [ -n ${ARK_ADMIN_PASSWORD} ]; then
    cmd="${cmd}?ServerAdminPassword=\"${ARK_ADMIN_PASSWORD}\""
fi

if [ -n ${RCON_PORT} ]; then
    cmd="${cmd}?RCONEnabled=True?RCONPort=${RCON_PORT}"
fi

cmd="${cmd}${ARK_EXTRA_OPTS}"

# Server dash options
ark_flags="-log"
if [ -n ${DISABLE_BATTLEYE} ]; then 
    ark_flags="${ark_flags} -NoBattlEye"
else 
    ark_flags="${ark_flags} -BattlEye"
fi

if [ -n ${MAX_PLAYERS} ]; then 
    ark_flags="${ark_flags} -WinLiveMaxPlayers=${MAX_PLAYERS}"
fi

ark_flags="${ark_flags} ${ARK_EXTRA_DASH_OPTS}"

proton run /opt/arkserver/ShooterGame/Binaries/Win64/ArkAscendedServer.exe ${cmd} ${ark_flags}