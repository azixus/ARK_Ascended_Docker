import time
import os
import subprocess
import socket
import psutil
from rich import print, logging

from config import get_cmdline_args, get_port, get_server_binary
from steamcmd import install_update_game
from status import is_server_running, store_pid, clear_pid, get_real_server_port
import ark_rcon

# logger = logging.getLogger("server")


def install(config: dict, **kwargs: any):
    game_folder = config["ark"]["install_folder"]
    appid = config["ark"]["appid"]
    steamcmd_folder = config["steamcmd"]

    # Install the game
    print(f"Installing the game in {game_folder}.")
    install_update_game(steamcmd_folder, game_folder, appid)


def update(
    config: dict,
    start_on_success: bool = False,
    force: bool = False,
    saveworld: bool = True,
    **kwargs: any,
):
    # If server running, ask user unless force is True
    pid = is_server_running(config)
    if pid:
        print(f"[red]Server is already running on PID {pid}[/red]")
        if not force:
            # Ask user input, return by default
            choice = input("Would you like to stop the server now? [y/N]: ").lower()
            if choice not in ["y", "yes"]:
                return

        stop(config, saveworld=saveworld)

    game_folder = config["ark"]["install_folder"]
    appid = config["ark"]["appid"]
    steamcmd_folder = config["steamcmd"]["install_folder"]

    # Update the game
    print(f"Updating the game in {game_folder}.")
    install_update_game(
        steamcmd_folder,
        game_folder,
        appid,
    )

    # Start the game if requested
    if start_on_success:
        start(config, no_autoupdate=True)


def start(
    config: dict, no_autoupdate: bool = False, clean: bool = False, **kwargs: any
):
    # Force kill, clean PID and log file
    if clean:
        # Force kill server
        pid = is_server_running(config)
        if pid:
            os.killpg(pid)

        # Create directory structure and clean log file
        log_file = config["ark"]["advanced"]["log_file"]
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("")
        
        # Clean pid file
        pid_file = config["ark"]["advanced"]["pid_file"]
        with open(pid_file, "w", encoding="utf-8") as f:
            f.write("")

    pid = is_server_running(config)
    if pid:
        print(f"[red]Server is already running under PID {pid}[/red]")
        return

    # If not set, update the server
    if not no_autoupdate:
        update(config, start_on_success=False)

    # todo: Load ini files

    # Clean to support other starts than proton
    if config["ark"]["exec"]["start_type"] == "LINUX_PROTON":
        start_cmd = config["ark"]["proton"]["start_command"]
        start_env = config["ark"]["proton"]["start_env"]
        start_args = config["ark"]["proton"]["start_args"]

        # Check server file exists
        server_exec_path = get_server_binary(config)
        if server_exec_path is None:
            print("[red]Server is not installed.[/red]")
            return

        # Build start command without arguments
        start_cmd = [start_cmd, start_args, server_exec_path]
    else:
        print("[red]Unknown start type.[/red]")
        return

    # Concatenate optional args to the start_cmd list
    main_args, flags_args, opts_args = get_cmdline_args(config)

    # For some obscure reason, ArkAscendedServer.exe expects a
    # [space]-splitted argv for the main args.
    # E.g., TheIsland_WP?SessionName="My ASA Server"
    #       => argv[i]   = TheIsland_WP?SessionName="My
    #       => argv[i+1] = ASA
    #       => argv[i+2] = Server"
    # todo: Likely need to fix when Linux binaries are released
    start_cmd = start_cmd + main_args.split(" ") + flags_args + opts_args

    # Build environment
    custom_env = os.environ.copy()
    for key, val in start_env.items():
        custom_env[key] = val

    # Start server and store PGID = PID. We use it to kill a group of process
    print(f"Executing {' '.join(start_cmd)}")
    ark_server = subprocess.Popen(
        start_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=custom_env,
        # preexec_fn=os.setpgrp,
        start_new_session=True
    )
    pid = ark_server.pid
    pgid = os.getpgid(pid)
    assert pid == pgid

    print(f"Server started under PID {pid}. Waiting 5 seconds...")
    try:
        # Wait and return if process dies early
        ret = ark_server.wait(timeout=5)
        print(f"[red]Server process died, ret = {ret}.[/red]")
        print(list(ark_server.stdout))
        return
    # Process still alive after timeout, OK
    except subprocess.TimeoutExpired:
        print("Server process still alive")

    # Try to identify socket for 5 seconds
    server_port = get_port(config)
    up = False
    for _ in range(0, 5):
        l_port = get_real_server_port(config, pid)
        if l_port:
            if l_port == server_port:
                up = True
                break
            else:
                print(
                    f"[red]Server listening on port {l_port} instead of {server_port}.[/red]"
                )
                return

        time.sleep(1)

    if not up:
        print("[red]Server still not listening after 5 seconds.[/red]")
        return

    print(
        f"[green]Server listening on port {server_port} and should be ready in a few seconds.[/green]"
    )

    # Save PID / PGID
    store_pid(config, pid)


def restart(
    config: dict, saveworld: bool = False, no_autoupdate: bool = False, **kwargs: any
):
    pid = is_server_running(config)
    if pid is None:
        print("[red]Server is not running.[/red]")
        return

    stop(config, saveworld=saveworld)
    start(config, no_autoupdate=no_autoupdate)


def stop(config: dict, saveworld: bool = False, **kwargs: any):
    pid = is_server_running(config)
    if pid is None:
        print("[red]Server is not running.[/red]")
        return

    if saveworld:
        # todo: manage success / failure
        print("Saving world... ", end="")
        try:
            if ark_rcon.saveworld(config):
                print("Done.")
            else:
                print("Failed.")
        except TimeoutError:
            print("[red]Failed to run SaveWorld.[/red]")

    # Try to stop the server gracefully by calling DoExit
    print("Attempting to stop gracefully...")
    try:
        ark_rcon.doexit(config, fastcrash=True)
        clean_shutdown = True
    except TimeoutError:
        print("[red]Failed to run DoExit.[/red]")
        clean_shutdown = False

    # If DoExit worked, wait for process to die
    if clean_shutdown:
        timeout = config["ark"]["advanced"]["do_exit_timeout"]
        p = psutil.Process(pid)
        print(f"Waiting {timeout}s for the server to stop.")
        try:
            p.wait(timeout=timeout)
            print("[green]Server has been stopped.[/green]")
        except psutil.TimeoutExpired:
            print("[red]Failed to stop server gracefully.[/red]")
            clean_shutdown = False

    # If DoExit failed / process still lives, kill the process group
    if not clean_shutdown:
        print("Forcing server shutdown... ", end="")
        os.killpg(pid, 9)
        print("Done.")

    clear_pid(config)
