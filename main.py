#===============#
#    VERSION    #
#===============#
ver = [2, 0, 0, 'alpa (refactor)']

@lambda _: _()
def version(): return f"{".".join([str(num) for num in ver[:3]])}{"".join([f".{part}" if isinstance(part, int) else f"-{part}" for part in ver[3:]])}"


#===============#
#    IMPORTS    #
#===============#
from clicanvas.input.readline import input, maxHistory, loadHistory, saveHistory
from parse import CommandExecuter, Command, CommandToken
from utils import *
from typing import Any
from types import ModuleType
from pathlib import Path
import os, socket as ip, sys


#===============#
#   CONSTANTS   #
#===============#
CONFIG_PATH: Path = Path.home().joinpath(".csh.conf")
HIST_PATH: Path = Path.home().joinpath(".csh_history")

def resolvePath(path: Path, extended: str) -> Path:
    return (path.joinpath(extended).resolve()) if not extended.startswith("/") else Path(extended).resolve()

def shortenPath(path: Path) -> str:
    try:
        return "~" if not (relative := path.relative_to(Path.home())) else f"~/{relative}"

    except ValueError:
        return str(path)


#===============#
#    GLOBALS    #
#===============#
curdir: Path = Path.cwd()
PATH: list[str] = (os.getenv("PATH") or '').split(":" if os.name == "posix" else ";")
USERNAME: str = os.getenv("USER" if os.name == "posix" else "USERNAME", Path.home().name)
HOSTNAME: str = ip.gethostname()
com = CommandExecuter(PATH, [], lambda path: resolvePath(curdir, path), {"HOME": str(Path.home()), "USER": USERNAME, "HOSTNAME": HOSTNAME, "PATH": "|".join(PATH)}, {"~": str(Path.home()), "%": str(Path(__file__).parent)}, {})
mod = ModuleType("cshApi")
mod.__dict__['__file__'] = __file__
mod.__dict__['__package__'] = None
mod.__dict__['__name__'] = "cshApi"
mod.__dict__['getStdout'] = com.getStdout
mod.__dict__['getStdin'] = com.getStdin
sys.modules["cshApi"] = mod

#===================#
# BUILT-IN COMMANDS #
#===================#\
@com.buildCommand(['exit', 'quit'])
def halt(args: list[str]) -> None:
    exit()

com.addCommand(Command(["clear", 'cls'], lambda args: print(f"\x1b[2J\x1b[3J\x1b[H", end='', flush=True)))
@com.buildCommand(["cd", "chdir"])
def chdir(args: list[str]) -> None:
    global curdir
    if not args:
        curdir = Path.home()
        return

    if os.name == "posix":
        past = curdir
        curdir = resolvePath(curdir, args[0])
        os.chdir(curdir)
        if not curdir.is_dir():
            print(f"\x1b[91mPath '{curdir}' is a file or doesn't exist")
            curdir = past
            return

    else:
        curdir = (curdir.joinpath(args[0]).resolve())

@com.buildCommand(["ls", "listdir"])
def listdir(args: list[str]) -> None:
    restriction: int = 0 if "-a" in args else 1
    (args.pop(args.index("-a"))) if restriction == 0 else None

    target: Path = curdir if not args else resolvePath(curdir, args[0])
    if not target.is_dir():
        print(f"\x1b[91mPath '{target}' is either a file or doesn't exist.\x1b[0m")
        return

    paths = [path for path in target.iterdir() if (restriction == 0) or (restriction == 1 and (not path.name.startswith(".")))]

    print("  ".join([f"{"\x1b[94m" if path.is_dir() else ""}{path.name}{"\x1b[0m" if path.is_dir() else ""}" for path in paths]))

@com.buildCommand(["cat", 'read'])
def readFile(args: list[str]) -> None:
    stdout = com.getStdout()
    for filepath in args:
        path = resolvePath(curdir, filepath)
        if not path.exists():
            print(f"\x1b[91mFile {repr(filepath)} not found\x1b[0m")
            continue

        with path.open("r", encoding='utf8') as file:
            stdout.write(file.read())

    stdout.flush()

def _echoReplace(args: list[str]) -> list[str]:
    return [arg.replace("\\n", "\n").replace("\\t", "\t") for arg in args]

@com.buildCommand(["echo"])
def echo(args: list[str]) -> None:
    stdout = com.getStdout()
    stdout.write(" ".join(_echoReplace(args)) + "\n")
    stdout.flush()

@com.buildCommand(['var'])
def var(args: list[str]) -> None:
    color: bool = "-c" in args
    if color:
        args.remove("-c")

    if not args:
        for name, value in com.vars.items():
            print(f"{name} \x1b[91m=\x1b[0m \x1b[92m{repr(value).replace("|", "\x1b[94m | \x1b[92m") if name == "PATH" else repr(value)}\x1b[0m")

        for name, value in com.specialVars.items():
            print(f"\x1b[96m{name}\x1b[0m \x1b[91m=\x1b[0m \x1b[92m{repr(value)}\x1b[0m")

        return

    for arg in args:
        if "=" not in arg:
            print(f"\x1b[91mArgument '{arg}' is not a valid variable assignment.\x1b[0m")
            continue

        name, value = arg.split("=", 1)
        com.vars[name] = value

@com.buildCommand(['alias'])
def alias(args: list[str]):
    if not args:
        for alias, tok in com.aliases.items():
            print(f"{alias}={repr(" & ".join([" ".join([f'"{arg}"' if ' ' in arg else arg for arg in ([command.exe] + command.args)]) for command in tok]))}")

        return

    com.aliases[args[0]] = com.parser(com.lexer(args[1].strip()))

#================#
#   MAIN LOGIC   #
#================#
if __name__ == "__main__":
    if not CONFIG_PATH.exists():
        CONFIG_PATH.touch()
        exportToJSON(
            {
                "PATH": {
                    "includeSystemPath": True,
                    "paths": [
                        "%/bin"
                    ]
                },
                "aliases": {
                    "la": "ls -a",
                },
                "vars": {
                    "CODE": "~/code"
                }
            },
            CONFIG_PATH
        )

    json = importFromJSON(CONFIG_PATH)
    if not ((pathObj := json.get("PATH")) is None):
        com.PATH = [Path(com._replaceVars(path)) for path in pathObj.get("paths", [])] + ([Path(path) for path in PATH] if pathObj.get("includeSystemPath", True) else [])
        com.vars['PATH'] = "|".join([str(path) for path in com.PATH])

    if not ((aliasesObj := json.get("aliases")) is None):
        com.aliases |= {name: com.parser(com.lexer(val.strip())) for name, val in aliasesObj.items()}

    if not ((varsObj := json.get("vars")) is None):
        com.vars |= {name: com._replaceVars(path) for name, path in varsObj.items()}

    if not HIST_PATH.exists():
        HIST_PATH.touch()

    loadHistory(HIST_PATH)

    while True:
        command: str = input(f"\x1b[94m{USERNAME}@{HOSTNAME}\x1b[0m:\x1b[38;5;40m{shortenPath(curdir)}\x1b[95m$\x1b[0m ")
        com.run(command)
