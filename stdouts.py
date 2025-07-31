import sys
from pathlib import Path
import os

class Stdout:
    style: bool = False

    def __init__(self, *args, **kwargs):
        raise NotImplementedError

    def write(self, data: str):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError

    def __close__(self):
        raise NotImplementedError

    def flush(self):
        raise NotImplementedError

    def __eq__(self, other):
        return self.__class__.__name__ == other.__class__.__name__

class basicConsoleStdout(Stdout):
    style: bool = False

    def __init__(self) -> None:
        pass

    def write(self, data: str):
        sys.stdout.write(data)

    def clear(self):
        os.system("powershell clear")

    def flush(self):
        sys.stdout.flush()

    def __close__(self):
        pass

class fileStdout(Stdout):
    style: bool = False

    def __init__(self, file: str, mode: int = 0) -> None:
        self.filepath = Path(file).resolve()
        if not self.filepath.exists():
            self.stream = self.filepath.open("x")

        if mode == 1:
            self.stream = self.filepath.open("a")

        self.stream = self.filepath.open("w")

    def write(self, data: str):
        self.stream.write(data)

    def clear(self):
        self.stream.truncate(0)

    def flush(self):
        self.stream.flush()

    def __close__(self):
        self.stream.close()

class strStdout(Stdout):
    style: bool = False

    def __init__(self) -> None:
        self.text = ""

    def write(self, data: str):
        self.text += data

    def clear(self):
        self.text = ""

    def flush(self):
        pass

    def __close__(self):
        return self.text

class nullStdout(Stdout):
    style: bool = False

    def __init__(self):
        pass

    def write(self, data: str):
        pass

    def clear(self):
        pass

    def flush(self):
        pass

    def __close__(self):
        pass