import os
import time
from rich.console import Console
from pathlib import Path
import inspect

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
os.chdir(Path.home())

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
        return userInput.split(" ")

    def run(self, userInput : str) -> None:
        pui = self.parseUserInput(userInput)
        if flatten(self.commandNames).__contains__(pui[0]):
            runCommand : Command = self.commands[indexIntoLayeredList(self.commandNames, pui[0])]
            if numOfNonDefaultArgs(runCommand.func) == len(pui) - 1:
                runCommand.run(*pui[1:])
            elif numOfNonDefaultArgs(runCommand.func) > len(pui) - 1:
                runCommand.run(*flatten([pui[1:], [None for _ in range(len(pui) - 1, numOfNonDefaultArgs(runCommand.func))]]))

commands : list[Command] = []

def showHelp(commands : list[Command], userInputCommand : str | None) -> None:
    commandNames = [command.names for command in commands]
    if userInputCommand == None:
        commands[-1].help()
    elif flatten(commandNames).__contains__(userInputCommand):
        commands[indexIntoLayeredList(commandNames, userInputCommand)].help()

@lambda _: _()
def setUpCommands() -> None:
    commands.append(Command(["print", "pt"], lambda i: print(i), "Prints out what you input into it."))
    commands.append(Command(["exit", "stop"], lambda: exit(), "Stops the shell."))

    commands.append(Command(["help"], lambda command: showHelp(commands, command), "lets you know how to use a command and what that command does."))

comm = CommandManager(commands)

def showStartingPrints(startup : bool = False) -> None:
    os.system("cls")
    if startup:
        cli.print("Welcome to the Custom Shell\n     By: [green][bold]Minemario64[/bold][/green]")
        cli.print("---------------------------")
    cli.print()

def showCWDAndGetInput() -> str:
    return cli.input(f"{str(curdir)}> ")

def main():
    showStartingPrints(True)
    while True:
        ui = showCWDAndGetInput()
        comm.run(ui)

if __name__ == "__main__":
    main()