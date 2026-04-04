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
from parse import CommandExecuter, Command
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
com = CommandExecuter(PATH, [], lambda path: resolvePath(curdir, path))


#===================#
# BUILT-IN COMMANDS #
#===================#\
@com.buildCommand(['exit', 'quit'])
def halt(args: list[str]) -> None:
    saveHistory(HIST_PATH)
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
        with resolvePath(curdir, filepath).open("r", encoding='utf8') as file:
            stdout.write(file.read())

    stdout.flush()

def _echoReplace(args: list[str]) -> list[str]:
    return [arg.replace("\\n", "\n").replace("\\t", "\t") for arg in args]

@com.buildCommand(["echo"])
def echo(args: list[str]) -> None:
    stdout = com.getStdout()
    stdout.write(" ".join(_echoReplace(args)) + "\n")
    stdout.flush()


#================#
#   MAIN LOGIC   #
#================#
if not CONFIG_PATH.exists():
    CONFIG_PATH.touch()

if not HIST_PATH.exists():
    HIST_PATH.touch()

loadHistory(HIST_PATH)

while True:
    command: str = input(f"\x1b[94m{USERNAME}@{HOSTNAME}\x1b[0m:\x1b[38;5;40m{shortenPath(curdir)}\x1b[95m$\x1b[0m ")
    com.run(command)
