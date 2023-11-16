import os
import psutil
import requests
import subprocess
import json
from typing import Optional
from rich import print
from ark_rcon import playercount

from config import get_port
from eos import get_eos_credentials


def is_server_running(config: dict) -> Optional[int]:
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
    # Save PID / PGID
    with open(config["ark"]["advanced"]["pid_file"], "w", encoding="utf-8") as f:
        f.write(f"{pid}")


def clear_pid(config: dict):
    # Save PID / PGID
    with open(config["ark"]["advanced"]["pid_file"], "w", encoding="utf-8") as f:
        f.write("")


def get_real_server_port(config: dict, server_pid: int) -> Optional[int]:
    # Get real port by filtering on the process name == GameThread and
    # the pgid == server_pid
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
                print("[red]Found matching PGID, but invalid name.[/red]")

    return None


def server_full_status(config: dict, eos_config: dict, server_port: int):
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
        print("[red]Failed to get oauth token... Please run the command again.[/red]")
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

    # Check for errors
    if "errorCode" in resp_json or "sessions" not in resp_json:
        print("[red]Failed to query server list... Please run the command again.[/red]")
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
        print("[red]Server is down.[/red]")
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

    print(f"Server Name     {serv_name}")
    print(f"Map             {map_name}")
    print(f"Day             {day}")
    print(f"Players         {curr_players} / {max_players}")
    print(f"Mods            {mods}")
    print(f"BattlEye        {battleye}")
    print(f"PVE             {pve}")
    print(f"Server Version  {major}.{minor}")
    print(f"Server Address  {ip}:{bind_port}")
    print("[green]Server is up.[/green]")


def server_status(config: dict, full: bool = False, **kwargs: any):
    pid = is_server_running(config)
    if pid is None:
        print("[red]Server is not running.[/red]")
        return

    # Load EOS credentials for full status
    if full:
        creds = get_eos_credentials(config)
    else:
        creds = None

    print(f"Server PID      {pid}")
    
    # Check server port
    server_port = get_port(config)
    l_port = get_real_server_port(config, pid)
    if l_port is None:
        print("[red]Server is not listening.[/red]")
        return
    elif l_port != server_port:
        print(f"[red]Server listening on port {l_port} instead of {server_port}.[/red]")
        return

    print(f"Server Port     {server_port}")
    
    n_players = playercount(config, fastcrash=True)
    if n_players is None:
        print("[red]Server is down.[/red]")
        return

    if creds:
        server_full_status(config, eos_config=creds, server_port=server_port)
    else:        
        print(f"Players         {n_players} / ?")
        print("[green]Server is up.[/green]")
