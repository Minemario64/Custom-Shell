from pathlib import Path
from .__init__ import ART_PATH, TERMINAL_WIDTH, fixedWidth, fixedSize
from .artLookup import lookup
from typing import Literal

def centerStr(text: str, width: int) -> str:
    return "\n".join([f"{" "*((width - len(ln)) // 2)}{ln}{" "*((width - len(ln)) // 2)}" for ln in text.split("\n")])

class Layout:

    def __init__(self, lookupPath: str) -> None:
        if not isinstance(lookupPath, str):
            raise TypeError("lookupPath needs to be a String Object")

        self.innerLayout = None
        self.art: str = eval(f"lookup{"".join([f"['{part}']" for part in lookupPath.split("-")])}", {"__builtins__": None, "lookup": lookup})

    def addLayout(self, layout) -> None:
        if not isinstance(layout, Layout):
            raise TypeError("layout needs to be a Layout Object")
        self.innerLayout = layout

    def combineText(self, text: str) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

class HorizontalLayout(Layout):

    def __init__(self, lookupPath: str, side: Literal['left', 'right']):
        super().__init__(lookupPath)
        self.side = side

    def combineText(self, text: str, color: str | None = None) -> str:
        if self.side == 'left':
            artLns = [fixedWidth(ln, TERMINAL_WIDTH // 2) for ln in centerStr(self.art, TERMINAL_WIDTH // 2).split("\n")]
            return "\n".join([f"{f"[{color}]" if not color is None else ""}{artLn}{f"[/{color}]" if not color is None else ""}{ln}" for artLn, ln in zip(artLns, fixedSize(text.split("\n"), len(artLns), ''))])

        elif self.side == "right":
            artLns = [fixedWidth(ln[::-1], TERMINAL_WIDTH // 2)[::-1] for ln in self.art.split("\n")]
            return "\n".join([f"{ln}{artLn}" for artLn, ln in zip(artLns, fixedSize([fixedWidth(ln, TERMINAL_WIDTH // 2) for ln in text.split("\n")], len(artLns), ' '*(TERMINAL_WIDTH // 2)))])

        raise ValueError(f"{self}.side must either be 'left' or 'right'.")