import re
import os
from typing import Optional

# Python 3.11+ compatible import
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
import tomli_w

from utils import Logger

logger = Logger.get_logger(__name__)


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

    return f"{map_name}{main_str}", flags_args, opts_args


def update_ini_file(
    ini_config: dict, ini_name: str, ini_content: str, delete_only: bool = False
) -> str:
    # Since Unreal Engine's configuration files are so damn weird, we only
    # use regex here instead of a proper parser.
    for section, settings in ini_config.items():
        # Select section regex
        section_regex = rf"\[{section}\](?:.*?)(?=(?:\[[^\n]+\])|$)"
        res = re.search(section_regex, ini_content, re.DOTALL | re.IGNORECASE)
        if res:
            section_content = res.group(0).strip()
        else:
            section_content = f"[{section}]"

        # Add key=val pairs to section_content
        for key, val in settings.items():
            # Duplicate variable n time if it is a list
            if isinstance(val, list):
                keyval = "\n".join([f"{key}={v}" for v in val])
            else:
                keyval = f"{key}={val}"

            if not delete_only:
                logger.debug("In %s.%s, setting %s", ini_name, section, keyval)
            else:
                logger.debug("In %s.%s, Removing %s", ini_name, section, keyval)

            # Replace key if it already exists, otherwise add it
            key_regex = rf"\n^{key} *=.*$"
            res = re.findall(key_regex, section_content, re.MULTILINE | re.IGNORECASE)
            # No match, simply add line
            if len(res) == 0:
                if not delete_only:
                    section_content += f"\n{keyval}"
            else:
                if not delete_only:
                    # Replace first occurence of the group
                    section_content = section_content.replace(res[0], f"\n{keyval}", 1)
                else:
                    section_content = section_content.replace(res[0], "", 1)

                # If there are any other occurence, remove them
                for m in res[1:]:
                    section_content = section_content.replace(m, "", 1)

        res = re.search(section_regex, ini_content, re.DOTALL)
        if res:
            ini_content = ini_content.replace(res.group(0), section_content + "\n")
        else:
            ini_content += f"\n\n{section_content}\n"

    return ini_content


def build_ini_file(config: dict, name: str):
    ini_dir = config["ark"]["advanced"]["ini_dir"]
    config_file = os.path.join(ini_dir, f"{name}.ini")
    if not os.path.exists(config_file):
        logger.warning("[yellow]Ini file %s not found.[/]", config_file)

    # Load config, or return
    custom_ini_config = config["ark"]["config"].get(name, None)
    if not custom_ini_config:
        logger.warning("[yellow]No custom settings for %s found.[/]", config_file)
        return

    with open(config_file, "r", encoding="utf-8") as ini_file:
        ini_content = ini_file.read().strip()

    # Check previously loaded config and remove unspecified options
    prev_ini_config_file = config["ark"]["advanced"]["prev_ini_config"]
    prev_ini_config = {}
    prev_ini_config[name] = {}
    try:
        with open(prev_ini_config_file, "rb") as f:
            prev_ini_config.update(tomllib.load(f))

        ini_content = update_ini_file(
            prev_ini_config[name], name, ini_content, delete_only=True
        )
    except FileNotFoundError:
        logger.debug("Previous ini configuration not found.")

    # Update ini config
    ini_content = update_ini_file(
        custom_ini_config, name, ini_content, delete_only=False
    )

    # Save new ini file
    with open(config_file, "w", encoding="utf-8") as ini_file:
        ini_file.write(ini_content.strip())

    # Backup updated config
    if name not in prev_ini_config:
        prev_ini_config[name] = {}
    prev_ini_config[name].update(custom_ini_config)
    with open(prev_ini_config_file, "wb") as f:
        tomli_w.dump(prev_ini_config, f)


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


def get_rcon_port(config: dict) -> Optional[int]:
    port = None

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


def get_admin_password(config: dict) -> Optional[str]:
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
