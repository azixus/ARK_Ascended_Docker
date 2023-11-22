import logging
import re
import math
from rich.logging import RichHandler


class MarkupFormatter(logging.Formatter):
    """Formatter that removes console markup"""

    @staticmethod
    def _filter(s):
        return re.sub(r"\[.*?\]", r"", s)

    def format(self, record):
        original = super().format(record)
        return self._filter(original)


class Logger:
    _log_file = "./manager.log"

    @classmethod
    def get_logger(cls, name: str):
        """
        Logger for console and file.
        """
        logger = logging.getLogger(name)
        file_formatter = MarkupFormatter("%(asctime)s | %(levelname)s: %(message)s")
        rich_formatter = logging.Formatter("%(message)s")
        logger.setLevel(logging.DEBUG)

        console_handler = RichHandler(show_time=False, show_level=False, markup=True)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(rich_formatter)
        logger.addHandler(console_handler)

        file_handler = logging.FileHandler(filename=cls._log_file)
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

        return logger


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
