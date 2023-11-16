import socket
from typing import Optional
from rcon.source import Client

from config import get_rcon_port, get_admin_password

def send(config: dict, command: str, address: str = '127.0.0.1', fastcrash: bool = False):
    port = get_rcon_port(config)
    if port == -1:
        raise ValueError("RCON is disabled.")
    
    # TCP port check with low timeout, unlike rcon
    if fastcrash:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        try:
            s.connect((address, port))
        except TimeoutError:
            # RCON unreachable, todo: log
            raise
        finally:
            s.close()

    admin_pass = get_admin_password(config)
    client = Client(address, port, passwd=admin_pass)
    client.timeout = 3
    client.connect(login=True)
    response = client.run(command)
    client.close()

    return response

def saveworld(config: dict, address: str = '127.0.0.1', fastcrash: bool = False) -> bool:
    try:
        res = send(config, "SaveWorld", address=address, fastcrash=fastcrash)
        return 'World Saved' in res
    except TimeoutError:
        return False

def listplayers(config: dict, address: str = '127.0.0.1', fastcrash: bool = False) -> Optional[str]:
    try:
        res = send(config, "ListPlayers", address=address, fastcrash=fastcrash)
        return res
    except TimeoutError:
        return None

def playercount(config: dict, address: str = '127.0.0.1', fastcrash: bool = False) -> Optional[str]:
    res = listplayers(config, address=address, fastcrash=fastcrash)
    if not res:
        return None
    
    if 'No Players' in res:
        return 0
    else:
        return res.count('\n')

def doexit(config: dict, address: str = '127.0.0.1', fastcrash: bool = False):
    try:
        send(config, "DoExit", address=address, fastcrash=fastcrash)
        return True
    except TimeoutError:
        return False
