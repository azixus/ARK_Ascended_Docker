import os
from typing import Optional

import psutil
import requests

from ark_rcon import playercount
from config import get_port
from eos import get_eos_credentials
from utils import Logger

logger = Logger.get_logger(__name__)


def is_server_running(config: dict) -> Optional[int]:
    """
    Check if the server is running by reading the process ID (PID) from the PID file.

    Args:
        config (dict): The configuration settings, including the path to the PID file.

    Returns:
        Optional[int]: The PID of the running server process if it is found, else None.
    """
    # Get PID from file
    pid_file = config["ark"]["advanced"]["pid_file"]
    with open(pid_file, "r", encoding="utf-8") as f:
        try:
            pid = int(f.read())
        except ValueError:
            return None

    if psutil.pid_exists(pid):
        return pid
    else:
        return None


def store_pid(config: dict, pid: int):
    """
    Store the process ID (PID) of the running server in the PID file.

    Args:
        config (dict): The configuration settings, including the path to the PID file.
        pid (int): The process ID to be stored.
    """
    # Save PID / PGID
    with open(config["ark"]["advanced"]["pid_file"], "w", encoding="utf-8") as f:
        f.write(f"{pid}")


def clear_pid(config: dict):
    """
    Clear the stored process ID (PID) in the PID file.

    Args:
        config (dict): The configuration settings, including the path to the PID file.
    """
    # Save PID / PGID
    with open(config["ark"]["advanced"]["pid_file"], "w", encoding="utf-8") as f:
        f.write("")


def get_real_server_port(config: dict, server_pid: int) -> Optional[int]:
    """
    Get the real server port by filtering on the process name (GameThread) and the process group ID (PGID).

    Args:
        config (dict): The configuration settings.
        server_pid (int): The process ID (PID) of the running server.

    Returns:
        Optional[int]: The port number of the server if found, else None.
    """
    for conn in psutil.net_connections(kind="udp"):
        # Some connections have unknown pid
        if conn.pid is None:
            continue

        pgid = os.getpgid(conn.pid)
        if pgid == server_pid:
            p = psutil.Process(conn.pid)
            if p.name() == "GameThread":
                return conn.laddr.port
            else:
                logger.error("[red]Found matching PGID, but invalid name.[/]")

    return None


def get_mod_name(modid: str) -> str:
    url = f"https://api.cfwidget.com/{modid}"
    try:
        resp = requests.get(
            url,
            timeout=2,
        )
        resp_json = resp.json()
        return f"{resp_json.get('title', modid)} ({modid})"
    except TimeoutError:
        return modid


def server_full_status(config: dict, eos_config: dict, server_port: int):
    """
    Check and display detailed information about the Ark server's status using EOS (Epic Online Services).

    Args:
        config (dict): The configuration settings.
        eos_config (dict): The EOS configuration settings, including DedicatedServerClientToken and DeploymentId.
        server_port (int): The port number of the Ark server.

    Returns:
        None
    """
    creds = eos_config["DedicatedServerClientToken"]
    deploy_id = eos_config["DeploymentId"]

    oauth_data = {"grant_type": "client_credentials", "deployment_id": deploy_id}

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "Authorization": f"Basic {creds}",
    }

    oauth_response = requests.post(
        "https://api.epicgames.dev/auth/v1/oauth/token",
        data=oauth_data,
        headers=headers,
        timeout=10,
    )
    resp_json = oauth_response.json()
    # If there is an error or no access token
    if "errorCode" in resp_json or "access_token" not in resp_json:
        logger.debug("EOS API error while requesting oauth token: %s", resp_json)
        logger.error(
            "[red]Failed to get oauth token... Please run the command again.[/]"
        )
        return

    token = resp_json["access_token"]

    # Send query to get server(s) registered under public IP
    ip = requests.get("https://ifconfig.me/ip", timeout=10).text.strip()
    filter_criteria = {
        "criteria": [{"key": "attributes.ADDRESS_s", "op": "EQUAL", "value": ip}]
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }

    filter_response = requests.post(
        f"https://api.epicgames.dev/matchmaking/v1/{deploy_id}/filter",
        json=filter_criteria,
        headers=headers,
        timeout=10,
    )
    resp_json = filter_response.json()
    logger.debug("Server list from EOS: %s", resp_json)

    # Check for errors
    if "errorCode" in resp_json or "sessions" not in resp_json:
        logger.error(
            "[red]Failed to query server list... Please run the command again.[/]"
        )
        return

    # Extract correct server based on server port
    serv = next(
        (
            session
            for session in resp_json["sessions"]
            if f":{server_port}" in session["attributes"]["ADDRESSBOUND_s"]
        ),
        None,
    )
    if serv is None:
        logger.warning("[yellow]Server is not available in the server list.[/]")
        return

    # Extract server details
    curr_players = serv.get("totalPlayers", "")
    max_players = serv.get("settings", {}).get("maxPublicPlayers", "")
    serv_name = serv.get("attributes", {}).get("CUSTOMSERVERNAME_s", "")
    day = serv.get("attributes", {}).get("DAYTIME_s", "")
    battleye = serv.get("attributes", {}).get("SERVERUSESBATTLEYE_b", "")
    ip = serv.get("attributes", {}).get("ADDRESS_s", "")
    bind = serv.get("attributes", {}).get("ADDRESSBOUND_s", "")
    map_name = serv.get("attributes", {}).get("MAPNAME_s", "")
    major = serv.get("attributes", {}).get("BUILDID_s", "")
    minor = serv.get("attributes", {}).get("MINORBUILDID_s", "")
    pve = serv.get("attributes", {}).get("SESSIONISPVE_l", "")
    mods = serv.get("attributes", {}).get("ENABLEDMODS_s", "")

    battleye = "Yes" if battleye else "No"
    pve = "Yes" if pve else "No"
    bind_port = bind.split(":")[1]

    if mods == "":
        mods = "-"
    else:
        mod_names = [get_mod_name(mod) for mod in mods.split(",")]
        mods = ", ".join(mod_names)

    logger.info("Server Name     %s", serv_name)
    logger.info("Map             %s", map_name)
    logger.info("Day             %s", day)
    logger.info("Players         %s / %s", curr_players, max_players)
    logger.info("Mods            %s", mods)
    logger.info("BattlEye        %s", battleye)
    logger.info("PVE             %s", pve)
    logger.info("Server Version  %s.%s", major, minor)
    logger.info("Server Address  %s:%s", ip, bind_port)
    logger.info("[green]Server is up![/]")


def server_status(config: dict, full: bool = False, **kwargs: any):
    """
    Check and display the status of the Ark server.

    Args:
        config (dict): The configuration settings.
        full (bool, optional): If True, display detailed server information. Defaults to False.
        **kwargs: Additional keyword arguments.

    Returns:
        None
    """
    pid = is_server_running(config)
    if pid is None:
        logger.warning("[yellow]Server is not running.[/]")
        return

    # Load EOS credentials for full status
    if full:
        creds = get_eos_credentials(config)
    else:
        creds = None

    logger.info("Server PID      %s", pid)

    # Check server port
    server_port = get_port(config)
    l_port = get_real_server_port(config, pid)
    if l_port is None:
        logger.warning("[yellow]Server is not listening.[/]")
        return
    elif l_port != server_port:
        logger.error(
            "[red]Server listening on port %s instead of %s.[/]", l_port, server_port
        )
        return

    logger.info("Server Port     %s", server_port)

    n_players = playercount(config, fastcrash=True)
    if n_players is None:
        logger.warning("[yellow]Server is down.[/]")
        return

    if creds:
        server_full_status(config, eos_config=creds, server_port=server_port)
    else:
        logger.info("Players         %s / ?", n_players)
        logger.info("[green]Server is up![/]")
