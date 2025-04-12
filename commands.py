version = [0, 3, 0]
VERSION = ".".join([str(num) for num in version])

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

class CommandManager:

    def __init__(self, commands : list[Command]) -> None:
        self.commands : list[Command] = commands
        self.commandNames : list[list[str]] = [command.names for command in commands]
        self.recording: bool = False

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
        if self.recording:
            recordedCommands.append(userInput)
        pui = self.changeVarArgs(self.parseUserInput(userInput))
        if flatten(self.commandNames).__contains__(pui[0]):
            runCommand : Command = self.commands[indexIntoLayeredList(self.commandNames, pui[0])]
            if numOfNonDefaultArgs(runCommand.func) == len(pui) - 1:
                runCommand.run(*pui[1:])
            elif numOfNonDefaultArgs(runCommand.func) > len(pui) - 1:
                runCommand.run(*flatten([pui[1:], [None for _ in range(len(pui) - 1, numOfNonDefaultArgs(runCommand.func))]]))

helpCommand = Command(["help"], lambda command: showHelp(commands, command), "lets you know how to use a command and what that command does.")

def showHelp(commands : list[Command], userInputCommand : str | None) -> None:
    commandNames = [command.names for command in commands]
    if userInputCommand == None:
        commands[commands.index(helpCommand)].help()
    if userInputCommand == "all" or userInputCommand == "*":
        cli.print(f"\t[bold][cyan]all commands[/bold][/cyan]\n\n[bold][green]{"[/green], [green]".join([command.names[0] for command in commands])}[/green]\n\tRun [yellow]help {escape("[command]")}[/yellow] to learn more.[/bold]")
    if userInputCommand == "*":
        cli.print("\n-------------------------------------------------------------------------")
    if userInputCommand == "env" or userInputCommand == "*":
        cli.print(f"\t[bold][cyan]environment variables[/bold][/cyan]\n\n[bold]{"\n".join([f"[yellow]{k}[/yellow]: [green]{envVars[k]}[/green]" for k in envVars.keys()])}[/bold]")
    if flatten(commandNames).__contains__(userInputCommand):
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
            runPyFile(filepath)

        case "bin" | "exe":
            os.system(f"start {filepath}")

        case "web" | "website":
            os.system(f"start http://{filepath}")

        case "html":
            os.system(f"start {filepath}")

def runWConfig(name : str | None) -> None:
    if name == None:
        cli.print("The run command needs an argument.")
        return None

    config = importFromJSON(Path.home().joinpath("config.json"))["run"]
    for runConfig in config:
        if runConfig["names"].__contains__(name):
            execRunCom(f'"{Path(runConfig["path"])}"', runConfig["language"])

def webcutWConfig(name : str | None) -> None:
    if name == None:
        cli.print("The websitecut command needs an argument.")
        return None

    config = importFromJSON(Path.home().joinpath("config.json"))["webcut"]
    for webConfig in config:
        if webConfig["names"].__contains__(name):
            execRunCom(Path(webConfig["url"]), "website")

def runPyFile(filepath : str | None) -> None:

    config = importFromJSON(Path.home().joinpath("config.json"))
    if not config["needpypath"]:
        os.system(f'python3{f' {filepath}' if not filepath == None else ''}')
        return None

    if not Path(config["pypath"]).exists():
        cli.print("[bold][orange]Error:[/bold][/orange] python path does not exist.")
        return None

    filepy = Path(filepath)

    os.chdir(Path(config["pypath"]).absolute())
    os.system(f'python.exe{f' {filepy}' if not filepath == None else ''}')
    os.chdir(curdir)

validInputs = ["needpypath", "pypath", "addondir"]
validInputTypes = ["bool", "dir", "dir"]

def changeConfig() -> None:

    config = importFromJSON(Path.home().joinpath("config.json"))

    inp = cli.input("Config Change? ").lower()

    if validInputs.__contains__(inp):
        validInputType = validInputTypes[validInputs.index(inp)]
        if validInputType == "bool":
            uinp = cli.input("t/f: ").lower()
            val = True if uinp == "true" or uinp == "t" else False
        elif validInputType == "dir":
            val = cli.input("directory: ")
            if not Path(val).is_dir():
                cli.print(f"'{val}' is not a directory.")
                return None
        config[validInputs[validInputs.index(inp)]] = val
        exportToJSON(config, Path.home().joinpath("config.json"))

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
        if file.is_file() and file.suffix == ".cmcsaddon":
            with open(file, "r") as filecontent:
                exec(filecontent.read())

def renameFile(filepath : str | None, newfilepath: str | None) -> None:
    if filepath == None or newfilepath == None:
        cli.print("The command rename needs a filepath and a new filepath.")
        return None

    os.chdir(str(Path(filepath).parent))
    os.system(f'ren {Path(filepath).name} {newfilepath}')
    os.chdir(curdir)

def copyFile(filepath: str | None, newfilepath: str | None) -> None:
    if filepath == None or newfilepath == None:
        cli.print("The command rename needs a filepath and a new filepath.")
        return None

    with open(filepath, "r") as file:
        content = file.read()
    Path(newfilepath).touch()
    with open(newfilepath, "w") as file:
        file.write(content)

def initRecording(comM: CommandManager) -> None:
    def startRecording():
        comM.recording = True

    def stopRecording():
        comM.recording = False

    def clearRecording():
        global recordedCommands
        recordedCommands = []

    def saveRecording(filepath: str | None) -> None:
        global recordedCommands
        if filepath == None:
            cli.print("The saverecord command needs a filepath")
            return None

        recordedCommands = recordedCommands[0:-1]

        mode = cli.input("do you want to use the shell after the inputs? (y/n): ")
        match mode.lower():
            case "y" | "yes":
                recordedCommands.append("startinput")

        Path(filepath).touch()
        with open(filepath, "w") as file:
            file.write("\n".join(recordedCommands))

    comM.commands.append(Command(["record"], startRecording, "Records Your commands to save as a .cmcs file."))
    comM.commands.append(Command(["stoprecord", "strecord"], stopRecording, "Stops recording commands."))
    comM.commands.append(Command(["clearrecord", "clsrecord"], clearRecording, "Clears the recorded commands."))
    comM.commands.append(Command(["saverecord", "cmcs"], saveRecording, "Saves the recorded commands to a .cmcs file."))
    comM.commandNames = [command.names for command in comM.commands]

commands : list[Command] = []

@lambda _: _()
def setUpCommands() -> None:
    commands.append(Command(["print", "pt"], lambda i: cli.print(i), "Prints out what you input into it."))
    commands.append(Command(["exit", "stop"], lambda: exit(), "Stops the shell."))

    commands.append(Command(["clear", "cls"], showStartingPrints, "Clears the screen."))
    commands.append(Command(["system", "sys"], lambda command: os.system(command), "Runs the system command you pass into it"))

    commands.append(Command(["curdir", "cd"], lambda dir: changeDir(dir), "If no arguments are given, prints the current directory.\nIf 1 argument is given, changes the directory."))
    commands.append(Command(["python", "python3", "py"], lambda file: runPyFile(file), "Runs a python file."))

    commands.append(Command(["listdir", "list", "ls"], lambda mode, length=2: listDir(mode, length), "Lists the contents of the current directory. Mode: [cyan]custom[/cyan], [cyan]ps[/cyan], [cyan]powershell[/cyan]"))
    commands.append(Command(["run"], lambda exec: runWConfig(exec), "Runs a set file via a config. Needs arguments"))

    commands.append(Command(["execute", "start", "exe"], lambda file: os.system(f"start {file}"), "Executes and .exe file"))
    commands.append(Command(["makefile", "mkfile", "mkf"], lambda filename: Path.cwd().joinpath(filename).touch(), "Makes a file with the given name."))

    commands.append(Command(["makedir", "mkdir", "mkd"], lambda dirname: curdir.joinpath(f"{dirname}/").mkdir(exist_ok=True), "Makes a folder with the given name."))
    commands.append(Command(["version", "ver"], lambda: cli.print(f"[bold][red]{VERSION}[/bold][/red]"), "Prints the current version of the shell."))

    commands.append(Command(["sleep", "wait"], lambda secs: time.sleep(float(secs)), "Waits the given number of seconds."))
    commands.append(Command(["textedit", "txte", "notepad", "note"], lambda filepath: os.system(f"notepad{f" {filepath}" if not filepath == None else ""}"), "Opens a document in notepad"))

    commands.append(Command(["vscode", "code", "vsc"], lambda filepath: os.system(f"code {filepath}"), "Opens a file or folder in VSCode."))
    commands.append(Command(["execpy", "rpy"], lambda code: exec(code), "Runs the inputted python code. [bold][red]WARNING[/bold][/red]: can be used for arbritrary code execution."))

    commands.append(Command(["website", "web"], lambda url: os.system(f"start http://{url}"), "Opens the given website in your default browser."))
    commands.append(Command(["html"], lambda filepath: os.system(f"start {filepath}"), "Opens the given HTML file in the default browser."))

    commands.append(Command(["websitecut", "webcut", "webc"], lambda exec: webcutWConfig(exec), "Opens up a set website via a config."))
    commands.append(Command(["config"], lambda: changeConfig(), "Changes the set config file."))

    commands.append(Command(["rename", "ren"], renameFile, "Renames a file to another file."))
    commands.append(Command(["remove", "rm"], lambda file: os.system(f"del {file}"), "Deletes a file."))

    commands.append(Command(["removedir", "rmdir"], lambda folder: os.system(f"rmdir {folder}"), "Deletes a folder."))
    commands.append(Command(["copy"], copyFile, "Copies a file to another file."))

    commands.append(Command(["restartaddons", "rsaddons", "rsa"], importAddons, "Reimports all the cmcs addons from the set folder."))
    commands.append(helpCommand)


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

importAddons()

def changeToInterpreter(comM: CommandManager):
    commands[2].func = lambda: os.system("cls")
    commands.insert(-1, Command(["startinput"], lambda: inputLoop(comM), "Starts the user input of a .cmcs file."))
    comM.commands = commands
    comM.commandNames = [command.names for command in comM.commands]