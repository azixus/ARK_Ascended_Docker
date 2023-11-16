import os
import pexpect
from utils import Logger

logger = Logger.get_logger(__name__)


def install_update_game(
    steamcmd_path: str, game_path: str, appid: str, validate: bool = False
):
    """
    Install or update a game using SteamCMD.

    Args:
        steamcmd_path (str): The path to the SteamCMD executable.
        game_path (str): The path where the game will be installed or updated.
        appid (str): The Steam AppID of the game.
        validate (bool, optional): If True, validate files after installation. Defaults to False.

    Raises:
        ValueError: If steamcmd.sh is not found or not executable.
        PermissionError: If permission is denied while creating the game folder.
        ValueError: If the game folder is not writeable.
        RuntimeError: If the installation process fails.

    Returns:
        None
    """
    # Check steamcmd command available
    steamcmd_sh = os.path.join(steamcmd_path, "steamcmd.sh")
    if not os.access(steamcmd_sh, os.X_OK):
        logger.error("[red]Steamcmd %s not found / not executable[/]", steamcmd_path)
        raise ValueError("steamcmd.sh not found or not executable")

    # Attempt to create folder
    try:
        os.makedirs(game_path, exist_ok=True)
    except PermissionError:
        logger.error(
            "[red]Failed to create %s folder, permission denied.[/]", game_path
        )
        raise

    # Ensure folder is writeable
    if os.access(game_path, os.W_OK):
        logger.info("[green]Folder %s is writeable[/]", game_path)
    else:
        logger.error("[red]Folder %s is not writeable[/]", game_path)
        raise ValueError(f"Could not write into {game_path} directory")

    # Install / update steamcmd
    validate_str = "validate" if validate else ""
    cmdline = " ".join(
        [
            steamcmd_sh,
            f"+force_install_dir {game_path}",
            "+login anonymous",
            f"+app_update {appid}",
            f"{validate_str}",
            "+quit",
        ]
    )

    steamcmd = pexpect.spawn(cmdline)
    logger.info("$ %s", cmdline)
    while True:
        try:
            steamcmd.expect("\r\n")
            line = steamcmd.before.decode("utf-8")
            logger.info(">>> %s", line)
        except KeyboardInterrupt:
            steamcmd.close(force=True)
        except pexpect.EOF:
            break

    res = steamcmd.wait()

    if res == 0:
        logger.info("[green]App %s successfully installed![/]", appid)
    else:
        logger.error("[red]Failed to install app %s. Error: %s[/]", appid, res)
        raise RuntimeError("Failed to install game")
