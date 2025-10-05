from pathlib import Path

EMPTY: int = 0
PATH_NON_LAST: int = 1
PATH_LAST: int = 3

treeChars: dict[int, str] = {EMPTY: "│ ",
                             PATH_NON_LAST: "├╴",
                             PATH_LAST: "╰╴"}

def generateDirTree(dir: Path, rootName: str = "/",*, depth: int = 0) -> str:
    if not dir.is_dir():
        raise ValueError("dir is a file or does not exist")

    result: str = f"{rootName}\n" if depth == 0 else ""

    pathLength: int = len(list(dir.iterdir())) - 1
    for i, path in enumerate(dir.iterdir()):
        result += f"{treeChars[EMPTY]*depth}{treeChars[PATH_NON_LAST] if i < pathLength else treeChars[PATH_LAST]}{path.name}\n"
        if path.is_dir():
            result += generateDirTree(path, depth=depth + 1)

    return result.rstrip("\n") if depth == 0 else result

if __name__ == "__main__":
    print(generateDirTree(Path()))