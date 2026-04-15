import os, re
import pathlib
from typing import Callable, Any
import __future__

class Path(pathlib.Path):
    def absolute(self) -> Path:
        """Returns the absolute path of this path, without resolving symlinks."""
        return Path(absolutePath(str(self)))

    def shorten(self, vars: dict[str, str]) -> str:
        """Returns a shortened version of this path, replacing any matching prefixes with the corresponding keys in vars."""
        return shortenPath(str(self), vars)

def sortDict(d: dict, key: Callable[[Any], int] | None = None, **kwargs) -> dict: return {k: d[k] for k in sorted(d.keys(), key=key, **kwargs)}

def shortenPath(path: str, vars: dict[str, str]) -> str:
    varPaths: dict[str, str] = sortDict(vars, key=lambda var: len(vars[var]), reverse=True)
    for var, varPath in varPaths.items():
        if path.startswith(varPath):
            return var + path[len(varPath):]

    return path

def absolutePath(path: str) -> str:
    if os.name == "nt":
        path = path.replace("/", "\\")
        if not re.match(r"^[a-zA-Z]:\\.*", path):
            path = "\\".join([os.getcwd(), path.lstrip("\\ ")])

        paths: list[str] = []
        for part in path.split("\\"):
            if part == ".":
                continue

            elif part == "..":
                paths.pop()

            else:
                paths.append(part)

        path = "\\".join(paths)
        return path

    else:
        raise NotImplementedError("TODO: Implement absolutePath for linux")

if __name__ == "__main__":
    print(os.getcwd())
    while True:
        try:
            print(shortenPath(str(Path(input(">>> ")).absolute()), vars={"~": str(Path.home()), "%": str(Path(__file__).parent.parent)}))

        except NotImplementedError:
            pass

        except KeyboardInterrupt:
            print()
            break