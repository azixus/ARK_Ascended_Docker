import socket
from typing import Optional
from rcon.source import Client

from config import get_rcon_port, get_admin_password
from utils import Logger

logger = Logger.get_logger(__name__)


def send(
    config: dict, command: str, address: str = "127.0.0.1", fastcrash: bool = False
):
    port = get_rcon_port(config)
    if port is None:
        raise ValueError("RCON is disabled.")

    # TCP port check with low timeout, unlike rcon
    if fastcrash:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        try:
            s.connect((address, port))
        except TimeoutError:
            # RCON unreachable
            logger.error(
                "[red]Could not connect to RCON port on %s:%s[/]", address, port
            )
            raise
        finally:
            s.close()

    admin_pass = get_admin_password(config)
    client = Client(address, port, passwd=admin_pass)
    client.timeout = 3
    client.connect(login=True)

    logger.debug("Sending RCON command '%s' to %s:%s", command, address, port)
    response = client.run(command)
    client.close()

    return response


def saveworld(
    config: dict, address: str = "127.0.0.1", fastcrash: bool = False
) -> bool:
    """
    Save the world by sending an RCON request to the server.

    Args:
        config (dict): The configuration settings.
        address (str, optional): The IP address to send the request. Defaults to '127.0.0.1'.
        fastcrash (bool, optional): If True, crash quickly if the port is down. Defaults to False.

    Returns:
        bool: True if the world is saved successfully, False otherwise.
    """
    try:
        res = send(config, "SaveWorld", address=address, fastcrash=fastcrash)
        return "World Saved" in res
    except TimeoutError:
        return False


def listplayers(
    config: dict, address: str = "127.0.0.1", fastcrash: bool = False
) -> Optional[str]:
    """
    Get a list of players by sending an RCON request to the server.

    Args:
        config (dict): The configuration settings.
        address (str, optional): The IP address to send the request. Defaults to '127.0.0.1'.
        fastcrash (bool, optional): If True, crash quickly if the port is down. Defaults to False.

    Returns:
        Optional[str]: A string containing the list of players, or None if the request times out.
    """
    try:
        res = send(config, "ListPlayers", address=address, fastcrash=fastcrash)
        return res
    except TimeoutError:
        return None


def playercount(
    config: dict, address: str = "127.0.0.1", fastcrash: bool = False
) -> Optional[str]:
    """
    Get the count of players by sending an RCON request to the server.

    Args:
        config (dict): The configuration settings.
        address (str, optional): The IP address to send the request. Defaults to '127.0.0.1'.
        fastcrash (bool, optional): If True, crash quickly if the port is down. Defaults to False.

    Returns:
        Optional[int]: The number of players if available, or None if the request times out or there are no players.
    """
    res = listplayers(config, address=address, fastcrash=fastcrash)
    if not res:
        return None

    if "No Players" in res:
        return 0
    else:
        return res.count("\n")


def doexit(config: dict, address: str = "127.0.0.1", fastcrash: bool = False):
    """
    Perform an exit action by sending an RCON request to the server.

    Args:
        config (dict): The configuration settings.
        address (str, optional): The IP address to send the request. Defaults to '127.0.0.1'.
        fastcrash (bool, optional): If True, crash quickly if the port is down. Defaults to False.

    Returns:
        bool: True if the exit action is successful, False otherwise.
    """
    try:
        send(config, "DoExit", address=address, fastcrash=fastcrash)
        return True
    except TimeoutError:
        return False
