from pathlib import Path
from functools import cache

@cache
def generateLookup() -> dict:
    from .__init__ import ART_PATH
    result = {}
    for path in ART_PATH.iterdir():
        if path.is_dir():
            if path.name == "__pycache__":
                continue

            result[path.name] = {}
            for file in [p for p in path.iterdir() if p.is_file()]:
                result[path.name][file.stem.removeprefix(f"{path.name}-")] = file.read_bytes().decode("ascii")

    return result

lookup = generateLookup()