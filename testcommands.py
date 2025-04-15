version = [0, 3, 0]
VERSION = ".".join([str(num) for num in version])

DEBUG: bool = True

import os
import time
from rich.console import Console
from rich.markup import escape
from pathlib import Path
from json import load, dumps, dump
import inspect
from PuzzlePack import *

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
os.chdir(curdir)

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

recordedCommands: list[str] = []

def combineQuotes(args: list[str]) -> list[str]:
    newargs = []
    inquote = False
    quote = ""
    text = ""
    for arg in args:
        if arg.__contains__('"') or arg.__contains__("'"):
            if arg.__contains__(quote) and inquote:
                inquote = False
                text += arg.strip(quote)
                quote = ""
                newargs.append(text)
                text = ""
            elif not inquote:
                inquote = True
                quote = '"' if arg.__contains__('"') else "'"
                text += arg.strip(quote)
            else:
                text += arg
        else:
            if inquote:
                text += arg
            else:
                newargs.append(arg)
        if inquote:
            text += ' '
    if inquote:
        newargs.append(text[0:-1])
    return newargs

class CommandManager:

    def __init__(self, commands : list[Command]) -> None:
        self.commands : list[Command] = commands
        self.commandNames : list[list[str]] = [command.names for command in commands]
        self.recording: bool = False

    def parseCommand(self, userInput : str) -> tuple[str, dict[str:str]]:
        output: tuple[str, dict[str:str]] = (userInput.split(" ", 1)[0], {"args": None})
        if userInput.__contains__(" "):
            args: list[str] = combineQuotes(userInput.split(" ")[1:])
            kwarg = None
            for arg in args:
                if arg.startswith("-"):
                    if kwarg != None:
                        output[1][kwarg] = None
                    kwarg = arg[1:]
                else:
                    if kwarg != None:
                        output[1][kwarg] = arg
                        kwarg = None
                    else:
                        if output[1]["args"] == None:
                            output[1]["args"] = []
                        output[1]["args"].append(arg)
        return output

    def changeVarArgs(self, parsedUserInput: tuple[str, dict[str:str]]) -> tuple[str, dict[str:str]]:
        changedUserInput = parsedUserInput
        for idx, arg in enumerate(flatten(parsedUserInput[1].values())):
            if envVars.__contains__(arg):
                changedUserInput[1][list(parsedUserInput[1].keys())[idx]] = envVars[arg]

        return changedUserInput

    def run(self, userInput : str) -> None:
        if self.recording:
            recordedCommands.append(userInput)
        pui = self.changeVarArgs(self.parseCommand(userInput))
        if flatten(self.commandNames).__contains__(pui[0]):
            runCommand : Command = self.commands[indexIntoLayeredList(self.commandNames, pui[0])]
            if numOfNonDefaultArgs(runCommand.func) == 0:
                runCommand.run()
            else:
                runCommand.run(**pui[1])

# Better Addon Attempt
#------------------------------------

class PluginRegistry(type):
    plugins: dict = {}

    def __new__(cls, name, bases, dct):

        newPluginClass = super().__new__(cls, name, bases,  dct)

        if bases != ():
            PluginRegistry.plugins[name] = newPluginClass
            if DEBUG:
                cli.print(f"Registered Plugin: [bold][green]{name}")
        else:
            if DEBUG:
                cli.print(f"Created Plugin Base: [bold][green]{name}")

        return newPluginClass

class Plugin(metaclass=PluginRegistry):

    def __init__(self, filepath : Path) -> None:
        self.filepath = filepath

    def run(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

def showStartingPrints(startup : bool = False) -> None:
    os.system("cls")
    if startup:
        cli.print(f"  Welcome to the Custom Shell\nBy: [green][bold]Minemario64[/bold][/green]   Ver: [bold][red]{VERSION}[/bold][/red]")
        cli.print("\nType [bold][yellow]help all[/bold][/yellow] to find all the commands.")
        cli.print("-------------------------------")
    cli.print()

def importAddons() -> None:
    config = importFromJSON(Path.home().joinpath("config.json"))
    if config["addondir"] == "":
        return None
    addondir = Path(config["addondir"]).absolute()
    for file in addondir.iterdir():
        if file.is_file() and file.suffix == ".cmcsaddon2":
            with open(file, "r") as filecontent:
                exec(caesarCypher.deCypher(filecontent.read(), "alphanumeric", 13))
                exec(f"{list(PluginRegistry.plugins.keys())[-1]}('{file.name}').run()")

#------------------------------------------------------

def needsArgsSetup(command: str, args: int) -> callable:
    def checkArgs(**kwargs) -> bool:
        if kwargs["args"] == None or len(kwargs["args"]) < args:
            cli.print(f"The command [bold][cyan]{command}[/bold][/cyan] needs at least {args} arguments.")
            return False
        return True

    return checkArgs

def needsKWArgsSetup(command: str, neededkwargs: list[str]) -> callable:
    def checkKWArgs(**kwargs) -> bool:
        for arg in neededkwargs:
            try:
                if kwargs[arg] == None:
                    cli.print(f"The command [bold][cyan]{command}[/bold][/cyan] needs to have these key word arguments: [bold][green]{"[/bold][/green], [bold][green]".join(neededkwargs[0:-1])}{f"[/bold][/green], and [bold][green]{neededkwargs[-1]}"}[/bold][/green].")
                    return False
            except:
                cli.print(f"The command [bold][cyan]{command}[/bold][/cyan] needs to have these key word arguments: [bold][green]{"[/bold][/green], [bold][green]".join(neededkwargs[0:-1])}{f"[/bold][/green], and [bold][green]{neededkwargs[-1]}"}[/bold][/green].")
                return False
        return True

    return checkKWArgs

def defaultArgs(defaultArgs: dict, **kwargs) -> dict:
    for arg, default in defaultArgs.items():
        try:
            if kwargs[arg] == None:
                kwargs[arg] = default
        except:
            kwargs[arg] = default

    return kwargs

#---------------------------------------------------

def println(**kwargs) -> None:
    if not needsArgsSetup("print", 1)(**kwargs):
        return None

    kwargs = defaultArgs({"s": " ", "-style": None}, **kwargs)
    cli.print(*tuple(kwargs["args"]), sep=kwargs["s"], style=kwargs["-color"])

def sysRun(**kwargs) -> None:
    if kwargs["args"] != None:
        os.system(" ".join(kwargs["args"]))
    os.system(input("sys Command: "))

commands : list[Command] = []

@lambda _: _()
def setUpCommands() -> None:
    commands.append(Command(["print"], println, "Prints the arguments you give it."))
    commands.append(Command(["exit", "stop"], lambda: exit(), "Exits the terminal."))

    commands.append(Command(["clear", "cls"], showStartingPrints, "Clears the terminal."))
    commands.append(Command(["system", "sys"], sysRun, "Runs the system command given."))


def showCWDAndGetInput() -> str:
    return input(f"{str(curdir)}> ")

def inputLoop(comM: CommandManager) -> None:
    while True:
        ui = showCWDAndGetInput()
        comM.run(ui)

configExport = {"needpypath": False, "pypath": "", "addondir": "", "run": [], "webcut": []}

if not Path.home().joinpath("config.json").exists():
    Path.home().joinpath("config.json").touch()
    exportToJSON(configExport, Path.home().joinpath("config.json"))

def changeToInterpreter(comM: CommandManager):
    commands[2].func = lambda: os.system("cls")
    commands.insert(-1, Command(["startinput"], lambda: inputLoop(comM), "Starts the user input of a .cmcs file."))
    comM.commands = commands
    comM.commandNames = [command.names for command in comM.commands]