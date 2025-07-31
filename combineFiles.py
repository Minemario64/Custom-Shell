from pathlib import Path
import re
from enum import Enum
from typing import Iterator
from dataclasses import dataclass

class ImportType(Enum):
    NORMAL = 0
    SELECTION = 1
    PACKAGE_ALL = 2
    NORMAL_RENAME = 3

@dataclass
class Importer:
    indent: int
    type: ImportType
    path: Path | None
    selection: str | Iterator[str]

def is_importer(ln: str) -> bool:
    importAllStatement = re.compile(r"^( *)?from ([a-zA-Z0-9.]*) import \*$")
    packageAllStatement = re.compile(r'^__all__\s+=\s+\["[A-Za-z]+", "[A-Za-z]+"\]$')
    importSelectionStatement = re.compile(r"^( *)?from ([a-zA-Z0-9.]*) import ([a-zA-Z0-9_!]*(, )?)*")
    importStatement = re.compile(r"^( *)?import ([a-zA-Z0-9.]*)( as [a-zA-Z0-9])?")
    return False