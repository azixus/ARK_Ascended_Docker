from enum import Enum
import time

import ark_rcon
from custom_logging import Logger
from utils import human_time_to_seconds, seconds_to_human_time

logger = Logger.get_logger(__name__)


class ScheduledAction(Enum):
    NONE = 1
    RESTARTING = 10
    STOPPING = 20
    UPDATING = 30


def get_scheduled_action(config: dict) -> ScheduledAction:
    with open(config["ark"]["advanced"]["schedule_file"], "r", encoding="utf-8") as f:
        action_str = f.read()
        try:
            action = ScheduledAction(int(action_str))
            logger.debug("Current scheduled action: %s (%s)", action.name, action.value)
            return action
        except ValueError:
            logger.debug(
                "Cannot convert scheduled action '%s'. Assuming NONE.", action_str
            )
            return ScheduledAction.NONE


def set_scheduled_action(config: dict, action: ScheduledAction):
    logger.debug("Setting scheduled action to %s (%s)", action.name, action.value)

    with open(config["ark"]["advanced"]["schedule_file"], "w", encoding="utf-8") as f:
        f.write(f"{action.value}")


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
