from enum import Enum
import datetime
import os
import time
import psutil

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
import tomli_w

import ark_rcon
from custom_logging import Logger
from utils import human_time_to_seconds, seconds_to_human_time


class ScheduledAction(Enum):
    NONE = 1
    RESTARTING = 10
    STOPPING = 20
    UPDATING = 30


logger = Logger.get_logger(__name__)

default_sche_config = {
    "action": ScheduledAction.NONE,
    "pid": 0,
    "expected_time": datetime.datetime(1970, 1, 1, 0, 0, 1),
}


def get_scheduled_config(config: dict) -> dict:
    try:
        with open(config["ark"]["advanced"]["schedule_file"], "r+b") as f:
            sche_config = tomllib.load(f)
            sche_config["action"] = ScheduledAction(sche_config["action"])
            return sche_config
    except (FileNotFoundError, tomllib.TOMLDecodeError, KeyError):
        return default_sche_config


def set_scheduled_config(
    config: dict, action: ScheduledAction, pid: int, expected_time: datetime.datetime
):
    logger.debug("Setting scheduled action to %s (%s)", action.name, action.value)

    sche_config = {
        "action": action.value,
        "pid": pid,
        "expected_time": expected_time,
    }

    with open(config["ark"]["advanced"]["schedule_file"], "wb") as f:
        tomli_w.dump(sche_config, f)


def clear_scheduled_config(config: dict):
    with open(config["ark"]["advanced"]["schedule_file"], "wb") as f:
        f.write(b"")


def get_scheduled_action(config: dict) -> ScheduledAction:
    sche_config = get_scheduled_config(config)
    # Clear config and return NONE if pid not found
    if not psutil.pid_exists(sche_config["pid"]):
        clear_scheduled_config(config)
        return ScheduledAction.NONE

    return sche_config["action"]


def sleep_and_warn(config: dict, warn_config: dict, action: ScheduledAction):
    # Convert human time to seconds
    warn_config = [
        {"message": c["message"], "time": human_time_to_seconds(c["time"])}
        for c in warn_config
    ]
    warn_config.sort(key=lambda c: c["time"], reverse=True)
    secs_left = max(c["time"] for c in warn_config)

    exp_time = datetime.datetime.now() + datetime.timedelta(seconds=secs_left)
    set_scheduled_config(config, action, os.getpid(), exp_time)

    # For each warning, sleep a specific amount based on the total time left
    for warning in warn_config:
        msg = warning["message"]
        warn_time = warning["time"]
        sleep_time = secs_left - warn_time

        if sleep_time > 0:
            logger.info("Sleeping for %s.", seconds_to_human_time(sleep_time))
            time.sleep(sleep_time)
            secs_left -= sleep_time

        ark_rcon.broadcast(config, msg)

    logger.info("Sleeping for %s.", seconds_to_human_time(secs_left))
    time.sleep(secs_left)

    # Remove scheduled config
    logger.debug("Clearing scheduled config")
    clear_scheduled_config(config)
