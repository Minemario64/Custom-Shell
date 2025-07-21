from pathlib import Path
import shutil
from typing import Any
import threading as thr
TERMINAL_WIDTH = shutil.get_terminal_size().columns

ART_PATH: Path = Path(__file__).parent

def fixedWidth(text: str, width: int, fill: str = " ") -> str:
    if len(text) > width:
        return text[0:width]

    return text + fill*(width - len(text))

def fixedSize(item: list, length: int, fill: Any):
    if len(item) > length:
        return item[0:length]

    while len(item) < length:
        item.append(fill)

    return item

__all__ = ["display"]

from .display import *