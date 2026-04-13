from pathlib import Path
from lib.argparse import getListArgs

EMPTY: int = 0
PATH_NON_LAST: int = 1
PATH_LAST: int = 3

treeChars: dict[int, str] = {
    EMPTY: "│ ",
    PATH_NON_LAST: "├╴",
    PATH_LAST: "╰╴"
}

def generateDirTree(dir: Path, rootName: str = "/",*, depth: int = 0, ignore: list[str] | None = None) -> str:
    if not dir.is_dir():
        raise ValueError("dir is a file or does not exist")

    if ignore is not None and dir.name in ignore:
        return ""

    result: str = f"{rootName}\n" if depth == 0 else ""

    pathLength: int = len([path for path in dir.iterdir() if not path.name in (ignore if ignore is not None else [])]) - 1
    for i, path in enumerate([path for path in dir.iterdir() if not path.name in (ignore if ignore is not None else [])]):
        result += f"{treeChars[EMPTY]*depth}{treeChars[PATH_NON_LAST] if i < pathLength else treeChars[PATH_LAST]}{path.name}\n"
        if path.is_dir():
            result += generateDirTree(path, depth=depth + 1, ignore=ignore)

    return result.rstrip("\n") if depth == 0 else result

if __name__ == "__main__":
    import sys
    kwargs = getListArgs({"ignore": ["-i", "--ignore"]}, [], sys.argv[1:])
    print(generateDirTree(Path.cwd(), Path.cwd().name, ignore=kwargs["ignore"]))