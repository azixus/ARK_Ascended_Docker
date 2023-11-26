import math
import os
import sys
import time

import ark_rcon
from custom_logging import Logger

logger = Logger.get_logger(__name__)


def human_size_to_bytes(size):
    size_name = ("B", "K", "M", "G", "T", "P")
    num, unit = int(size[:-1]), size[-1]
    try:
        idx = size_name.index(unit)
    except ValueError as e:
        raise ValueError(f"Invalid size unit {unit}.") from e

    factor = 1024**idx
    return num * factor


def bytes_to_human_size(size):
    size_name = ("B", "KiB", "MiB", "GiB", "TiB", "PiB")
    idx = 0 if size == 0 else math.floor(math.log(size, 1024))
    v = size / 1024**idx
    return f"{v:3.2f}{size_name[idx]}"


def human_time_to_seconds(h_time):
    unit_mult = {"s": 1, "m": 60, "h": 60 * 60, "d": 60 * 60 * 24}
    num, unit = int(h_time[:-1]), h_time[-1]
    try:
        mult = unit_mult[unit]
    except KeyError as e:
        raise ValueError(f"Invalid size unit {unit}.") from e

    return num * mult


def seconds_to_human_time(seconds):
    unit_mult = [("s", 1), ("m", 60), ("h", 60 * 60), ("d", 60 * 60 * 24)]
    prev = seconds
    prev_unit = unit_mult[0][0]
    for unit, mult in unit_mult[1:]:
        curr = seconds / mult
        if curr < 1:
            break

        prev = curr
        prev_unit = unit

    return f"{prev:3.1f}{prev_unit}"


def daemonize() -> int:
    # First fork
    try:
        r, w = os.pipe()
        logger.debug("Forking process.")
        fork_pid = os.fork()
    except OSError as e:
        logger.error("Failed to fork process, err: %s", e)
        sys.exit(1)

    # As the parent process, show message, get daemon pid and return
    if fork_pid > 0:
        logger.debug("Process forked successfully into PID %s.", fork_pid)
        logger.debug("Reading daemon PID in pipe...")
        daemon_pid = int(os.fdopen(r).readline().strip())
        logger.debug("Got daemon PID %s", daemon_pid)
        return daemon_pid

    # Double fork
    os.setsid()
    try:
        logger.debug("Double-forking process.")
        fork_pid = os.fork()
    except OSError as e:
        logger.error("Failed to fork process, err: %s", e)
        sys.exit(1)

    # As the parent process, show message and return
    if fork_pid > 0:
        logger.debug("Double-forked successfully into PID %s.", fork_pid)
        logger.debug("Writing grandchild PID to pipe...")
        os.write(w, f"{fork_pid}\n".encode())
        logger.debug("Done. Exiting first forked process.")
        sys.exit(0)

    # Double forked, redirect stdin, stdout, stderr to /dev/null
    os.setsid()
    sys.stdout.flush()
    sys.stderr.flush()
    stdin = open("/dev/null", "rb")
    stdout = open("/dev/null", "a+b")
    stderr = open("/dev/null", "a+b")
    os.dup2(stdin.fileno(), sys.stdin.fileno())
    os.dup2(stdout.fileno(), sys.stdout.fileno())
    os.dup2(stderr.fileno(), sys.stderr.fileno())
    return 0


def sleep_and_warn(config: dict, warn_config: dict):
    # Convert human time to seconds
    warn_config = [
        {"message": c["message"], "time": human_time_to_seconds(c["time"])}
        for c in warn_config
    ]
    warn_config.sort(key=lambda c: c["time"], reverse=True)
    time_left = max(c["time"] for c in warn_config)

    # For each warning, sleep a specific amount based on the total time left
    for warning in warn_config:
        msg = warning["message"]
        warn_time = warning["time"]
        sleep_time = time_left - warn_time

        if sleep_time > 0:
            logger.info("Sleeping for %s.", seconds_to_human_time(sleep_time))
            time.sleep(sleep_time)
            time_left -= sleep_time

        ark_rcon.broadcast(config, msg)

    logger.info("Sleeping for %s.", seconds_to_human_time(time_left))
    time.sleep(time_left)
