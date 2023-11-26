#!/bin/python3
import argparse

# Python 3.11+ compatible import
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from server import start, stop, restart, update
from status import server_status
from config import get_config
from custom_logging import Logger
from ark_rcon import echo_send
from backup import backup, restore

logger = Logger.get_logger(__name__)


def main():
    # Initializes common parser arguments, e.g. start/restart,

    ### GENERIC
    generic_parser = argparse.ArgumentParser()
    generic_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        required=False,
        help="Make logs more verbose",
    )

    generic_parser.add_argument(
        "-c",
        "--config",
        required=False,
        help="Manager configuration file",
        default="./config.toml",
    )
    ### GENERIC END

    ### START/RESTART
    start_restart_parser = argparse.ArgumentParser(add_help=False)
    start_restart_parser.add_argument(
        "--no-autoupdate",
        action="store_true",
        required=False,
        help="Disables automatic updating on startup if it is enabled",
    )
    # start_restart_parser.add_argument(
    #     "--alwaysrestart",
    #     action="store_true",
    #     required=False,
    #     help="Enable automatically restarting the server even if it crashes without becoming ready for player connections.",
    # )
    ### START/RESTART END

    top_actions_parser = argparse.ArgumentParser(
        prog="manager",
        description="ARK Survival Ascended server manager",
    )

    actions_parser = top_actions_parser.add_subparsers(
        title="action", help="desired action to execute", required=True, dest="action"
    )

    start_parser = actions_parser.add_parser(
        name="start",
        parents=[generic_parser, start_restart_parser],
        add_help=False,
        description="Starts the server and puts it into the background",
        help="starts the server",
    )
    start_parser.add_argument(
        "--clean",
        action="store_true",
        required=False,
        help="Executes a clean startup by cleaning pid and log files",
    )

    restart_parser = actions_parser.add_parser(
        name="restart",
        parents=[generic_parser, start_restart_parser],
        add_help=False,
        description="Restarts the server and puts it into the background",
        help="restarts the server",
    )
    restart_parser.add_argument(
        "--warn",
        action="store_true",
        required=False,
        help="Warns any connected players that the server is going down",
    )

    stop_parser = actions_parser.add_parser(
        name="stop",
        parents=[generic_parser],
        add_help=False,
        description="Stops the server if it is running",
        help="stops the server",
    )
    stop_parser.add_argument(
        "--warn",
        action="store_true",
        required=False,
        help="Warns any connected players that the server is going down",
    )
    stop_parser.add_argument(
        "--saveworld",
        action="store_true",
        required=False,
        help="Saves the world using saveworld - usually not necessary, as server usually saves the world on a graceful shutdown",
    )

    update_parser = actions_parser.add_parser(
        name="update",
        parents=[generic_parser, start_restart_parser],
        add_help=False,
        description="Updates the server to the newest available version",
        help="updates the server",
    )
    update_parser.add_argument(
        "--no-autostart",
        action="store_true",
        required=False,
        help="Do not automatically restart the server upon successful update",
    )
    update_parser.add_argument(
        "--force",
        action="store_true",
        required=False,
        help="Stop the server without requesting user input",
    )
    update_parser.add_argument(
        "--saveworld",
        action="store_true",
        required=False,
        help="Saves the world before updating the server",
    )

    status_parser = actions_parser.add_parser(
        name="status",
        parents=[generic_parser],
        add_help=False,
        description="Shows the status of the server",
        help="shows the status",
    )
    status_parser.add_argument(
        "--full",
        action="store_true",
        required=False,
        help="Queries the EOS API to obtain additional status information",
    )

    rcon_parser = actions_parser.add_parser(
        name="rcon",
        parents=[generic_parser],
        add_help=False,
        description="Sends an rcon command to the server",
        help="sends an rcon command",
    )
    rcon_parser.add_argument(
        "command",
        type=str,
        help="Command to send to the RCON server",
    )
    rcon_parser.add_argument(
        "-i",
        "--ip",
        required=False,
        help="IP address of the RCON server, 127.0.0.1 by default",
    )
    rcon_parser.add_argument(
        "-p",
        "--port",
        required=False,
        help="Port of the RCON server, specified in config.toml by default",
    )

    backup_parser = actions_parser.add_parser(
        name="backup",
        parents=[generic_parser],
        add_help=False,
        description="Take a backup of the server files",
        help="backup the server",
    )
    backup_parser.add_argument(
        "--compression-level",
        required=False,
        default=6,
        help="Compression level for the tar compression"
    )

    restore_parser = actions_parser.add_parser(
        name="restore",
        parents=[generic_parser],
        add_help=False,
        description="Interactively restore a backup of the server files",
        help="restore a backup",
    )
    latest_path = restore_parser.add_mutually_exclusive_group()
    latest_path.add_argument(
        "--latest",
        action="store_true",
        required=False,
        help="Restore the latest backup",
    )
    latest_path.add_argument(
        "-p",
        "--path",
        type=str,
        required=False,
        help="Path to the backup to restore",
    )

    # Parse args
    args = top_actions_parser.parse_args()
    args_dict = vars(args)
    try:
        config = get_config(args.config)
    except tomllib.TOMLDecodeError as e:
        logger.error("[red]Failed to parse configuration file: %s.[/]", e)
        return
    except FileNotFoundError:
        logger.error("[red]File %s not found.[/]", args.config)
        return

    args_dict["config"] = config

    actions = {
        "start": start,
        "restart": restart,
        "stop": stop,
        "update": update,
        "status": server_status,
        "rcon": echo_send,
        "backup": backup,
        "restore": restore,
    }
    try:
        actions[args.action](**args_dict)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception("Process crashed with exception: %s", e)


if __name__ == "__main__":
    main()
