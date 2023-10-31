#!/bin/bash
RCON_CMDLINE="rcon -a 127.0.0.1:${RCON_PORT} -p ${ARK_ADMIN_PASSWORD}"
LOG_FILE=/opt/arkserver/ShooterGame/Saved/Logs/ShooterGame.log
SHUTDOWN_TIMEOUT=30

status() {
    # Get PID
    ark_pid=$(pgrep -f ".*proton.*ArkAscendedServer.exe")
    if [[ -z $ark_pid ]]; then
        echo "Server PID not found (server offline?)"
        return
    fi

    echo "Server PID $ark_pid"

    ark_port=$(ss -tupln | grep "GameThread" | grep -oP '(?<=:)\d+')
    if [[ -z $ark_port ]]; then
        echo "Server not listening"
        return
    fi

    echo "Server listening on port $ark_port"
    
    # Check number of players
    out=$(${RCON_CMDLINE} ListPlayers 2>/dev/null)
    res=$?
    if [[ $res == 0 ]]; then
        echo "Server is up"
        num_players=0
        if [[ "$out" != "No Players"* ]]; then
            num_players=$(echo -n "$out" | wc -l)
        fi
        echo "$num_players players connected"
    else
        echo "Server is down"
    fi
}

start() {
    echo "Starting server on port ${SERVER_PORT}"
    echo "-------- STARTING SERVER --------" >> $LOG_FILE

    nohup bash /opt/arkserver/start.sh >/dev/null 2>&1 &
    sleep 3

    echo "Server should be up in a few minutes"
}

stop() {
    ark_pid=$(pgrep -f ".*proton.*ArkAscendedServer.exe")
    if [[ -z $ark_pid ]]; then
        echo "Server PID not found (server offline?)"
        return
    fi

    if [[ $1 == "--saveworld" ]]; then
        saveworld
    fi

    echo "Stopping server gracefully..."
    echo "-------- STOPPING SERVER --------" >> $LOG_FILE

    # Check number of players
    out=$(${RCON_CMDLINE} DoExit 2>/dev/null)
    res=$?
    force=false
    if [[ $res == 0  && "$out" == "Exiting..." ]]; then
        echo "Waiting ${SHUTDOWN_TIMEOUT}s for the server to stop"
        timeout $SHUTDOWN_TIMEOUT tail --pid=$ark_pid -f /dev/null
        res=$?

        # Timeout occurred
        if [[ "$res" == 124 ]]; then
            echo "Server still running after $SHUTDOWN_TIMEOUT seconds"
            force=true
        fi
    else
        force=true
    fi

    if [[ "$force" == true ]]; then
        echo "Forcing server shutdown"
        kill -INT $ark_pid

        timeout $SHUTDOWN_TIMEOUT tail --pid=$ark_pid -f /dev/null
        res=$?
        # Timeout occurred
        if [[ "$res" == 124 ]]; then
            kill -9 $ark_pid
        fi
    fi

    echo "Done"
    echo "-------- SERVER STOPPED --------" >> $LOG_FILE
}

restart() {
    stop "$1"
    start
}

saveworld() {
    echo "Saving world..."
    out=$(${RCON_CMDLINE} SaveWorld 2>/dev/null)
    res=$?
    if [[ $res == 0 && "$out" == "World Saved" ]]; then
        echo "Success!"
    else
        echo "Failed."
    fi
}

custom_rcon() {
    out=$(${RCON_CMDLINE} "${@}" 2>/dev/null)
    echo "$out"
}

update() {
    echo "Updating ARK Ascended Server"
    
    stop --saveworld
    /opt/steamcmd/steamcmd.sh +force_install_dir /opt/arkserver +login anonymous +app_update 2430930 validate +quit

    echo "Update completed"
    start
}

# Main function
main() {
    action="$1"
    option="$2"

    case "$action" in
        "status")
            status
            ;;
        "start")
            start
            ;;
        "stop")
            stop "$option"
            ;;
        "restart")
            restart "$option"
            ;;
        "saveworld")
            saveworld
            ;;
        "rcon")
            custom_rcon "${@:2:99}"
            ;;
        "update") 
            update
            ;;
        *)
            echo "Invalid action. Supported actions: status, start, stop, restart, saveworld, rcon, update."
            exit 1
            ;;
    esac
}

# Check if at least one argument is provided
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <action> [--saveworld]"
    exit 1
fi

main "$@"
