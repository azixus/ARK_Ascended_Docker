#!/bin/bash
RCON_CMDLINE=( rcon -a 127.0.0.1:${RCON_PORT} -p ${ARK_ADMIN_PASSWORD} )

get_and_check_pid() {
    # Get PID
    ark_pid=$(cat "$PID_FILE" 2>/dev/null)
    if [[ -z "$ark_pid" ]]; then
        echo "0"
        return
    fi

    # Check process is still alive
    if ps -p $ark_pid > /dev/null; then
        echo "$ark_pid"
    else
        echo "0"
    fi
}

status() {
    # Get server PID
    ark_pid=$(get_and_check_pid)
    if [[ "$ark_pid" == 0 ]]; then
        echo "Server PID not found (server offline?)"
        return
    fi    

    echo "Server PID $ark_pid"

    ark_port=$(ss -tupln | grep "GameThread" | grep -oP '(?<=:)\d+')
    if [[ -z "$ark_port" ]]; then
        echo "Server not listening"
        return
    fi

    echo "Server listening on port $ark_port"
    
    # Check number of players
    out=$(${RCON_CMDLINE[@]} ListPlayers 2>/dev/null)
    res=$?
    if [[ $res == 0 ]]; then
        echo "Server is up"
        num_players=0
        if [[ "$out" != "No Players"* ]]; then
            num_players=$(echo "$out" | wc -l)
        fi
        echo "$num_players players connected"
    else
        echo "Server is down"
    fi
}

start() {
    # Check server not already running
    ark_pid=$(get_and_check_pid)
    if [[ "$ark_pid" != 0 ]]; then
        echo "Server is already running."
        return
    fi    

    echo "Starting server on port ${SERVER_PORT}"
    echo "-------- STARTING SERVER --------" >> $LOG_FILE

    # Start server in the background + nohup and save PID
    nohup /opt/manager/manager_server_start.sh >/dev/null 2>&1 &
    ark_pid=$!
    echo "$ark_pid" > $PID_FILE
    sleep 3

    echo "Server should be up in a few minutes"
}

stop() {
    # Get server pid
    ark_pid=$(get_and_check_pid)
    if [[ "$ark_pid" == 0 ]]; then
        echo "Server PID not found (server offline?)"
        return
    fi    

    if [[ $1 == "--saveworld" ]]; then
        saveworld
    fi

    echo "Stopping server gracefully..."
    echo "-------- STOPPING SERVER --------" >> $LOG_FILE

    # Check number of players
    out=$(${RCON_CMDLINE[@]} DoExit 2>/dev/null)
    res=$?
    force=false
    if [[ $res == 0  && "$out" == "Exiting..." ]]; then
        echo "Waiting ${SERVER_SHUTDOWN_TIMEOUT}s for the server to stop"
        timeout $SERVER_SHUTDOWN_TIMEOUT tail --pid=$ark_pid -f /dev/null
        res=$?

        # Timeout occurred
        if [[ "$res" == 124 ]]; then
            echo "Server still running after $SERVER_SHUTDOWN_TIMEOUT seconds"
            force=true
        fi
    else
        force=true
    fi

    if [[ "$force" == true ]]; then
        echo "Forcing server shutdown"
        kill -INT $ark_pid

        timeout $SERVER_SHUTDOWN_TIMEOUT tail --pid=$ark_pid -f /dev/null
        res=$?
        # Timeout occurred
        if [[ "$res" == 124 ]]; then
            kill -9 $ark_pid
        fi
    fi

    echo "" > $PID_FILE
    echo "Done"
    echo "-------- SERVER STOPPED --------" >> $LOG_FILE
}

restart() {
    stop "$1"
    start
}

saveworld() {
    # Get server pid
    ark_pid=$(get_and_check_pid)
    if [[ "$ark_pid" == 0 ]]; then
        echo "Server PID not found (server offline?)"
        return
    fi    

    echo "Saving world..."
    out=$(${RCON_CMDLINE[@]} SaveWorld 2>/dev/null)
    res=$?
    if [[ $res == 0 && "$out" == "World Saved" ]]; then
        echo "Success!"
    else
        echo "Failed."
    fi
}

custom_rcon() {
    # Get server pid
    ark_pid=$(get_and_check_pid)
    if [[ "$ark_pid" == 0 ]]; then
        echo "Server PID not found (server offline?)"
        return
    fi    

    out=$(${RCON_CMDLINE[@]} "${@}" 2>/dev/null)
    echo "$out"
}

update() {
    echo "Updating ARK Ascended Server"
    
    stop --saveworld
    /opt/steamcmd/steamcmd.sh +force_install_dir /opt/arkserver +login anonymous +app_update ${ASA_APPID} +quit
    # Remove unnecessary files (saves 6.4GB.., that will be re-downloaded next update)
    if [[ -n "${REDUCE_IMAGE_SIZE}" ]]; then 
        rm -rf /opt/arkserver/ShooterGame/Binaries/Win64/ArkAscendedServer.pdb
        rm -rf /opt/arkserver/ShooterGame/Content/Movies/
    fi

    echo "Update completed"
    start
}

backup(){
    echo "Creating backup. Backups are saved in your ark_backup folder"
    # saving before creating the backup
    saveworld
    # sleep is nessecary because the server seems to write save files after the saveworld function ends and thus tar runs into errors.
    sleep 10
    # Use backup script
    /opt/manager/manager_backup.sh

    res=$?
    if [[ $res == 0 ]]; then
        echo "BACKUP CREATED" >> $LOG_FILE
    else
        echo "creating backup failed"
    fi
}

restoreBackup(){
    echo "Stopping the server."
    stop
    sleep 5
    # restoring the backup
    /opt/manager/manager_restore_backup.sh
    
    sleep 5
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
        "backup")
            backup
            ;;
        "restore")
            restoreBackup
            ;;
        *)
            echo "Invalid action. Supported actions: status, start, stop, restart, saveworld, rcon, update, backup, restore."
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
