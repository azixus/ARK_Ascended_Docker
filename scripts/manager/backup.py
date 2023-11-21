import math
import os
import re
import tarfile
import time
from datetime import datetime
from glob import glob
from ark_rcon import saveworld
from utils import Logger
from status import is_server_running

logger = Logger.get_logger(__name__)


def human_size_to_bytes(size):
    size_name = ("B", "K", "M", "G", "T", "P")
    num, unit = int(size[:-1]), size[-1]
    idx = size_name.index(unit)
    factor = 1024**idx
    return num * factor


def bytes_to_human_size(size):
    size_name = ("B", "KiB", "MiB", "GiB", "TiB", "PiB")
    idx = 0 if size == 0 else math.floor(math.log(size, 1024))
    v = size / 1024**idx
    return f"{v:3.2f}{size_name[idx]}"


def get_backup_size(path: str):
    return os.path.getsize(path)


def get_total_backup_size(path: str, extension: str = "tar.gz"):
    return sum(
        get_backup_size(f)
        for f in glob(os.path.join(path, f"*.{extension}"))
        if os.path.isfile(f)
    )


def get_files(path: str, extension: str = "tar.gz"):
    return [f for f in glob(os.path.join(path, f"*.{extension}")) if os.path.isfile(f)]


def get_backup_timestamp(path: str) -> str:
    timestamp_regex = r"^backup_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\..+$"
    backup_name = os.path.basename(path)
    if res := re.search(timestamp_regex, backup_name):
        timestamp = res.group(1)
        return datetime.strptime(timestamp, "%Y-%m-%d_%H-%M-%S")
    else:
        return None


def generate_backup_name() -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"backup_{timestamp}.tar.gz"


def delete_bak(path: str) -> bool:
    try:
        os.remove(path)
        logger.debug("Backup %s successfully deleted.[/]", path)
        return True
    except OSError as e:
        logger.error("[red]Failed to delete backup %s. Err: %s[/]", path, e)
        return False


def delete_baks(candidates_bak: list) -> bool:
    # Free up at least as much as the last backup
    to_free = get_backup_size(candidates_bak[-1])
    freed = 0
    to_delete = []
    for bak in candidates_bak:
        to_delete.append(bak)
        freed += get_backup_size(bak)
        if freed > to_free:
            break

    if freed <= to_free:
        logger.error("[red]Cannot free enough space to save backup.[/]")
        return False

    # Delete baks
    for bak in to_delete:
        if not delete_bak(bak):
            return False

    return True


def backup(
    config: dict,
    compression_level: int = 6,
    **kwargs: any,
):
    backup_dir = config["ark"]["backup"]["target_dir"]
    if not os.access(backup_dir, os.W_OK | os.X_OK):
        logger.error(
            "[red]Backup folder %s not found or bad permissions.[/]", backup_dir
        )
        return

    max_bak_size = human_size_to_bytes(config["ark"]["backup"]["max_backup_size"])
    max_bak_files = config["ark"]["backup"]["max_backup_number"]

    # Get and sort backup files by timestamp
    current_baks = get_files(backup_dir)
    current_baks.sort(key=get_backup_timestamp)
    nb_baks = len(current_baks)

    # Get total backup size
    current_size = get_total_backup_size(backup_dir)

    logger.info(
        "You currenty have %s/%s backups taking %s/%s of disk space.",
        nb_baks,
        "∞" if max_bak_files == 0 else max_bak_files,
        bytes_to_human_size(current_size),
        "∞" if max_bak_size == 0 else bytes_to_human_size(max_bak_size),
    )

    if max_bak_size != 0 and current_size >= max_bak_size:
        logger.info("Deleting backups to free enough space.")
        if not delete_baks(current_baks):
            return
    elif max_bak_files != 0 and nb_baks >= max_bak_files:
        logger.info("Deleting the oldest backup(s) since all backup slots are filled.")
        for i in range(nb_baks - max_bak_files + 1):
            oldest_bak = current_baks[i]
            # If delete backup failed, return now
            if not delete_bak(oldest_bak):
                return

    # If server is up, try to save world
    pid = is_server_running(config)
    if pid:
        # Try to save the world, still proceed with the backup in any case
        if saveworld(config):
            # Add sleep to ensure the files are written to disk
            time.sleep(0.2)
        else:
            logger.warning("[red]Failed to save world before starting backup.[/]")

    # Find the files to backup
    backup_files = config["ark"]["backup"]["files"]
    server_folder = config["ark"]["install_folder"]
    files_to_backup = []
    for folder_config in backup_files:
        folder = os.path.join(server_folder, folder_config["folder"])
        files_regex = folder_config["files_regex"]
        files = get_files(folder, extension="*")

        # Combine each individual regex
        combined_regex = re.compile("(" + ")|(".join(files_regex) + ")")
        for file in files:
            if combined_regex.match(os.path.basename(file)):
                files_to_backup.append(file)

    logger.debug(
        "Found %s files to backup: %s", len(files_to_backup), ", ".join(files_to_backup)
    )

    # Do the backup
    backup_name = generate_backup_name()
    backup_path = os.path.join(backup_dir, backup_name)
    logger.info("Backup in progress...")
    with tarfile.open(backup_path, "w:gz", compresslevel=compression_level) as tar:
        for file in files_to_backup:
            logger.info("\t- Copying %s", os.path.basename(file))
            tar.add(file, arcname=os.path.relpath(file, server_folder))

        logger.debug("Trying to save backup to %s", backup_path)
    logger.info("[green]Backup saved to %s[/]", backup_path)


def restore(
    config: dict,
    path: str,
    latest: int,
    **kwargs: any,
):
    pid = is_server_running(config)
    if pid:
        logger.warning("[yellow]Cannot restore backup while server is running.[/]")
        return

    # Check that the path exists
    if path:
        if not os.access(path, os.R_OK):
            logger.error("[red]Backup file %s not found or bad permissions.[/]", path)
            return
    # Get the latest backup file / ask for the user to pick
    else:
        backup_dir = config["ark"]["backup"]["target_dir"]
        if not os.access(backup_dir, os.R_OK):
            logger.error(
                "[red]Backup folder %s not found or bad permissions.[/]", backup_dir
            )
            return

        # Get and sort backup files by timestamp
        current_baks = get_files(backup_dir)
        current_baks.sort(key=get_backup_timestamp)
        nb_baks = len(current_baks)

        if len(current_baks) == 0:
            logger.error("[red]Could not find any backup in %s[/]", backup_dir)
            return

        # Pick the latest backup or ask user
        if latest:
            path = current_baks[-1]
        else:
            for i, file in enumerate(current_baks):
                logger.info("%2d - - - - - File: %s", i + 1, file)

            res = input("Please input the number of the archive you want to restore: ")
            logger.debug(
                "Please input the number of the archive you want to restore: %s", res
            )
            try:
                choice = int(res) - 1
            except ValueError:
                logger.error("[red]Invalid number %s[/]", res)
                return

            if choice < 0 or choice >= nb_baks:
                logger.error("[red]Invalid backup choice %s.[/]", choice)
                return

            path = current_baks[choice]

    # Path should now be valid, extract backup into server folder
    server_folder = config["ark"]["install_folder"]
    with tarfile.open(path, "r:gz") as tar:
        tar.extractall(path=server_folder)

    logger.info("[green]%s successfully restored.[/]", os.path.basename(path))
