#!/bin/python3
import argparse

from server import start, stop, restart, update
from status import server_status
from config import get_config

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
        "--warnreason",
        required=False,
        help="Gives a reason for the shutdown. Defaults to maintenance",
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
    # start_on_success: bool = False,
    # force: bool = False,
    # saveworld: bool = True,

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

    # Parse args
    args = top_actions_parser.parse_args()
    args_dict = vars(args)
    config = get_config(args.config)
    args_dict["config"] = config

    actions = {
        "start": start,
        "restart": restart,
        "stop": stop,
        "update": update,
        "status": server_status,
    }
    actions[args.action](**args_dict)


if __name__ == "__main__":
    main()
