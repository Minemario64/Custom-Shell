#===============#
#    VERSION    #
#===============#
ver = [2, 0, 0, 'alpa (refactor)']

@lambda _: _()
def version() -> str: return f"{".".join([str(num) for num in ver[:3]])}{"".join([f".{part}" if isinstance(part, int) else f"-{part}" for part in ver[3:]])}"


#===============#
#    IMPORTS    #
#===============#
from clicanvas.input.readline import input, maxHistory, loadHistory, saveHistory
from parse import CommandExecuter, Command, KillSwitch
from utils import importFromJSON, exportToJSON, error, warn
from typing import Any, Generator
from types import ModuleType
import os, socket as ip, sys
from lib import *
from lib.path import Path

#===============#
#   CONSTANTS   #
#===============#
CONFIG_PATH: Path = Path.home().joinpath(".csh.conf")
HIST_PATH: Path = Path.home().joinpath(".csh_history")

def resolvePath(path: Path, extended: str) -> Path:
    return (path.joinpath(extended).resolve()) if not extended.startswith("/") else Path(extended).resolve()


#===============#
#    GLOBALS    #
#===============#
pastcwd: Path = Path.cwd()
curdir: Path = Path.cwd()
PATH: list[str] = (os.getenv("PATH") or '').split(":" if os.name == "posix" else ";")
USERNAME: str = os.getenv("USER" if os.name == "posix" else "USERNAME", Path.home().name)
HOSTNAME: str = ip.gethostname()
com = CommandExecuter(PATH, [], lambda path: resolvePath(curdir, path), {"HOME": str(Path.home()), "USER": USERNAME, "HOSTNAME": HOSTNAME, "PATH": "|".join(PATH), "VERSION": version, "OS": "linux" if sys.platform == "linux" else "windows"}, {"~": str(Path.home()), "%": str(Path(__file__).parent)}, {}) # pyright: ignore[reportArgumentType] # Why does pyright think version is not a string? It's literally defined as a string right above >:(
mod = ModuleType("cshApi")
mod.__dict__['__file__'] = __file__
mod.__dict__['__package__'] = None
mod.__dict__['__name__'] = "cshApi"
mod.__dict__['getStdout'] = com.getStdout
mod.__dict__['getStdin'] = com.getStdin
mod.__dict__['VERSION'] = version
sys.modules["cshApi"] = mod

                                            # TEMPLATE: ((BG, FG), (BG, FG)) # int in 256 color palette
def prompt(text: tuple[str, str], colors: tuple[tuple[int, int], tuple[int, int], tuple[int, int]]) -> str:
    from shutil import get_terminal_size
    dots: str = "∙ "*((get_terminal_size().columns - ((10 - (3 if text[1] == "" else 0)) + sum([len(s) for s in text]) + len(f"{USERNAME} @ {HOSTNAME}") + 5)) // 2)
    return f"\x1b[1m\x1b[38;5;{colors[0][0]}m╭─\x1b[22m\x1b[38;5;{colors[0][1]}m\x1b[48;5;{colors[0][0]}m {text[0]} \x1b[0m\x1b[38;5;{colors[0][0]}m\x1b[48;5;{colors[1][0]}m{f"\x1b[38;5;{colors[1][1]}m  {text[1]} " if text[1] != "" else ''}\x1b[0m\x1b[38;5;{colors[1][0]}m\x1b[0m\x1b[90m {dots}\x1b[38;5;{colors[2][0]}m\x1b[48;5;{colors[2][0]}m\x1b[38;5;{colors[2][1]}m {f"{USERNAME} @ {HOSTNAME}"} \x1b[38;5;{colors[2][0]}m\x1b[49m\n\x1b[38;5;{colors[0][0]}m╰\x1b[95m$\x1b[0m "


#===================#
# BUILT-IN COMMANDS #
#===================#
def _echoReplace(args: list[str]) -> list[str]:
    return [arg.replace("\\n", "\n").replace("\\t", "\t") for arg in args]

def integrateBuiltinCommands(commandExecuter: CommandExecuter) -> None:
    """Integrates builtin commands into a command executer, and mutates it

    This is for kind of but not really sandboxing the commands so .csh files don't mess with the user's current shell instance.

    Args:
        commandExecuter (CommandExecuter): the command executer to integrate the commands into
    """
    @commandExecuter.buildCommand(['exit', 'quit'])
    def halt(args: list[str]) -> None | KillSwitch:
        exit() if commandExecuter is com else KillSwitch()

    commandExecuter.addCommand(Command(["clear", 'cls'], lambda args: print(f"\x1b[2J\x1b[3J\x1b[H", end='', flush=True)))
    @commandExecuter.buildCommand(["cd", "chdir"])
    def chdir(args: list[str]) -> int | None:
        global curdir
        global pastcwd
        if not args:
            curdir = Path.home()
            return

        if args[0] == "-":
            curdir = pastcwd
            os.chdir(curdir)
            return

        elif args[0] == "\\-":
            args[0] = "-"

        pastcwd = curdir
        curdir = curdir.joinpath(args[0]).absolute()
        if not curdir.is_dir():
            error(f"Path '{curdir}' is a file or doesn't exist.")
            return 1

        os.chdir(curdir)

    @commandExecuter.buildCommand(["ls", "listdir"])
    def listdir(args: list[str]) -> int | None:
        flags = getFlags({"all": ["-a", "--all"]}, args)

        target: Path = curdir if not args else resolvePath(curdir, args[0])
        if not target.is_dir():
            error(f"Path '{target}' is either a file or doesn't exist.")
            return 1

        def is_hidden(path: Path) -> bool:
            if path.name.startswith("."):
                return True

            if os.name == "nt":
                import ctypes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
                return attrs != -1 and (attrs & FILE_ATTRIBUTE_HIDDEN)

            return False

        def dirContents(path: Path) -> Generator[Path, None, None]:
            for p in path.iterdir():
                if p.is_dir():
                    try:
                        [file for file in p.iterdir()]

                    except PermissionError:
                        continue

                if p.is_file() and os.name == "nt":
                    if path == Path.home():
                        if p.name.lower() in ["ntuser.dat", "ntuser.man"]:
                            yield p
                            continue

                        elif p.name.lower().startswith("ntuser"):
                            continue

                yield p

        paths = [path for path in dirContents(target) if (flags["all"] or (not flags['all'] and (not is_hidden(path))))]

        print("  ".join([f"{"\x1b[94m" if path.is_dir() else ""}{path.name}{"\x1b[0m" if path.is_dir() else ""}" for path in paths]))

    @commandExecuter.buildCommand(["cat", 'read'])
    def readFile(args: list[str]) -> int | None:
        stdout = commandExecuter.getStdout()
        for filepath in args:
            path = resolvePath(curdir, filepath)
            if not path.exists():
                error(f"File {repr(filepath)} not found.")
                continue

            with path.open("r", encoding='utf8') as file:
                stdout.write(file.read())

        stdout.flush()

    @commandExecuter.buildCommand(["echo", 'print'])
    def echo(args: list[str]) -> int | None:
        stdout = commandExecuter.getStdout()
        flags = getFlags({"escape": ["-e", "--escape"]}, args)
        base = " ".join(_echoReplace(args)) + "\n"
        stdout.write(base.replace("\\e", "\x1b") if flags["escape"] else base)
        stdout.flush()

    @commandExecuter.buildCommand(['touch', 'mkfile'])
    def touch(args: list[str]) -> int | None:
        if not args:
            error("No file name provided.")
            return 1

        for arg in args:
            path = resolvePath(curdir, arg)
            if not path.parent.exists():
                warn(f"Directory '{path.parent}' does not exist for file '{arg}'. Skipping.")
                continue

            if not path.exists():
                path.touch()

    @commandExecuter.buildCommand(['mkdir'])
    def mkdir(args: list[str]) -> int | None:
        if not args:
            error("No directory name provided.")
            return 1

        FLAGS = {"parents": True if any([arg in ("-p", "--parents") for arg in args]) else False}
        for flag in ("-p", "--parents"):
            if flag in args:
                args.remove(flag)

        path = resolvePath(curdir, args[0])
        path.mkdir(parents=FLAGS["parents"], exist_ok=True)

    @commandExecuter.buildCommand(['rm', 'del', 'remove'])
    def remove(args: list[str]) -> int | None:
        if not args:
            error("No file or directory name provided. Usage: rm <file(s) or directory(s)>")
            return 1

        flags = getFlags({"recursive": ["-r", "--recursive"]}, args)

        def rmRec(path: Path):
            for sub in path.iterdir():
                if sub.is_dir():
                    rmRec(sub)

                else:
                    sub.unlink()

            path.rmdir()

        for arg in args:
            path = resolvePath(curdir, arg)
            if not path.exists():
                error(f"File or directory '{arg}' not found.")
                continue

            if path.is_dir():
                if not flags["recursive"]:
                    try:
                        path.rmdir()

                    except OSError:
                        warn(f"Directory '{arg}' is not empty. Use 'rm -r {arg}' to remove it and its contents. Skipping.")

                else:
                    rmRec(path)

            else:
                path.unlink()

    @commandExecuter.buildCommand(['mv', 'move'])
    def move(args: list[str]) -> int | None:
        if len(args) < 2:
            error("Not enough arguments provided. Usage: mv <source> <destination>")
            return 1

        flags = getFlags({"recursive": ["-r", "--recursive"]}, args)

        def mvRec(srcDir: Path, dstDir: Path):
            for sub in srcDir.iterdir():
                if sub.is_dir():
                    dstSubDir = dstDir.joinpath(sub.name)
                    dstSubDir.mkdir(exist_ok=True)
                    mvRec(sub, dstDir.joinpath(sub.name))

                else:
                    dst = dstDir.joinpath(sub.name)
                    with sub.open("rb") as file:
                        content = file.read()

                    if not dst.parent.exists():
                        warn(f"Directory '{dst.parent}' does not exist for destination '{dst}'. Skipping.")
                        continue

                    sub.unlink()

                    if not dst.exists():
                        dst.touch()

                    with dst.open("wb") as file:
                        file.write(content)

            srcDir.rmdir()

        src, dst = resolvePath(curdir, args[0]), resolvePath(curdir, args[1])
        if not src.exists():
            error(f"Source file or directory '{args[0]}' not found.")
            return 1

        if not dst:
            error("No destination provided.")
            return 1

        if src.is_dir():
            if not flags["recursive"]:
                error(f"Source '{args[0]}' is a directory. Use 'mv -r {args[0]} <destination>' to move it and its contents.")

            else:
                dst.mkdir(exist_ok=True)
                mvRec(src, dst)

        else:
            with src.open("rb") as file:
                content = file.read()

            if not dst.parent.exists():
                error(f"Directory '{dst.parent}' does not exist for destination '{dst}'.")
                return 1

            src.unlink()

            if not dst.exists():
                dst.touch()

            with dst.open("wb") as file:
                file.write(content)

    @commandExecuter.buildCommand(['cp', 'copy'])
    def copy(args: list[str]) -> int | None:
        if len(args) < 2:
            error("Not enough arguments provided. Usage: cp <source> <destination>")
            return 1

        flags = getFlags({"recursive": ["-r", "--recursive"]}, args)

        def cpRec(srcDir: Path, dstDir: Path):
            for sub in srcDir.iterdir():
                if sub.is_dir():
                    dstSubDir = dstDir.joinpath(sub.name)
                    dstSubDir.mkdir(exist_ok=True)
                    cpRec(sub, dstDir.joinpath(sub.name))

                else:
                    dst = dstDir.joinpath(sub.name)
                    with sub.open("rb") as file:
                        content = file.read()

                    if not dst.parent.exists():
                        warn(f"Directory '{dst.parent}' does not exist for destination '{dst}'. Skipping.")
                        continue

                    if not dst.exists():
                        dst.touch()

                    with dst.open("wb") as file:
                        file.write(content)

        src, dst = resolvePath(curdir, args[0]), resolvePath(curdir, args[1])
        if not src.exists():
            error(f"Source file or directory '{args[0]}' not found.")
            return 1

        if not dst:
            error("No destination provided.")
            return 1

        if src.is_dir():
            if not flags['recursive']:
                error(f"Source '{args[0]}' is a directory. Use 'cp -r {args[0]} <destination>' to copy it and its contents.")

            else:
                dst.mkdir(exist_ok=True)
                cpRec(src, dst)

        else:
            with src.open("rb") as file:
                content = file.read()

            if not dst.parent.exists():
                error(f"Directory '{dst.parent}' does not exist for destination '{dst}'.")
                return 1

            if not dst.exists():
                dst.touch()

            with dst.open("wb") as file:
                file.write(content)

    @commandExecuter.buildCommand(['var', 'vars'])
    def var(args: list[str]) -> None:
        flags = getFlags({"color": ["-c", "--color"]}, args)

        if not args:
            for name, value in commandExecuter.vars.items():
                print(f"{name} \x1b[91m=\x1b[0m \x1b[92m{repr(value).replace("|", "\x1b[94m | \x1b[92m") if name == "PATH" else repr(value)}\x1b[0m")

            for name, value in commandExecuter.specialVars.items():
                print(f"\x1b[96m{name}\x1b[0m \x1b[91m=\x1b[0m \x1b[92m{repr(value)}\x1b[0m")

            return

        for arg in args:
            if "=" not in arg:
                error(f"Argument '{arg}' is not a valid variable assignment.")
                continue

            name, value = arg.split("=", 1)
            commandExecuter.vars[name] = value

    @commandExecuter.buildCommand(['alias', 'aliases'])
    def alias(args: list[str]):
        if not args:
            for alias, tok in commandExecuter.aliases.items():
                print(f"{alias}={repr(" & ".join([" ".join([f'"{arg}"' if ' ' in arg else arg for arg in ([command.exe] + command.args)]) for command in tok]))}")

            return

        commandExecuter.aliases[args[0]] = commandExecuter.parser(commandExecuter.lexer(args[1].strip()))

@com.buildCommand(['csh'])
def shellFile(args: list[str]) -> int | None:
    global curdir, pastcwd
    if not args:
        error("No shell file provided.")
        return 1

    path = resolvePath(curdir, args[0])
    if not path.is_file():
        error(f"Shell file '{path}' not found.")
        return 1

    comm = CommandExecuter(com.PATH, [], lambda path: resolvePath(curdir, path), com.vars, com.specialVars | {"^": str(path.parent.resolve())}, com.aliases)
    integrateBuiltinCommands(comm)

    for i, arg in enumerate(args):
        comm.vars[str(i)] = arg

    comm.vars["#"] = str(len(args))
    comm.vars["*"] = " ".join(args[1:])

    state: dict[str, Any] = {"global": False, "pcwd": pastcwd, "curcwd": curdir}

    text: str = path.read_text()
    for line in text.splitlines():
        if not line.strip():
            continue

        if line.strip() == "" or line.strip().startswith("#"):
            continue

        if line.strip().startswith("@global"):
            state["global"] = True
            continue

        elif line.strip().startswith("@local"):
            state |= {"global": False, "pcwd": pastcwd, "curcwd": curdir}
            continue

        if isinstance((comm.run(line)), KillSwitch):
            break

    if not state["global"]:
        pastcwd, curdir = state["pcwd"], state["curcwd"]

#================#
#   MAIN LOGIC   #
#================#
if __name__ == "__main__":
    flagsDict: dict[str, list[str]] = {
        "version": ["-v", "--version"],
        "dir": ['-d', '--directory']
    }
    lFlags = getListArgs({"command": ['-c', '--command']}, [alias for flag in flagsDict.values() for alias in flag], (args := sys.argv[1:]))
    flags = getFlags({k: v for k, v in flagsDict.items() if k in ["version"]}, args)
    kwargs = getKwArgs({"dir": ["-d", "--directory"]}, args)
    if flags["version"]:
        print(version)
        exit()

    integrateBuiltinCommands(com)

    if kwargs['dir']:
        com.run(f'cd "{kwargs['dir']}"')

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
                "vars": {},
                "maxHistory": 1000,
                "prompt": 'minimal'
            },
            CONFIG_PATH
        )

    json = importFromJSON(CONFIG_PATH)
    maxHistory(json.get("maxHistory", 100))
    if not ((pathObj := json.get("PATH")) is None):
        com.PATH = [Path(com._replaceVars(path)) for path in pathObj.get("paths", [])] + ([Path(path) for path in PATH] if pathObj.get("includeSystemPath", True) else [])
        com.vars['PATH'] = "|".join([str(path) for path in com.PATH])

    if not ((aliasesObj := json.get("aliases")) is None):
        com.aliases |= {name: com.parser(com.lexer(val.strip())) for name, val in aliasesObj.items()}

    if not ((varsObj := json.get("vars")) is None):
        com.vars |= {name: com._replaceVars(path) for name, path in varsObj.items()}

    if not HIST_PATH.exists():
        HIST_PATH.touch()

    match (promptMode := json.get('prompt', 'minimal')):
        case "minimal":
            PROMPT = lambda: f"\x1b[94m{USERNAME}@{HOSTNAME}\x1b[0m:\x1b[38;5;40m{curdir.shorten(com.specialVars)}\x1b[95m$\x1b[0m "

        case "modern":
            PROMPT = lambda: prompt((curdir.shorten(com.specialVars), ""), ((40, 0),(166, 0), (4, 15)))

        case _:
            warn(f"Unknown prompt '{promptMode}'. Defaulting to minimal.")
            PROMPT = lambda: f"\x1b[94m{USERNAME}@{HOSTNAME}\x1b[0m:\x1b[38;5;40m{curdir.shorten(com.specialVars)}\x1b[95m$\x1b[0m "

    if lFlags["command"]:
        command = " ".join(lFlags["command"])
        com.run(command)
        exit()

    loadHistory(HIST_PATH)

    while True:
        command: str = input(PROMPT())
        try:
            com.run(command)

        except KeyboardInterrupt:
            pass
