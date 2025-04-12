import os
import time
from rich.console import Console
from rich.markup import escape
from pathlib import Path
from json import load, dumps, dump
import inspect

def importFromJSON(filename: str | Path) -> dict | None:
    filepath = Path(filename) if isinstance(filename, str) else filename
    if filepath.exists():
        with open(filepath, "r") as file:
            return load(file)

def exportToJSON(data: dict, filename: str | Path, indent : bool = True) -> None:
    filepath = Path(filename) if isinstance(filename, str) else filename
    if filepath.exists():
        if indent:
            with open(filepath, "w") as file:
                file.write(dumps(data, indent=4))
        else:
            with open(filepath, "w") as file:
                dump(data, file)

def numOfNonDefaultArgs(func) -> int:
    sig = inspect.signature(func)
    return len([param for param in sig.parameters.values() if param.default == inspect.Parameter.empty])

def flatten(l : list) -> list:
    newList : list = []
    for item in l:
        if not isinstance(item, list):
            newList.append(item)
        else:
            for extraItem in flatten(item):
                newList.append(extraItem)
    return newList

def indexThroughLayeredList(l: list, targetVal, start : bool = True, idxStart : int = 0) -> int | None:
    idx : int = 0 if start else idxStart
    for item in l:
        if item == targetVal:
            return idx
        if isinstance(item, list):
            itemResult = indexThroughLayeredList(item, targetVal, False, idx)
            if isinstance(itemResult, int):
                return itemResult
            idx = int(itemResult) - 1
        idx += 1
    if start:
        return None
    return str(idx) if len(l) > 0 else str(idx + 1)

def indexIntoLayeredList(l : list, targetVal, start : bool = True, idxStart : int = 0) -> int | None:
    idx : int = 0 if start else idxStart
    for item in l:
        if item == targetVal:
            return idx
        if isinstance(item, list):
            itemResult = indexIntoLayeredList(item, targetVal, False, idx)
            if isinstance(itemResult, int):
                return itemResult
        idx += 1 if start else 0
    return None

cli = Console()
curdir = Path.home()
pyPath = Path(__file__).parent

envVars = {
    "%FILEDIR%": str(pyPath),
    "%HOME%": str(Path.home()),
    "%USER%": str(Path.home().name),
    "%PYDIR%": str(Path(importFromJSON(Path.home().joinpath("config.json"))["pypath"])) if importFromJSON(Path.home().joinpath("config.json"))["needpypath"] else None
    }

class Command:

    def __init__(self, names : list[str], func : callable, helpStr : str):
        self.names : list[str] = names
        self.func = func
        self.helpStr = f"\t[bold][cyan]{names[0]}[/bold][/cyan]\n\n{helpStr}\n\tCan be called with [bold][cyan]{f"{"[/cyan][/bold], [bold][cyan]".join(names[0:-1])}[/cyan][/bold], or [bold][cyan]{names[-1]}" if len(names) > 2 else f"{"[/cyan][/bold] and [bold][cyan]".join(names)}" if len(names) == 2 else f"[cyan][bold]{names[0]}"}[/cyan][/bold]"

    def run(self, *inputs, **kwinputs):
        return self.func(*inputs, **kwinputs)

    def help(self) -> None:
        cli.print(self.helpStr)

    def __repr__(self) -> str:
        return f"<Command: {self.names} calls {self.func}>"

class CommandManager:

    def __init__(self, commands : list[Command]) -> None:
        self.commands : list[Command] = commands
        self.commandNames : list[list[str]] = [command.names for command in commands]

    def parseUserInput(self, userInput : str) -> list[str]:
        splitText = userInput.split(" ")
        txtIn = 0
        inTxt = ''
        quoteIdx = [0, 0]
        chars = ["", ""]
        parsedText = splitText.copy()
        for txt in splitText:
            if txtIn > 0:
                parsedText.remove(txt)
            for ltxt in list(txt):
                if ltxt == '"' or ltxt == "'":
                    if inTxt == ltxt:
                        if txtIn == 2:
                            txtIn -= 1
                            inTxt = '"' if ltxt == "'" else "'"
                        elif txtIn == 1:
                            parsedText.insert(quoteIdx[txtIn - 1], chars[txtIn - 1])
                            txtIn -= 1
                            inTxt = ''
                    else:
                        quoteIdx[txtIn] = splitText.index(txt)
                        parsedText.remove(txt)
                        txtIn += 1
                        inTxt = ltxt
                elif txtIn > 0:
                    chars[txtIn - 1] += ltxt
            if txtIn > 0:
                chars[txtIn - 1] += " "
        return parsedText

    def changeVarArgs(self, parsedUserInput: list[str]) -> list[str]:
        changedUserInput = parsedUserInput.copy()
        for part in parsedUserInput:
            if envVars.__contains__(part):
                changedUserInput[parsedUserInput.index(part)] = envVars[part]
        return changedUserInput

    def run(self, userInput : str) -> None:
        pui = self.changeVarArgs(self.parseUserInput(userInput))
        if flatten(self.commandNames).__contains__(pui[0]):
            runCommand : Command = self.commands[indexIntoLayeredList(self.commandNames, pui[0])]
            if numOfNonDefaultArgs(runCommand.func) == len(pui) - 1:
                runCommand.run(*pui[1:])
            elif numOfNonDefaultArgs(runCommand.func) > len(pui) - 1:
                runCommand.run(*flatten([pui[1:], [None for _ in range(len(pui) - 1, numOfNonDefaultArgs(runCommand.func))]]))