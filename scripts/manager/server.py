import os
import subprocess
import psutil
import pty
import sys
import time

from config import get_cmdline_args, get_port, get_server_binary, build_ini_file
from steamcmd import install_update_game
from schedule import ScheduledAction, get_scheduled_action, sleep_and_warn
from status import (
    is_server_running,
    store_pid,
    clear_pid,
    get_real_server_port,
)
from custom_logging import Logger
from utils import daemonize
import ark_rcon

logger = Logger.get_logger(__name__)


def update(
    config: dict,
    no_autostart: bool = False,
    force: bool = False,
    saveworld: bool = False,
    warn: bool = False,
    **kwargs: any,
):
    """
    Install / Update the ASA server. If the server is running, ask confirmation before the update,
    unless force is set to true.

    Parameters:
        config (dict): A dictionary containing configuration details.
        start_on_success (bool): Start the server after a successful update (default is False).
        force (bool): Force update without asking the user (default is False).
        saveworld (bool): Save the world before stopping the server (default is False).
        **kwargs (any): Additional keyword arguments.

    Returns:
        None
    """
    logger.debug("-------STARTING UPDATE-------")
    # If server running, ask user unless force is True or warn is True
    pid = is_server_running(config)
    if pid:
        logger.warning("[yellow]Server is currently running on PID %s.[/]", pid)
        if not force and not warn:
            # Ask user input, return by default
            choice = input("Would you like to stop the server now? [y/N]: ").lower()
            if choice not in ["y", "yes"]:
                return
        # If warn is requested, run warnings in background
        elif warn:
            do_warn(config, "update")

        stop(config, saveworld=saveworld)

    game_folder = config["ark"]["install_folder"]
    appid = config["ark"]["appid"]
    steamcmd_folder = config["steamcmd"]["install_folder"]

    # Update the game
    logger.info("Updating the game in %s.", game_folder)
    install_update_game(
        steamcmd_folder,
        game_folder,
        appid,
    )
    logger.info("[green]Server updated![/]")
    logger.debug("-------UPDATE DONE-------")

    # Start the game unless disabled
    if not no_autostart:
        start(config, no_autoupdate=True)


def start(
    config: dict, no_autoupdate: bool = False, clean: bool = False, **kwargs: any
):
    """
    Start the ASA server and update it unless no_autoupdate is set.

    Parameters:
        config (dict): A dictionary containing configuration details.
        no_autoupdate (bool): Do not update the server on startup (default is False).
        clean (bool): Force kill the server and clean log/pid files (default is False).
        **kwargs (any): Additional keyword arguments.

    Returns:
        None
    """
    logger.debug("-------STARTING SERVER-------")
    # Force kill, clean PID and log file
    if clean:
        # Force kill server
        pid = is_server_running(config)
        if pid:
            os.killpg(pid)

        # Create directory structure and clean log file
        log_file = config["ark"]["advanced"]["log_file"]
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "wb") as f:
            f.write(b"")

        # Clean pid file
        pid_file = config["ark"]["advanced"]["pid_file"]
        with open(pid_file, "wb") as f:
            f.write(b"")

        # Clean schedule file
        schedule_file = config["ark"]["advanced"]["schedule_file"]
        with open(schedule_file, "wb") as f:
            f.write(b"")

    pid = is_server_running(config)
    if pid:
        logger.warning("[yellow]Server is already running under PID %s[/]", pid)
        return

    # If not set, update the server, but do not start automatically
    if not no_autoupdate:
        update(config, no_autostart=True, warn=False)

    # Set GameUserSettings.ini and Game.ini
    build_ini_file(config, "GameUserSettings")
    build_ini_file(config, "Game")

    # Clean to support other starts than proton
    if config["ark"]["exec"]["start_type"] == "LINUX_PROTON":
        start_cmd = config["ark"]["proton"]["start_command"]
        start_env = config["ark"]["proton"]["start_env"]
        start_args = config["ark"]["proton"]["start_args"]

        # Check server file exists
        server_exec_path = get_server_binary(config)
        if server_exec_path is None:
            logger.error("[red]Server is not installed.[/]")
            return

        # Build start command without arguments
        start_cmd = [start_cmd, start_args, server_exec_path]
    else:
        logger.error("[red]Unknown start type.[/]")
        return

    # Concatenate optional args to the start_cmd list
    main_args, flags_args, opts_args = get_cmdline_args(config)

    # For some obscure reason, ArkAscendedServer.exe expects a
    # [space]-splitted argv for the main args, ignoring quotes.
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
    logger.info("Starting the server with %s", " ".join(start_cmd))
    # Need to run in a pseudo-tty to prevent ARK from double forking (don't ask me why)
    m, s = pty.openpty()
    ark_server = subprocess.Popen(
        start_cmd,
        stdin=s,
        stdout=s,
        stderr=s,
        env=custom_env,
        start_new_session=True,
    )
    pid = ark_server.pid
    pgid = os.getpgid(pid)
    assert pid == pgid

    logger.debug("Server started under PID %s. Waiting 5 seconds...", pid)
    try:
        # Wait and return if process dies early
        ret = ark_server.wait(timeout=5)
        logger.error("[red]Server process died, ret = %s.[/]", ret)
        logger.debug(os.read(m, 10240))
        return
    # Process still alive after timeout, OK
    except subprocess.TimeoutExpired:
        logger.info("Server process still alive")

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
                logger.error(
                    "[red]Server listening on port %s instead of %s.[/]",
                    l_port,
                    server_port,
                )
                return

        time.sleep(1)

    if not up:
        logger.error("[red]Server still not listening after 5 seconds.[/]")
        logger.warning("[yellow]Killing server process.[/]")
        os.killpg(pid, 9)
        return

    logger.info(
        "[green]Server listening on port %s and should be ready in a few seconds.[/]",
        server_port,
    )

    # Save PID / PGID
    store_pid(config, pid)
    logger.debug("-------SERVER STARTED-------")


def restart(
    config: dict,
    saveworld: bool = False,
    no_autoupdate: bool = False,
    warn: bool = False,
    **kwargs: any,
):
    """
    Restart the ASA server and update it unless no_autoupdate is set.

    Parameters:
        config (dict): A dictionary containing configuration details.
        saveworld (bool): Save the world with SaveWorld before stopping the server (default is False).
        no_autoupdate (bool): Do not update the server on startup (default is False).
        **kwargs (any): Additional keyword arguments.

    Returns:
        None
    """

    logger.debug("-------SERVER RESTARTING-------")
    pid = is_server_running(config)
    if pid is None:
        logger.warning("[yellow]Server is not running.[/]")
        return

    if sche := get_scheduled_action(config) != ScheduledAction.NONE:
        logger.warning(
            "[yellow]There is already an action in progress: %s[/]", sche.name
        )
        return

    # If warn is requested, run warnings in background
    if warn:
        do_warn(config, "restart")

    stop(config, saveworld=saveworld, warn=False)
    start(config, no_autoupdate=no_autoupdate)

    logger.debug("-------SERVER RESTARTED-------")


def stop(config: dict, saveworld: bool = False, warn: bool = False, **kwargs: any):
    """
    Stop the ASA server gracefully or forcefully if it fails.

    Parameters:
        config (dict): A dictionary containing configuration details.
        saveworld (bool): Save the world with SaveWorld before stopping the server (default is False).
        **kwargs (any): Additional keyword arguments.

    Returns:
        None
    """
    logger.debug("-------STOPPING SERVER-------")
    pid = is_server_running(config)
    if pid is None:
        logger.warning("[yellow]Server is not running.[/]")
        return

    # If warn is requested, run warnings in background
    if warn:
        do_warn(config, "stop")

    if saveworld:
        logger.debug("Saving world... ")
        try:
            if ark_rcon.saveworld(config):
                logger.info("[green]World saved successfully.[/]")
            else:
                logger.error("[red]Failed to save world.[/]")
        except TimeoutError:
            logger.error("[red]Timed out while running SaveWorld.[/]")

    # Try to stop the server gracefully by calling DoExit
    logger.info("Stopping server gracefully...")
    try:
        ark_rcon.doexit(config, fastcrash=True)
        clean_shutdown = True
    except TimeoutError:
        logger.error("[red]Failed to run DoExit.[/]")
        clean_shutdown = False

    # If DoExit worked, wait for process to die
    if clean_shutdown:
        timeout = config["ark"]["advanced"]["do_exit_timeout"]
        p = psutil.Process(pid)
        logger.info("Waiting %ss for the server to stop.", timeout)
        try:
            p.wait(timeout=timeout)
            logger.info("[green]Server has been stopped.[/]")
        except psutil.TimeoutExpired:
            logger.error("[red]Failed to stop server gracefully.[/]")
            clean_shutdown = False

    # If DoExit failed / process still lives, kill the process group
    if not clean_shutdown:
        logger.warning("[yellow]Forcing server shutdown.[/]")
        os.killpg(pid, 9)

    clear_pid(config)
    logger.debug("-------SERVER STOPPED-------")


def do_warn(config: dict, warn_type: str) -> bool:
    try:
        warn_config: list = config["ark"]["warn"][warn_type]
    except KeyError:
        logger.error("[red]Failed to read warn configuration.[/]")
        sys.exit(1)  # Exit process immediately

    # Daemonize process
    logger.info("[green]Starting background process to warn players.[/]")
    daemon_pid = daemonize()
    if daemon_pid > 0:
        logger.info(
            "[green]Background process successfully started as PID %s.[/]",
            daemon_pid,
        )
        sys.exit(0)  # Exit process immediately

    # We are now in a background process
    # Wait and display warning(s)
    sleep_and_warn(config, warn_config)
