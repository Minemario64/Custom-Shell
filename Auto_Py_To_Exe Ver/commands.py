import os
import time
from rich.console import Console
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
pyPath = Path(Path(__file__).parent).joinpath("/_internal")
os.chdir(curdir)

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

    def run(self, userInput : str) -> None:
        pui = self.parseUserInput(userInput)
        if flatten(self.commandNames).__contains__(pui[0]):
            runCommand : Command = self.commands[indexIntoLayeredList(self.commandNames, pui[0])]
            if numOfNonDefaultArgs(runCommand.func) == len(pui) - 1:
                runCommand.run(*pui[1:])
            elif numOfNonDefaultArgs(runCommand.func) > len(pui) - 1:
                runCommand.run(*flatten([pui[1:], [None for _ in range(len(pui) - 1, numOfNonDefaultArgs(runCommand.func))]]))

def showHelp(commands : list[Command], userInputCommand : str | None) -> None:
    commandNames = [command.names for command in commands]
    if userInputCommand == None:
        commands[-1].help()
    elif flatten(commandNames).__contains__(userInputCommand):
        commands[indexIntoLayeredList(commandNames, userInputCommand)].help()

def changeDir(newDir: str | None) -> None:
    global curdir
    if newDir == None:
        cli.print(curdir)
    else:
        os.chdir(newDir)
        curdir = Path().cwd()

def listDir(mode: str | None, lenOfSep : int = 2) -> None:
    listMode = "custom" if mode == None else mode
    match listMode:
        case "custom":
            cli.print((" "*lenOfSep).join([f"[bold]{path.name if not list(path.name).__contains__(" ") else f'"{path.name}"'}[/bold]" if not path.is_dir() else f"[bold][cyan]{path.name if not list(path.name).__contains__(" ") else f'"{path.name}"'}[/bold][/cyan]"  for path in curdir.iterdir()]))

        case "ps" | "powershell":
            os.system("powershell ls")

        case _:
            cli.print(f"[bold][cyan]{listMode}[/bold][/cyan] is not a valid mode. Check the help to find the valid modes")

def execRunCom(filepath : Path, language : str) -> None:
    match language:
        case "python":
            os.system(f"python3 {filepath}")

        case "bin" | "exe":
            os.system(f"start {filepath}")

def runWConfig(name : str | None) -> None:
    if name == None:
        cli.print("The run command needs an argument.")
        return None

    config = importFromJSON(pyPath.joinpath("config.json"))["run"]
    for runConfig in config:
        if runConfig["names"].__contains__(name):
            execRunCom(Path(runConfig["path"]), runConfig["language"])

def showStartingPrints(startup : bool = False) -> None:
    os.system("cls")
    if startup:
        cli.print("  Welcome to the Custom Shell\nBy: [green][bold]Minemario64[/bold][/green]   Ver: [bold][red]0.1.0[/bold][/red]")
        cli.print("-------------------------------")
    cli.print()

commands : list[Command] = []

def changeToInterpreter():
    commands[2].func = lambda: os.system("cls")

@lambda _: _()
def setUpCommands() -> None:
    commands.append(Command(["print", "pt"], lambda i: cli.print(i), "Prints out what you input into it."))
    commands.append(Command(["exit", "stop"], lambda: exit(), "Stops the shell."))
    commands.append(Command(["clear", "cls"], lambda: showStartingPrints(), "Clears the screen."))
    commands.append(Command(["system", "sys"], lambda command: os.system(command), "Runs the system command you pass into it"))
    commands.append(Command(["curdir", "cd"], lambda dir: changeDir(dir), "If no arguments are given, prints the current directory.\nIf 1 argument is given, changes the directory."))
    commands.append(Command(["python", "python3", "py"], lambda file: os.system(f"python3{f" {file}" if not file == None else ""}"), "Runs a python file."))
    commands.append(Command(["listdir", "list", "ls"], lambda mode, length=2: listDir(mode, length), "Lists the contents of the current directory. Mode: [cyan]custom[/cyan], [cyan]ps[/cyan], [cyan]powershell[/cyan]"))
    commands.append(Command(["run"], lambda exec: runWConfig(exec), "Runs a set file via a config. Needs arguments"))
    commands.append(Command(["execute", "start", "exe"], lambda file: os.system(f"start {file}"), "Executes and .exe file"))
    commands.append(Command(["makefile", "mkfile", "mkf"], lambda filename: Path.cwd().joinpath(filename).touch(), "Makes a file with the given name."))
    commands.append(Command(["makedir", "mkdir", "mkd"], lambda dirname: Path.cwd().joinpath(f"/{dirname}").mkdir(exist_ok=True), "Makes a folder with the given name."))
    commands.append(Command(["version", "ver"], lambda: cli.print("[bold][red]0.1.0[/bold][/red]"), "Prints the current version of the shell."))
    commands.append(Command(["sleep", "wait"], lambda secs: time.sleep(float(secs)), "Waits the given number of seconds."))

    commands.append(Command(["help"], lambda command: showHelp(commands, command), "lets you know how to use a command and what that command does."))