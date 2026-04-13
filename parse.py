from typing import Callable
from io import BytesIO
from lexer import *
from utils import importFromJSON, loadModule
from copy import deepcopy
import sys, subprocess, os
from lib.path import Path

class KillSwitch:
    pass

class Command:
    def __init__(self, names : list[str], func : Callable[..., None]):
        self.names : list[str] = names
        self.func = func

    def run(self, *inputs, **kwinputs) -> None | KillSwitch:
        result = self.func(*inputs, **kwinputs)
        return result if isinstance(result, KillSwitch) else None

    def __repr__(self) -> str:
        return f"<Command: {self.names[0]} calls {self.func} by using {", ".join(self.names)}>"

class CommandStdinBuf:
    def __init__(self, stdinBuf: bytes | bytearray | BytesIO | None = None) -> None:
        self.__stdinBuf = None if stdinBuf is None else BytesIO(stdinBuf) if not isinstance(stdinBuf, BytesIO) else stdinBuf

    def read(self, amount: int = -1) -> bytes:
        if self.__stdinBuf is None:
            return sys.stdin.buffer.read(amount)

        return self.__stdinBuf.read(amount)

    def readline(self, limit: int = -1) -> bytes:
        if self.__stdinBuf is None:
            return sys.stdin.buffer.readline(limit)

        return self.__stdinBuf.readline(limit)

class CommandStdoutBuf:
    def __init__(self, flusher: BytesIO | None = None):
        self.__stdoutBuf = bytearray()
        self._flusher = flusher

    def write(self, s: str | bytes) -> None:
        if isinstance(s, str):
            if self._flusher is None:
                sys.stdout.write(s)
                return

            self.__stdoutBuf.extend(bytes(s, 'utf8'))

        elif isinstance(s, bytes):
            if self._flusher is None:
                sys.stdout.buffer.write(s)
                return

            self.__stdoutBuf.extend(s)

    def flush(self) -> None:
        if self._flusher is None:
            sys.stdout.flush()
            return

        self._flusher.write(self.__stdoutBuf)
        self.__stdoutBuf = bytearray()

class CommandExecuter:
    def __init__(self, PATH: list[str] | list[Path], builtinCommands: list[Command] | dict[str, Command], pathResolver: Callable[[str], Path], vars: dict[str, str], specialVars: dict[str, str], aliases: dict[str, list[CommandToken]]) -> None:
        self.commands: dict[str, Command] = {name: cmd for cmd in builtinCommands for name in cmd.names} if isinstance(builtinCommands, list) else builtinCommands
        self.PATH = [Path(path) if isinstance(path, str) else path for path in PATH]
        self.lexer = Lexer()
        self.parser = Parser()
        self.__stdinBuf: CommandStdinBuf | None = None
        self.__stdoutBuf: CommandStdoutBuf | None = None
        self.pathResolver = pathResolver
        self.vars = vars
        self.specialVars = specialVars
        self.aliases = aliases

    def getStdin(self) -> CommandStdinBuf:
        return self.__stdinBuf or CommandStdinBuf(None)

    def getStdout(self) -> CommandStdoutBuf:
        return self.__stdoutBuf or CommandStdoutBuf(None)

    def addCommand(self, command: Command) -> None:
        for name in command.names:
            self.commands[name] = command

    def buildCommand(self, names: list[str]) -> Callable[[Callable], Command]:
        def commandBuilder(func: Callable) -> Command:
            command: Command = Command(names, func)
            self.addCommand(command)
            return command

        return commandBuilder

    def _runSubprocess(self, tok: CommandToken, stdin: BytesIO | None, retStdout: bool = False) -> BytesIO | None:
        EXTS: list[str] = [".py", ".sh" if sys.platform == "linux" else ".bat", ".pyin", ".pyw", ".csh"]
        if os.name == "nt": EXTS.append(".exe")

        exePath: str | Path | None = None
        mode: int = 0
        if Path(tok.exe).is_absolute() and Path(tok.exe).is_file():
            exePath = tok.exe

        if exePath is None and (not self.pathResolver(tok.exe).exists()):
            candidates = [self.pathResolver(tok.exe).parent / name for name in [f"{tok.exe}{ext}" for ext in EXTS]]
            for candidate in candidates:
                if candidate.is_file():
                    exePath = candidate
                    mode = 1
                    break

        if exePath is None:
            for directory in self.PATH:
                if sys.platform == "linux" and os.access(path := (directory / tok.exe), os.X_OK):
                    exePath = path
                    break

                candidates: list[Path] = [directory / name for name in [f"{tok.exe}{ext}" for ext in EXTS]]
                for candidate in candidates:
                    if candidate.is_file():
                        exePath = candidate
                        mode = 1
                        break

                else:
                    continue

                break

        if exePath is None:
            print(f"\x1b[91mCommand not found: {tok.exe}\x1b[0m")
            return

        makeProc: Callable[[list[str]], subprocess.CompletedProcess] = lambda args: subprocess.run(args,
            input=stdin.getvalue() if stdin else None,
            stdout=subprocess.PIPE if retStdout or (tok.stdout is not None) else None,
            stderr=None,
            cwd=os.getcwd()
        )

        capture_stdout = retStdout or (tok.stdout is not None)
        if mode == 1 and isinstance(exePath, Path):
            match exePath.suffix:
                case ".py" | ".pyw" | ".pyin":
                    proc = makeProc(["python3" if sys.platform != "win32" else "python", str(exePath.resolve())] + tok.args)

                case ".sh":
                    proc = makeProc(["bash", str(exePath.resolve())] + tok.args)

                case ".bat":
                    proc = makeProc(["cmd", "/c", str(exePath.resolve())] + tok.args)

                case "":
                    proc = makeProc([str(exePath.resolve())] + tok.args)

                case ".csh":
                    self._runCommand(CommandToken(exe='csh', args=[str(exePath.resolve())] + tok.args, stdin=tok.stdin, stdout=tok.stdout), retStdout)
                    return

                case ".exe":
                    proc = makeProc([str(exePath.resolve())] + tok.args)

                case _:
                    raise Exception(f"Unsupported file type: {exePath.suffix}")

        else:
            proc = subprocess.run(
                ([exePath] + tok.args),
                input=stdin.getvalue() if stdin else None,
                stdout=subprocess.PIPE if capture_stdout else None,
                stderr=None,
                cwd=os.getcwd()
            )

        if capture_stdout:
            if retStdout:
                return BytesIO(proc.stdout)

            elif tok.stdout:
                path = self.pathResolver(tok.stdout)
                if not path.parent.exists():
                    print(f"\x1b[91mPath '{path.parent.resolve()}' doesn't exist.\x1b[0m")
                    return

                if path.is_dir():
                    print(f"\x1b[91mPath '{path.resolve()}' is a directory.\x1b[0m")
                    return

                if not path.exists():
                    path.touch()

                with path.open("wb") as file:
                    file.write(proc.stdout)

            else:
                self.__stdoutBuf.write(proc.stdout) # type: ignore

    def _runCommand(self, tok: CommandToken, retStdout: bool = False) -> BytesIO | None | KillSwitch:
        if isinstance(tok.stdin, CommandToken):
            stdin = self._runCommand(tok.stdin, True) or BytesIO()
            if isinstance(stdin, KillSwitch):
                return stdin

        else:
            stdin = None

        json = importFromJSON(self._replaceVars("%/bin/libs.pmh"))

        if tok.exe in self.commands:
            self.__stdinBuf = CommandStdinBuf(stdin) if not isinstance(stdin, KillSwitch) else None

            self.__stdoutBuf = CommandStdoutBuf(BytesIO() if retStdout or (tok.stdout is not None) else None)
            if isinstance((killRet := self.commands[tok.exe].run(tok.args)), KillSwitch):
                return killRet

            if isinstance(tok.stdout, str):
                path = self.pathResolver(tok.stdout)
                if not path.parent.exists():
                    print(f"\x1b[91mPath '{path.parent.resolve()}' doesn't exist.\x1b[0m")
                    return None

                if path.is_dir():
                    print(f"\x1b[91mPath '{path.resolve()}' is a directory.\x1b[0m")
                    return None

                if not path.exists():
                    path.touch()

                with path.open("wb") as file:
                    file.write((self.getStdout()._flusher or BytesIO()).getvalue())

            if retStdout:
                return self.__stdoutBuf._flusher

        elif tok.exe in json:
            obj: dict[str, str] = json[tok.exe]
            match obj.get("type"):
                case "py/lib":
                    if not obj.get("file") is None:
                        filepath: Path = Path(self._replaceVars(obj['file']))
                        getattr(loadModule(filepath), obj.get("func", "main"))(tok.args)

        else:
            return self._runSubprocess(tok, stdin, retStdout)

    def _replaceVars(self, arg: str) -> str:
        res: str = arg
        mode: int = 0
        esc: bool = False
        L, R = 0, 0
        offset: int = 0
        for i, char in enumerate(arg):
            if char in self.specialVars and mode == 0 and not esc:
                res = f"{res[:i+offset]}{self.specialVars[char]}{res[i+1+offset:]}"
                offset = len(res) - len(arg)
                continue

            match char:
                case "\\":
                    esc = True
                    continue

                case "$":
                    if not esc and mode == 0:
                        mode = 1
                        continue

                    elif esc:
                        res = res[:i+offset-1] + res[i+offset:]

                case "{":
                    if mode == 1:
                        mode = 2
                        L = i+1

                case "}":
                    if mode == 2:
                        mode = 0
                        R = i-1
                        varName = arg[L:R+1]
                        res = f"{res[:L-2+offset]}{self.vars.get(varName, '') or os.getenv(varName, '')}{res[R+2+offset:]}"
                        offset = len(res) - len(arg)

            if esc:
                esc = False

            if mode == 1:
                mode = 0

        return res


    def _replaceVarsRec(self, command: CommandToken) -> CommandToken:
        new_args: list[str] = []
        for arg in command.args:
            replaced = self._replaceVars(arg)
            if ("${*}" in arg) and (" " in replaced):
                new_args.extend(replaced.split(" "))

            else:
                new_args.append(replaced)

        command.args = new_args
        if isinstance(command.stdin, CommandToken):
            command.stdin = self._replaceVarsRec(command.stdin)

        return command

    def _expandAliasRec(self, commands: list[CommandToken]) -> list[CommandToken]:
        res: list[CommandToken] = []
        for command in commands:
            if command.exe in self.aliases:
                coms: list[CommandToken] = deepcopy(self.aliases[command.exe])
                if command.args:
                    coms[-1].args.extend(command.args)

                res.extend(self._expandAliasRec(coms))

            else:
                if isinstance(command.stdin, CommandToken):
                    command.stdin = self._expandAliasRec([command.stdin])[0]

                res.append(command)

        return res

    def run(self, line: str) -> None:
        for command in self._expandAliasRec(self.parser(self.lexer(line.strip()))):
            self._runCommand(self._replaceVarsRec(command))