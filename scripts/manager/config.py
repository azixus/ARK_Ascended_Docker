import os
from typing import Optional

# Python 3.11+ compatible import
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def get_ark_args_main(ark_config: dict) -> list:
    """
    Generate command-line arguments for ASA main configuration.

    Parameters:
    - ark_config (dict): A dictionary containing ASA configuration settings.

    Returns:
    - list: A list of command-line arguments, each formatted as '?key=value' (except the ).
    """
    args = []

    # If there are no extra configs in [ark.config.main],
    # set empty dict
    try:
        main_config = ark_config["main"]
    except KeyError:
        main_config = {}

    # Arguments that must be enclosed within quotes
    quote_args = ["SessionName", "ServerAdminPassword"]

    # Parse args
    for key, val in main_config.items():
        # Add quotes
        if key in quote_args:
            # Strip in case quotes were already added
            val = val.strip('"')
            val = f'"{val}"'

        arg = f"?{key}={val}"
        args.append(arg)

    return args


def get_ark_args_flags(ark_config: dict) -> list:
    """
    Generate command-line arguments for ASA flags configuration.

    Parameters:
    - ark_config (dict): A dictionary containing ASA configuration settings.

    Returns:
    - list: A list of command-line arguments, each representing a flag.
    """
    args = []

    # Parse the enable_battleye first, outside [ark.config.main]
    # since it is a special argument. False by default.
    battleye_arg = "-NoBattlEye"
    try:
        if ark_config["enable_battleye"]:
            battleye_arg = "-BattlEye"
    except KeyError:
        pass

    args.append(battleye_arg)

    # If there are no extra configs in [ark.config.flags],
    # set empty dict
    try:
        flags_config = ark_config["flags"]
    except KeyError:
        flags_config = {}

    # Parse flags
    for key, val in flags_config.items():
        if val:
            arg = f"-{key}"
            args.append(arg)

    return args


# Returns ['-EventType=Summer', ...]
def get_ark_args_opts(ark_config: dict) -> list:
    """
    Generate command-line arguments for ASA options configuration.

    Parameters:
    - ark_config (dict): A dictionary containing ASA configuration settings.

    Returns:
    - list: A list of command-line arguments, each representing an option with a value.
    """
    args = []

    # If there are no extra configs in [ark.config.main],
    # set empty dict
    try:
        opts_config = ark_config["opts"]
    except KeyError:
        opts_config = {}

    # Parse opts
    for key, val in opts_config.items():
        arg = f"-{key}={val}"
        args.append(arg)

    return args


# Returns full cmdline arguments
def get_cmdline_args(config: dict) -> tuple[str, list, list]:
    # Ark config parameters
    ark_config = config["ark"]["config"]

    # Parse the map name first, outside [ark.config.main]
    try:
        map_name = ark_config["map"]
    except KeyError:
        raise Exception("Map missing from [ark.config]")

    main_args = get_ark_args_main(ark_config)
    flags_args = get_ark_args_flags(ark_config)
    opts_args = get_ark_args_opts(ark_config)

    main_str = "".join(main_args)
    flags_str = " ".join(flags_args)
    opts_str = " ".join(opts_args)
    cmdline = f"{map_name}{main_str} {flags_str} {opts_str}"

    cmdline = [f"{map_name}{main_str}", flags_str, opts_str]

    return f"{map_name}{main_str}", flags_args, opts_args


def get_config(path: str) -> dict:
    with open(path, "rb") as f:
        config = tomllib.load(f)

    if check_config(config) is False:
        raise ValueError("Invalid configuration file.")

    return config


def check_config(config: dict):
    # Only need the main config parameter, and the map
    return (
        "ark" in config
        and "config" in config["ark"]
        and "appid" in config["ark"]
        and "map" in config["ark"]["config"]
        and "steamcmd" in config
        and "install_folder" in config["steamcmd"]
    )  # and \
    #    'main' in config['ark']['config'] and \
    #        'flags' in config['ark']['config'] and \
    #            'opts' in config['ark']['config'] and \


def get_port(config: dict) -> int:
    try:
        return config["ark"]["config"]["main"]["Port"]
    except KeyError:
        return 7777


def get_rcon_enabled(config: dict) -> bool:
    rcon = False
    try:
        rcon = config["ark"]["config"]["main"]["RCONEnabled"]
    except KeyError:
        pass

    try:
        rcon = config["ark"]["config"]["GameUserSettings"]["ServerSettings"][
            "RCONEnabled"
        ]
    except KeyError:
        pass

    return rcon


def get_rcon_port(config: dict) -> int:
    port = -1

    if get_rcon_enabled(config):
        try:
            port = config["ark"]["config"]["main"]["RCONPort"]
        except KeyError:
            pass

        try:
            port = config["ark"]["config"]["GameUserSettings"]["ServerSettings"][
                "RCONPort"
            ]
        except KeyError:
            pass

    return port


def get_admin_password(config: dict) -> str:
    password = None

    try:
        password = config["ark"]["config"]["main"]["ServerAdminPassword"]
    except KeyError:
        pass

    try:
        password = config["ark"]["config"]["GameUserSettings"]["ServerSettings"][
            "ServerAdminPassword"
        ]
    except KeyError:
        pass

    return password


def get_server_binary(config: dict) -> Optional[str]:
    # Check server file exists
    server_folder = config["ark"]["install_folder"]
    server_rel = config["ark"]["proton"]["server_rel_binary"]

    server_exec_path = os.path.join(server_folder, server_rel)
    if os.path.exists(server_exec_path):
        return server_exec_path
    else:
        return None
