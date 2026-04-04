from typing import Callable
from pathlib import Path
from io import BytesIO
from lexer import *
import sys, subprocess

class Command:
    def __init__(self, names : list[str], func : Callable[..., None]):
        self.names : list[str] = names
        self.func = func

    def run(self, *inputs, **kwinputs):
        self.func(*inputs, **kwinputs)

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
    def __init__(self, PATH: list[str], builtinCommands: list[Command], pathResolver: Callable[[str], Path]) -> None:
        self.commands: dict[str, Command] = {name: cmd for cmd in builtinCommands for name in cmd.names}
        self.PATH = [Path(path) for path in PATH]
        self.lexer = Lexer()
        self.parser = Parser()
        self.__stdinBuf: CommandStdinBuf | None = None
        self.__stdoutBuf: CommandStdoutBuf | None = None
        self.pathResolver = pathResolver

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

    def _runCommand(self, tok: CommandToken, retStdout: bool = False) -> BytesIO | None:
        if isinstance(tok.stdin, CommandToken):
            stdin = self._runCommand(tok.stdin, True) or BytesIO()

        else:
            stdin = None

        if tok.exe in self.commands:
            self.__stdinBuf = CommandStdinBuf(stdin)
            self.__stdoutBuf = CommandStdoutBuf(BytesIO() if retStdout or (tok.stdout is not None) else None)
            self.commands[tok.exe].run(tok.args)
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

        else:
            try:
                proc = subprocess.Popen([tok.exe, *tok.args], stdin=None if stdin is None else subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = proc.communicate(stdin.getvalue() if stdin is not None else None)
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
                        file.write(stdout)

                print(stdout, stderr)

                if stderr:
                    sys.stderr.buffer.write(stderr)
                    sys.stderr.flush()

                if retStdout:
                    return BytesIO(stdout)

                if stdout:
                    sys.stdout.buffer.write(stdout)
                    sys.stdout.flush()

            except FileNotFoundError:
                print(f"\x1b[91mCommand '{tok.exe}' not found.\x1b[0m")

    def run(self, line: str) -> None:
        for command in self.parser(self.lexer(line.strip())):
            self._runCommand(command)