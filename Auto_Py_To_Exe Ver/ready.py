version = [1, 0, 0]
VERSION = ".".join([str(num) for num in version])

DEBUG: bool = True

import os
import time
from rich.console import Console
from rich.markup import escape
from pathlib import Path
from json import load, dumps, dump
import inspect

charLists = {
    "alphabet": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "alphanumeric": "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
    "qwerty": "QWERTYUIOPASDFGHJKLZXCVBNM",
    "numeric": "1234567890"
}

def customCypherPreset(charListName : str | list[str], turns : int, *extra, keepCase : bool = True, addInfo : bool = False, getInfo : bool = True, customCharList : bool = False) -> callable:
    def customCypher(text : str):
        if getInfo:
            return [cypher(text, charListName, turns, keepCase=keepCase, addInfo=addInfo, customCharList=customCharList), {"characterListName": charListName, "turns": turns} if customCharList else {"characterList": charListName, "turns": turns}]
        else:
            return cypher(text, charListName, turns, keepCase=keepCase, addInfo=addInfo, customCharList=customCharList)

    def customDeCypher(text : str):
        if getInfo:
            return [deCypher(text, charListName, turns, keepCase=keepCase, addInfo=addInfo, customCharList=customCharList), {"characterListName": charListName, "turns": turns} if customCharList else {"characterList": charListName, "turns": turns}]
        else:
            return deCypher(text, charListName, turns, keepCase=keepCase, addInfo=addInfo, customCharList=customCharList)

    return customCypher, customDeCypher

def cypher(text : str, charListID : str | list[str] = "alphabet", turns : int = 1,*, keepCase : bool = True, addInfo : bool = False, customCharList : bool = False) -> str:
    if not customCharList:
        charList = [char for char in charLists[charListID]]
    else:
        charList = charListID
    newText = ""
    for char in text:
        if char.islower() and keepCase:
            case = 0
        else:
            case = 1
        if charList.__contains__(char.upper()):
            charIdx = charList.index(char.upper())
            charIdx += turns
            charIdx %= len(charList)
            newText += charList[charIdx].lower() if case == 0 else charList[charIdx]
        else:
            newText += char
    if addInfo:
        newText += f"\nturns: {turns}   Character List: {charListID}\n{" " * len(f"turns: {turns}  ")}{"-" * len(f" Character List: {charListID} ")}\n{" " * len(f"turns: {turns}  ")}{charList}"
    return newText

def deCypher(text : str, charListID : str | list[str] = "alphabet", turns : int = 1,*, keepCase : bool = True, addInfo : bool = False, customCharList : bool = False) -> str:
    if not customCharList:
        charList = [char for char in charLists[charListID]]
    else:
        charList = charListID
    newText = ""
    for char in text:
        if char.islower() and keepCase:
            case = 0
        else:
            case = 1
        if charList.__contains__(char.upper()):
            charIdx = charList.index(char.upper())
            charIdx -= turns
            charIdx %= len(charList)
            newText += charList[charIdx].lower() if case == 0 else charList[charIdx]
        else:
            newText += char
    if addInfo:
        newText += f"\nturns: {turns}   Character List: {charListID}\n{" " * len(f"turns: {turns}  ")}{"-" * len(f" Character List: {charListID} ")}\n{" " * len(f"turns: {turns}  ")}{charList}"
    return newText

puzzleCypher, puzzleDeCypher = customCypherPreset("alphabet", 2, keepCase=True, addInfo=False, getInfo=True)

codeCypher, codeDeCypher = customCypherPreset("alphanumeric", 2, keepCase=True, addInfo=False, getInfo=True)

capCypher, capDeCypher = customCypherPreset("alphabet", 2, keepCase=False, addInfo=False, getInfo=False)
from typing import Literal

heldCommands: list[list] = []

def hold(func: callable, *args, **kwargs) -> None:
    heldCommands.append([func, args, kwargs])

def release() -> None:
    for command in heldCommands:
        command[0](*command[1], **command[2])

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

    def __init__(self, names : list[str], func : callable, helpInfo : dict, parserPreset: Literal["default", "base-split"] = "default"):
        self.names : list[str] = names
        self.func = func
        self.helpInfo = helpInfo
        self.helpStr = f"\n\t[bold][cyan]{helpInfo["name"]}[/bold][/cyan]\n\n{helpInfo["description"]}\n\n{f"\t[bold][green]Kwargs:[/bold][/green]\n[bold]{"\n\n[bold]".join([f'{arg}[/bold]: {description}' for arg, description in helpInfo["kwargs"].items()])}\n\n" if helpInfo["has-kwargs"] else ''}Can be called with: [bold][cyan]{"[/bold][/cyan], [bold][cyan]".join(names)}[/bold][/cyan]."
        self.parserPreset = parserPreset

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
            if kwarg != None:
                output[1][kwarg] = None

        return output

    def changeVarArgs(self, parsedUserInput: tuple[str, dict]) -> tuple[str, dict]:
        changedUserInput = parsedUserInput
        for idx, arg in enumerate(flatten(parsedUserInput[1].values())):
            if envVars.__contains__(arg):
                changedUserInput[1][list(parsedUserInput[1].keys())[idx]] = envVars[arg]

        return changedUserInput

    def run(self, userInput : str) -> None:
        if flatten(self.commandNames).__contains__(userInput.split(" ", 1)[0]):
            command : Command = self.commands[indexIntoLayeredList(self.commandNames, userInput.split(" ", 1)[0])]
        else:
            return None

        match command.parserPreset:
            case "default":
                pui = self.changeVarArgs(self.parseCommand(userInput))

            case "base-split":
                parse = userInput.split(" ", 1)
                pui = (parse[0], {"args": parse[1]})

        if numOfNonDefaultArgs(command.func) == 0:
            command.run()
        else:
            command.run(**pui[1])

# Better Addon Attempt
#------------------------------------

class PluginRegistry(type):
    plugins: dict = {}

    def __new__(cls, name, bases, dct):

        try:
            PluginRegistry.plugins[name]
            hold(cli.print, f"[bold][red]Error[/bold][/red]: Plugin '{name}' failed to import; plugin name '[red][bold]{name}[/bold][/red]' already exists")

        except KeyError:
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

#------------------------------------------------------

def lambdaWithKWArgsSetup(lambdaFunc: callable):
    def runLambdaWithKWArgs(**kwargs):
        lambdaFunc(kwargs)

    return runLambdaWithKWArgs

def needsArgsSetup(command: str, args: int, comparison: str = ">=") -> callable:
    def checkAtLeastArgs(**kwargs) -> bool:
        if kwargs["args"] == None or len(kwargs["args"]) < args:
            cli.print(f"The command [bold][cyan]{command}[/bold][/cyan] needs at least {args} arguments.")
            return False
        return True

    def checkAtMostArgs(**kwargs) -> bool:
        if kwargs["args"] != None and len(kwargs["args"]) > args:
            cli.print(f"The command [bold][cyan]{command}[/bold][/cyan] needs at most {args} arguments.")
            return False
        return True

    def checkExactArgs(**kwargs) -> bool:
        if kwargs["args"] == None or len(kwargs["args"]) != args:
            cli.print(f"The command [bold][cyan]{command}[/bold][/cyan] needs exactly {args} arguments.")
            return False
        return True

    def checkNoArgs(**kwargs) -> bool:
        if kwargs["args"] != None:
            cli.print(f"The command [bold][cyan]{command}[/bold][/cyan] does not take any arguments.")
            return False
        return True

    if args == 0:
        return checkNoArgs
    elif comparison == ">=":
        return checkAtLeastArgs
    elif comparison == "<=":
        return checkAtMostArgs
    elif comparison == "=":
        return checkExactArgs

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

def booleanArgs(booleanArgs: list[str], **kwargs) -> dict:
    for arg in booleanArgs:
        try:
            if kwargs[arg] == None:
                pass
            kwargs[arg] = True
        except:
            kwargs[arg] = False

    return kwargs


#---------------------------------------------------

addonClasses: list = []

def importAddons() -> None:
    config = importFromJSON(Path.home().joinpath("config.json"))
    if config["addondir"] == "":
        return None
    addondir = Path(config["addondir"]).absolute()


    global addonClasses

    for file in addondir.iterdir():
        if file.is_file() and file.suffix == ".cmcsaddon2":
            with open(file, "r") as filecontent:
                exec(deCypher(deCypher(filecontent.read(), "alphabet", 13), "numeric", 3), globals())
                addonClasses.append(globals()[list(PluginRegistry.plugins.keys())[-1]](file.name))
                exec(f"{list(PluginRegistry.plugins.keys())[-1]}('{(file.name)}').run()", globals())

def manageAddons(**kwargs) -> None:
    global addonClasses
    kwargs = booleanArgs(["l"], **kwargs)
    if kwargs["l"]:
        cli.print(*tuple(cls.__class__.__name__ for cls in addonClasses if not isinstance(cls, str)), sep="    ")
        return None

    if not needsArgsSetup("addons", 2, "=")(**kwargs):
        return None

    match kwargs["args"][0]:
        case "close":
            idx = list(PluginRegistry.plugins.keys()).index(kwargs["args"][1])
            addonClasses[idx].close()
            addonClasses[idx] = kwargs["args"][1]

        case "run":
            idx = list(PluginRegistry.plugins.keys()).index(kwargs["args"][1])
            addonClasses[idx] = PluginRegistry.plugins[kwargs["args"][1]]
            addonClasses[idx].run()

        case "restart":
            if kwargs["args"][1] == "all":
                for pluginname in PluginRegistry.plugins.keys():
                    cli.print(f"Closing Plugin: [bold][yellow]{pluginname}")
                    PluginRegistry.plugins[pluginname] = None
                    globals().pop(pluginname)

                PluginRegistry.plugins = {key:value for key, value in PluginRegistry.plugins.items() if value != None}

                importAddons()

#---------------------------------------------------

def println(**kwargs) -> None:
    try:
        if kwargs["-file"] != None:
            with open(curdir.joinpath(kwargs["-file"]), "r") as file:
                cli.print(file.read(), style=kwargs["-color"])
    except KeyError:
        if not needsArgsSetup("print", 1)(**kwargs):
            return None

        kwargs = defaultArgs({"s": " ", "-color": None}, **kwargs)
        cli.print(*tuple(kwargs["args"]), sep=kwargs["s"], style=kwargs["-color"])

def execRunCom(filepath : Path, language : str) -> None:
    match language:
        case "python":
            runPyFile(**{"args": filepath})

        case "bin" | "exe":
            os.system(f"start {filepath}")

        case "web" | "website":
            os.system(f"start http://{filepath}")

        case "html":
            os.system(f"start {filepath}")

def runWConfig(**kwargs) -> None:
    if not needsArgsSetup("run", 1, "=")(**kwargs):
        return None

    config = importFromJSON(Path.home().joinpath("config.json"))["run"]
    for runConfig in config:
        if runConfig["names"].__contains__(kwargs["args"][0]):
            execRunCom(f'"{Path(runConfig["path"])}"', runConfig["language"])

def webcutWConfig(**kwargs) -> None:
    if not needsArgsSetup("webcut", 1, "="):
        return None

    config = importFromJSON(Path.home().joinpath("config.json"))["webcut"]
    for webConfig in config:
        if webConfig["names"].__contains__(kwargs["args"][0]):
            execRunCom(Path(webConfig["url"]), "website")

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

def listdir(**kwargs) -> None:
    try:
        kwargs["ps"]
        os.system("powershell ls")
    except KeyError:
        kwargs = defaultArgs({"t": "all", "s": " "*2, "-folder-color": "blue bold", "-file-color": None}, **kwargs)
        folders = []
        files = []
        for file in curdir.iterdir():
            if file.is_dir():
                folders.append(f'"{file.name}"' if file.name.__contains__(" ") else file.name)
            elif file.is_file():
                files.append(f'"{file.name}"' if file.name.__contains__(" ") else file.name)

        match kwargs["t"]:
            case "all":
                cli.print(f"{kwargs["s"].join(folders)}", end=kwargs["s"], style=kwargs["-folder-color"])
                cli.print(f"{kwargs["s"].join(files)}", style=kwargs["-file-color"])

            case "files" | "file" | "f":
                cli.print(f"{kwargs["s"].join(files)}", style=kwargs["-file-color"])

            case "folders" | "dirs" | "folder" | "dir" | "d":
                cli.print(f"{kwargs["s"].join(folders)}", style=kwargs["-folder-color"])

def makeFile(**kwargs) -> None:
    if not needsArgsSetup("makefile", 1)(**kwargs):
        return None

    for file in kwargs["args"]:
        curdir.joinpath(file).touch()

def makeDir(**kwargs) -> None:
    if not needsArgsSetup("makedir", 1)(**kwargs):
        return None

    for folder in kwargs["args"]:
        curdir.joinpath(folder).mkdir(exist_ok=True)

def openVSCode(**kwargs) -> None:
    if not needsArgsSetup("vscode", 1, "=")(**kwargs):
        return None

    os.system(f'code {kwargs["args"][0]}')

def openWebsite(**kwargs) -> None:
    if not needsArgsSetup("website", 1)(**kwargs):
        return None

    for website in kwargs["args"]:
        os.system(f'start http://{website}')

def wait(**kwargs) -> None:
    if not needsArgsSetup("wait", 1, "="):
        return None

    kwargs = defaultArgs({"-format": "seconds"}, **kwargs)

    match kwargs["-format"]:
        case "secs" | "sec" | "s" | "seconds" | "second":
            time.sleep(float(kwargs["args"][0]))

        case "mins" | "min" | "m" | "minutes" | "minute":
            time.sleep(float(kwargs["args"][0]) * 60)

def openNotepad(**kwargs) -> None:
    if not needsArgsSetup("vscode", 1, "<=")(**kwargs):
        return None


    os.system(f'notepad{f' {kwargs["args"]}' if kwargs["args"] != None else ""}')

def changeDir(**kwargs) -> None:
    global curdir
    if kwargs["args"] == None:
        cli.print(curdir)
        return None

    os.chdir(kwargs["args"])
    curdir = Path.cwd()

def executeFile(**kwargs) -> None:
    if kwargs["args"] == '':
        cli.print("The command execute needs an argument.")
        return None

    os.system(f'start {kwargs["args"][0]}')

def runPyFile(**kwargs) -> None:

    config = importFromJSON(Path.home().joinpath("config.json"))
    if not config["needpypath"]:
        os.system(f'python3{f' {kwargs["args"]}' if not kwargs["args"] == '' else ''}')
        return None

    if not Path(config["pypath"]).exists():
        cli.print("[bold][orange]Error:[/bold][/orange] python path does not exist.")
        return None

    filepy = Path(kwargs["args"]).absolute()

    os.chdir(Path(config["pypath"]).absolute())
    os.system(f'python.exe{f' {filepy}' if not kwargs["args"] == None else ''}')
    os.chdir(curdir)

def runHTML(**kwargs) -> None:
    if kwargs["args"] == '':
        cli.print("The command html needs an argument.")
        return None

    for file in kwargs["args"]:
        os.system(f'start {file}')

def renameFile(**kwargs) -> None:
    if not needsArgsSetup("rename", 2, "=")(**kwargs):
        return None

    os.system(f"ren {kwargs["args"][0]} {kwargs['args'][1]}")

def copyFile(**kwargs) -> None:
    if not needsArgsSetup("copy", 2)(**kwargs):
        return None

    with open(kwargs["args"][0], "r") as file:
        fileContent = file.read()

    for file in kwargs["args"][1:]:
        with open(file, "w") as newFile:
            newFile.write(fileContent)

def removeContent(**kwargs) -> None:
    if not needsArgsSetup("remove", 1)(**kwargs):
        return None

    kwargs = booleanArgs(["rf"], **kwargs)

    if kwargs["rf"]:
        os.system(f"rmdir /s {kwargs["args"][0]}")
    else:
        os.system(f"del /f {kwargs["args"][0]}")

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

helpCommand = Command(["help"], lambdaWithKWArgsSetup(lambda kwargs: showHelp(commands, **kwargs)), {"name": "help", "description": "lets you know how to use a command and what that command does.", "has-kwargs": False})

def showHelp(commands : list[Command], **kwargs) -> None:
    commandNames = [command.names for command in commands]
    if kwargs["args"] == None:
        commands[commands.index(helpCommand)].help()
        return None

    if kwargs["args"][0] == "all" or kwargs["args"][0] == "*":
        cli.print(f"\t[bold][cyan]all commands[/bold][/cyan]\n\n[bold][green]{"[/green], [green]".join([command.names[0] for command in commands])}[/green]\n\tRun [yellow]help {escape("[command]")}[/yellow] to learn more.[/bold]")

    if kwargs["args"][0] == "*":
        cli.print("\n-------------------------------------------------------------------------")

    if kwargs["args"][0] == "env" or kwargs["args"][0] == "*":
        cli.print(f"\t[bold][cyan]environment variables[/bold][/cyan]\n\n[bold]{"\n".join([f"[yellow]{k}[/yellow]: [green]{envVars[k]}[/green]" for k in envVars.keys()])}[/bold]")

    if flatten(commandNames).__contains__(kwargs["args"][0]):
        commands[indexIntoLayeredList(commandNames, kwargs["args"][0])].help()

def sysCommand(**kwargs) -> None:
    os.system(kwargs["args"])

def initRecording(comM: CommandManager) -> None:
    def record(**kwargs):
        global recordedCommands
        if not needsArgsSetup("record", 1, "<=")(**kwargs):
            return None

        kwargs = booleanArgs(["l"], **kwargs)
        kwargs = defaultArgs({"f": None}, **kwargs)

        if kwargs["l"]:
            cli.print("\n".join(recordedCommands))

        if kwargs["f"] != None:
            while True:
                mode = cli.input("do you want to use the shell after the inputs? (y/n): ")
                match mode.lower():
                    case "y" | "yes":
                        recordedCommands.append("startinput")
                        break

                    case "n" | "no":
                        break

            Path(kwargs["f"]).touch()
            with open(kwargs["f"], "w") as file:
                file.write("\n".join(recordedCommands))
            return None

        match kwargs["args"][0]:
            case "start":
                comM.recording = True

            case "stop":
                comM.recording = False

            case "clear":
                recordedCommands = []

    comM.commands.append(Command(["record"], record, {"name": "record", "description": "Records Your commands to save as a .cmcs file.", "has-kwargs": True, "kwargs": {"-l": "Lists all currently recorded commands", "-f": "Saves the recorded commands in given filepath as a .cmcs file"}}))
    comM.commandNames = [command.names for command in comM.commands]

#--------------------

commands: list[Command] = []

@lambda _: _()
def initCommands() -> None:
    commands.append(Command(["print"], println, {"name": "print", "description": "Prints the arguments you give it.", "has-kwargs": True, "kwargs": {"-s": "Separating string between each argument", "--color": "Style the printed text", "--file": "Will print the contents of the text file you give it instead of the given arguments"}}))
    commands.append(Command(["exit", "stop"], lambda: exit(), {"name": "exit", "description": "Exits the terminal.", "has-kwargs": False}))

    commands.append(Command(["clear", "cls"], showStartingPrints, {"name": "clear", "description": "Clears the terminal.", "has-kwargs": False}))
    commands.append(Command(["list", "ls"], listdir, {"name": "list", "description": "Lists all files in the current directory.", "has-kwargs": True, "kwargs": {"-ps": "Runs the powershell version of ls instead of the shell's version", "-t": "Filter to both files and folders 'all', only files 'files', or only folders 'folders'", "--folder-color": "Styles the color of the names of the folders", "--file-color": "Styles the color of the names of the files"}}))

    commands.append(Command(["makefile", "mkf"], makeFile, {"name": "makefile", "description": "Makes files.", "has-kwargs": False}))
    commands.append(Command(["makedir", "mkdir"], makeDir, {"name": "makedir", "description": "Makes directories.", "has-kwargs": False}))

    commands.append(Command(["vscode", "code"], openVSCode, {"name": "vscode", "description": "Opens the given file or folder in vscode.", "has-kwargs": False}))
    commands.append(Command(["website", "web"], openWebsite, {"name": "website", "description": "Opens the given websites in your default browser.", "has-kwargs": False}))

    commands.append(Command(["wait", "sleep"], wait, {"name": "sleep", "description": "Waits the given amount of time.", "has-kwargs": True, "kwargs": {"--format": "Takes the given argument and gives it a different unit of time: 'secs', 'mins'"}}))
    commands.append(Command(["notepad", "note", "txt"], openNotepad, {"name": "notepad", "description": "Opens a file in notepad.", "has-kwargs": False}))

    commands.append(Command(["execute", "start", "exe"], executeFile, {"name": "execute", "description": "Runs an executable file", "has-kwargs": False}, 'base-split'))
    commands.append(Command(["cd"], changeDir, {"name": "changedir", "description": "Changes the current directory.", "has-kwargs": False}))

    commands.append(Command(["python", "python3", "py"], runPyFile, {"name": "python", "description": "Runs a python file.", "has-kwargs": False}, 'base-split'))
    commands.append(Command(["html"], runHTML, {"name": "html", "description": "Runs the given HTML files.", "has-kwargs": False}))

    commands.append(Command(["rename", "ren"], renameFile, {"name": "rename", "description": "Renames a given file.", "has-kwargs": False}))
    commands.append(Command(["copy"], copyFile, {"name": "copy", "description": "Copies the contents of a text file to the other given files.", "has-kwargs": False}))

    commands.append(Command(["remove", "rm"], removeContent, {"name": "remove", "description": "Removes a file or folder and all it's content.", "has-kwargs": False}))
    commands.append(Command(["run"], runWConfig, {"name": "run", "description": "Runs a set file via a config.", "has-kwargs": False}))

    commands.append(Command(["webcut", "webc"], webcutWConfig, {"name": "webcut", "description": "Opens up a set website via a config.", "has-kwargs": False}))
    commands.append(Command(["version", "ver"], lambda: cli.print(f"[bold][red]{VERSION}[/bold][/red]"), {"name": "version", "description": "Prints the current version of the shell.", "has-kwargs": False}))

    commands.append(Command(["addons"], manageAddons, {"name": "addons", "description": "Manages all imported addons.", "has-kwargs": True, "kwargs": {"-l": "Lists the currently imported addons."}}))
    commands.append(Command(["system", "sys"], sysCommand, {"name":"system", "description": "Runs the given system command (CMD).", "has-kwargs": False}, "base-split"))

    commands.append(Command(["config"], changeConfig, {"name": "config", "description": "Changes the config file", "has-kwargs": False}))
    commands.append(helpCommand)


def showCWDAndGetInput() -> str:
    return input(f"{str(curdir)}> ")

def inputLoop(comM: CommandManager) -> None:
    while True:
        ui = showCWDAndGetInput()
        comM.run(ui)

configExport = {"needpypath": False, "pypath": "", "addondir": "", "run": [], "webcut": []}

def updateConfig() -> None:
    config = importFromJSON(Path.home().joinpath("config.json"))
    for setting, default in configExport.items():
        try:
            config[setting]
        except KeyError:
            config[setting] = default
    exportToJSON(config, Path.home().joinpath("config.json"))

if not Path.home().joinpath("config.json").exists():
    Path.home().joinpath("config.json").touch()
    exportToJSON(configExport, Path.home().joinpath("config.json"))

updateConfig()

def changeToInterpreter(comM: CommandManager):
    commands[2].func = lambda: os.system("cls")
    commands.insert(-1, Command(["startinput"], lambda: inputLoop(comM), {"name": "startinput", "description": "Starts the user input of a .cmcs file.", "has-kwargs": False}))
    comM.commands = commands
    comM.commandNames = [command.names for command in comM.commands]

importAddons()

comm = CommandManager(commands)

initRecording(comm)

def main():
    showStartingPrints(True)
    release()
    inputLoop(comm)

if __name__ == "__main__":
    main()