import os
import pexpect
from rich import print

def install_update_game(
    steamcmd_path: str, game_path: str, appid: str, validate: bool = False
):
    # Check steamcmd command available
    steamcmd_sh = os.path.join(steamcmd_path, "steamcmd.sh")
    if not os.access(steamcmd_sh, os.X_OK):
        print(f"[red]Steamcmd {steamcmd_path} not found / not executable[/red]")
        raise ValueError("steamcmd.sh not found or not executable")

    # Attempt to create folder
    try:
        os.makedirs(game_path, exist_ok=True)
    except PermissionError:
        print(f"[red]Failed to create {game_path} folder, permission denied.[/red]")
        raise

    # Ensure folder is writeable
    if os.access(game_path, os.W_OK):
        print(f"[green]Folder {game_path} is writeable[/green]")
    else:
        print(f"[red]Folder {game_path} is not writeable[/red]")
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
    print(f"$ {cmdline}")
    while True:
        try:
            steamcmd.expect("\r\n")
            line = steamcmd.before.decode("utf-8")
            print(f">>> {line}")
        except KeyboardInterrupt:
            steamcmd.close(force=True)
        except pexpect.EOF:
            break

    res = steamcmd.wait()

    if res == 0:
        print(f"[green]App {appid} successfully installed![/green]")
    else:
        print(f"[red]Failed to install app {appid}. Error: {res}[/red]")
        raise RuntimeError("Failed to install game")
