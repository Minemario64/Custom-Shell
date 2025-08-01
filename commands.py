ver = [1, 3, 1, ""]

version = (".".join([str(num) for num in ver[0:3]]), ver[3])
def Version(sep: str) -> str:
    return f"{version[0]}{sep}{version[1]}" if version[1] != '' else version[0]

import os
import time
from rich.console import Console
from pathlib import Path
from json import load, dumps, dump
import json.decoder as JSONDecoder
import inspect
import re
from projectManager import *
from stdouts import *
from caesarCypher import *
from typing import Literal, Any, Callable
from varTypes import *
from asciiart import display, TERMINAL_WIDTH
from stats import SystemStats
from getpass import getpass


# GLOBAL SETTINGS
DEV: bool = True
REPLACE_V2: bool = False

if ((sys.argv[1:].__contains__("-nd") or sys.argv[1:].__contains__("--nodebug")) or (__name__ == "__main__" and not DEV)) or not DEV:
    DEBUG: bool = False

else:
    DEBUG: bool = True

heldCommands: list[list] = []
stdout = basicConsoleStdout()

def runImmediately(func):
    func()

    return func

def hold(func: Callable, *args, **kwargs) -> None:
    heldCommands.append([func, args, kwargs])

def release() -> None:
    for command in heldCommands:
        command[0](*command[1], **command[2])

def importFromJSON(filename: str | Path) -> dict:
    filepath = Path(filename) if isinstance(filename, str) else filename
    if filepath.exists():
        with open(filepath, "r") as file:
            return load(file)

    raise FileNotFoundError(f"'{str(filepath)}' does not exist")

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

def indexThroughLayeredList(l: list, targetVal, start : bool = True, idxStart : int = 0) -> int | str:
    idx : int = 0 if start else idxStart
    for item in l:
        if (item == targetVal) and (type(item) == type(targetVal)):
            return idx
        if isinstance(item, list):
            itemResult = indexThroughLayeredList(item, targetVal, False, idx)
            if isinstance(itemResult, int):
                return itemResult
            idx = int(itemResult) - 1
        idx += 1
    if start:
        raise IndexError(f"Does not have the value {repr(targetVal)}")

    return str(idx) if len(l) > 0 else str(idx + 1)

def indexIntoLayeredList(l : list, targetVal, start : bool = True, idxStart : int = 0) -> int:
    idx : int = 0 if start else idxStart
    for item in l:
        if (item == targetVal) and (type(item) == type(targetVal)):
            return idx
        if isinstance(item, list):
            itemResult = indexIntoLayeredList(item, targetVal, False, idx)
            if isinstance(itemResult, int) and itemResult != -1:
                return itemResult
        idx += 1 if start else 0
    if start:
        raise IndexError(f"Does not have the value {repr(targetVal)}")

    return -1

def is_hidden(path: Path) -> bool:
    try:
        return bool(os.stat(path).st_file_attributes & 0x2)

    except FileNotFoundError:
        return False

class ConsoleStdout(basicConsoleStdout):
    style: bool = True

    def __init__(self, console: Console) -> None:
        self.console = console

    def write(self, data: str):
        self.console.print(data, end="")

    def clear(self):
        os.system("powershell clear")

    def flush(self):
        sys.stdout.flush()

    def __close__(self):
        pass

def removeRichStyling(text: str) -> str:
    return "".join([l[0] for l in [text.split("[") for text in text.split("]")]])

OGPrint = print

def print(*textArgs, sep: str = " ", end: str = "\n", style: str | None = None, flush: bool = False) -> None:
    output = sep.join(map(str, textArgs)) + end
    if stdout.__class__.style:
        if style != None:
            stdout.write(f"[{style}]{output}[/{style}]")

        else:
            stdout.write(output)

    else:
        stdout.write(removeRichStyling(output))

    if flush:
        stdout.flush()

try:
    if sys.argv[1:].__contains__("--version") or (sys.argv[1:].__contains__("-k") or sys.argv[1:].__contains__("--keep")) or ([arg for arg in sys.argv[1:] if not arg.startswith("-")][0].__contains__("neofetch") or Path([arg for arg in sys.argv[1:] if not arg.startswith("-")][0]).resolve(True)):
        HOSTNAME = SystemStats()['hostname']

except (FileNotFoundError, IndexError, OSError):
    HOSTNAME = SystemStats()['hostname']

jsonTypesToBytes = lambda data, sep=" ": bytes([int(binStr, 2) for binStr in data.split(sep)])

curdir = Path.home()
cwd = Path.cwd()
pyPath = Path(__file__).parent if DEBUG else Path.cwd()
jsonPath = Path.home().joinpath(".csconfig")

os.chdir(curdir)

configExport = {"~:Home": False, "Auto-Highlighting": True, "needpypath": False, "pycommand": "python", "pypath": "", "addondir": "", "run": [], "webcut": [], "vars": [], "aliases": {"la": "ls -a"}, "bookmarks": {}}
configTypes = {"~:Home": "bool", "Auto-Highlighting": "bool", "needpypath": "bool", "pycommand": "str", "pypath": "dirpath/", "addondir": "dirpath", "run": "managed", "webcut": "managed", "vars": "managed", "aliases": "managed", "bookmarks": "managed"}
configTypeUsr = {"bool": "Boolean", "": "Nothing", "dirpath": "Directory", "str": "String"}

def updateConfig() -> None:
    try:
        config = importFromJSON(jsonPath)

    except JSONDecoder.JSONDecodeError as e:
        print(f"\033[1;91mERROR\033[0m\033[31m: Could not decode the Custom-Shell config file -- {repr(e).removeprefix("JSONDecodeError(\"").removesuffix("\")")}\033[0m")
        os._exit(0)

    result = {}
    for setting, default in configExport.items():
        try:
            config[setting]
            result[setting] = config[setting]

        except KeyError:
            result[setting] = default

    exportToJSON(result, jsonPath)

if not jsonPath.exists():
    jsonPath.touch()
    if cwd.joinpath(".csconfig").exists():
        json = importFromJSON(cwd.joinpath(".csconfig"))
        exportToJSON(json, jsonPath)
        updateConfig()

    else:
        exportToJSON(configExport, jsonPath)

else:
    updateConfig()

envVars = {
    "FILEDIR": PathVar(str(pyPath)),
    "USER": StrVar(Path.home().name),
    "ROOT": PathVar(str(Path.root)),
    "APPDATA": PathVar(str(Path.home().joinpath("AppData/Roaming"))),
    "LOCALAPPDATA": PathVar(str(Path.home().joinpath("AppData/Local"))),
    "PYDIR": PathVar(str(Path(importFromJSON(jsonPath)["pypath"]))) if importFromJSON(jsonPath)["needpypath"] else StrVar(''),
    "V": StrVar(Version("-"))
}

ENVIRONMENT_VARS = {f"%{name}%": value for name, value in envVars.items()} | {"~": PathVar(str(Path.home()))}

cli = Console(highlight=importFromJSON(jsonPath)["Auto-Highlighting"])

stdout = ConsoleStdout(cli)
__stdout__ = stdout

class Command:

    def __init__(self, names : list[str], func : Callable[..., None], helpInfo : dict, parserPreset: Literal["default", "base-split"] = "default"):
        self.names : list[str] = names
        self.func = func
        self.helpInfo = helpInfo
        self.helpStr = f"\n\t[bold][cyan]{helpInfo["name"]}[/bold][/cyan]\n\n{helpInfo["description"]}\n\n{f"\t[bold][green]Kwargs:[/bold][/green]\n[bold]{"\n\n[bold]".join([f'{arg}[/bold]: {description}' for arg, description in helpInfo["kwargs"].items()])}\n\n" if helpInfo["has-kwargs"] else ''}Can be called with: [bold][cyan]{"[/bold][/cyan], [bold][cyan]".join(names)}[/bold][/cyan]."
        self.parserPreset = parserPreset

    def run(self, *inputs, **kwinputs):
        self.func(*inputs, **kwinputs)

    def help(self, prefix: str = '') -> None:
        if prefix != '':
            helpStr = f"\n\t[bold][cyan]{self.helpInfo["name"]}[/bold][/cyan]\n\n{self.helpInfo["description"]}\n\n{f"\t[bold][green]Kwargs:[/bold][/green]\n[bold]{"\n\n[bold]".join([f'{arg}[/bold]: {description}' for arg, description in self.helpInfo["kwargs"].items()])}\n\n" if self.helpInfo["has-kwargs"] else ''}Can be called with: [bold][cyan]{"[/bold][/cyan], [bold][cyan]".join([f"{prefix}{name}" for name in self.names])}[/bold][/cyan]."
            print(helpStr)
            return

        print(self.helpStr)

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
                text += arg.removesuffix(quote)
                quote = ""
                newargs.append(text)
                text = ""

            elif not inquote:
                inquote = True
                quote = '"' if arg.__contains__('"') else "'"
                text += arg.removeprefix(quote)
                if arg.endswith(quote):
                    text = text[0:-1]

                inquote = False
                newargs.append(text)

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

def getVar(text: str, mode: Literal['$', '%', '%%']) -> tuple[str, str, str]:
    type = ''
    name = ''
    value = ''
    part = 0
    for char in text:
        match part:
            case 0:
                if char == mode[0]:
                    part += 1
                    continue

                if char == " ":
                    continue

                type += char

            case 1:
                if char == "=":
                    part += 1
                    name = name.rstrip(" ")
                    if mode == '%%':
                        name = name.removesuffix("%")
                    continue

                name += char

            case 2 | 3:
                if char == " " and part == 2:
                    continue

                value += char
                part = 3

    return (type, name, value)

class CommandManager:

    def __init__(self, commands : list[Command]) -> None:
        self.commands : list[Command] = commands
        self.commandNames : list[list[str]] = [command.names for command in commands]
        self.aliases = {alias: command for alias, command in importFromJSON(jsonPath)['aliases'].items()}
        self.vars: dict[str, VarType] = ENVIRONMENT_VARS | {f"%{dct["name"]}": TypeRegistry.types[TypeRegistry.nicknames[dct['type']]](TypeRegistry.types[TypeRegistry.nicknames[dct['type']]].__jload__(jsonTypesToBytes(dct["data"]))) for dct in importFromJSON(jsonPath)['vars']}
        self.recording: bool = False

    def parseCommand(self, userInput : str) -> dict[str, str | None | list[str] | bool | VarType]:
        output: dict[str, str | None | list[str] | bool | VarType] = {"args": None}
        if userInput.__contains__(" "):
            args: list[str] = combineQuotes(userInput.split(" ")[1:])
            kwarg = None
            for arg in args:
                if arg.startswith("-"):
                    if kwarg != None:
                        output[kwarg] = None
                    kwarg = arg[1:]
                else:
                    if kwarg != None:
                        output[kwarg] = arg
                        kwarg = None
                    else:
                        if output["args"] == None:
                            output["args"] = []
                        output["args"].append(arg) # pyright: ignore[reportAttributeAccessIssue]
            if kwarg != None:
                output[kwarg] = None

        return output

    def changeVarArgs(self, parsedUserInput: dict[str, str | None | list[str] | bool | VarType]) -> dict[str, str | None | list[str] | bool | VarType]:
        result = list(parsedUserInput.values())
        for idx, item in enumerate(result):
            if isinstance(item, list):
                for i, arg in enumerate(item):
                    if REPLACE_V2:
                        if arg != '':
                            print(arg)
                            print(self.vars.items())
                            for name, val in self.vars.items():
                                spl = arg.split(name)
                                print(*[f"{len(itm) - 1} {itm} | {name}: {val} | {spl}" for itm in spl], sep="\n")
                                l = [(itm[len(itm) - 1] != "\\" and i != len(itm) - 1) for i, itm in enumerate(spl)]
                                print(l, spl)
                                if len(l) > 1:
                                    item[i] = "".join([(itm + str(val)) if addVal else (itm[0:-1] + name) for itm, addVal in zip(spl, l)])
                                    arg = item[i]
                                    print("Updated")

                    else:
                        for name, val in self.vars.items():
                                item[i] = arg.replace(name, str(val))
                                arg = item[i]

                result[idx] = item
                continue

            elif isinstance(item, str):
                for name, val in self.vars.items():
                    result[idx] = item.replace(name, str(val))

        return {key: value for key, value in zip(parsedUserInput.keys(), result)}

    def parseStdout(self, commandStr: str, text: str) -> Stdout:
        match text:
            case "basic":
                return basicConsoleStdout()

            case "nul" | "null":
                return nullStdout()

            case "hold":
                hold(self.run, commandStr)
                return stdout

            case _:
                if text.startswith("+") and len(text.split(" ")) > 1:
                    return fileStdout(text, 1)

                return fileStdout(text)

    def setVar(self, name: str, value: VarType) -> None:
        self.vars[name] = value

    def releaseVer(self, name: str) -> None:
        self.vars.pop(name)

    def run(self, userInput : str, mode: int = 0) -> None:
        global stdout
        for alias in self.aliases.keys():
            if userInput.split(" ", 1)[0] == alias:
                userInput = userInput.replace(alias, self.aliases[alias])

        if userInput.__contains__("&&"):
            full = False
            if userInput.split("&&")[-1].split(">", 1)[0].strip(" ") == "":
                full = True

            if userInput.split("&&")[0].split(" ", 1)[0].lower() != "alias":
                for command in [com for i, com in enumerate(userInput.split("&&"), 1) if i != len(userInput.split("&&"))]:
                    if full:
                        command = f"{command} > {userInput.split("&&")[-1].split(">", 1)[1].strip(" ")}"

                    self.run(command.strip(" "))
                return

        if userInput.__contains__("|"):
            stop: bool = False
            try:
                if userInput.split(">", 1)[1].__contains__("|"):
                    stop = True

            except IndexError:
                pass

            if not stop:
                xtra: str = ""
                for i, inp in enumerate(userInput.split("|")):
                    if i < len(userInput.split("|")) - 1:
                        stdout = strStdout()
                        self.run(f"{inp} {xtra}".strip(" "), 1)
                        xtra = stdout.__close__().rstrip("\n")
                        continue

                    stdout = ConsoleStdout(cli)
                    if inp.__contains__(">"):
                        self.run(f"{inp.split(">", 1)[0].strip(" ")} \"{xtra}\" > {inp.split(">", 1)[1].lstrip(" ")}".strip(" "))
                        continue

                    self.run(f"{inp} {xtra}".strip(" "))

                return

        if userInput.__contains__(">") and mode != 1:
            userInput, stdoutStr = (text.strip(" ") for text in userInput.split(">", 1))
            r = self.parseStdout(userInput, stdoutStr)
            if stdout == r:
                return

            else:
                stdout = r

        if flatten(self.commandNames).__contains__(userInput.split(" ", 1)[0].lower()):
            command : Command | str = self.commands[indexIntoLayeredList(self.commandNames, userInput.split(" ", 1)[0].lower())]

        else:
            if not userInput.split(" ", 1)[0].startswith("alias"):
                sessionVarPattern = re.compile(r"^[a-z]* \$[a-zA-Z0123456789-_+]* *= *.*$")
                globalVarPattern = re.compile(r"^[a-z]* %[a-zA-Z0123456789-_+]* *= *.*$")
                printVarPattern = re.compile(r"^[$%][a-zA-Z0123456789-_+]*%?")
                if sessionVarPattern.match(userInput):
                    type, name, value = getVar(userInput, '$')
                    try:
                        value = TypeRegistry.types[TypeRegistry.nicknames[type]](value)
                    except KeyError:
                        pass
                    if not isinstance(value, str):
                        self.setVar(f"${name}", value)
                        return

                if globalVarPattern.match(userInput):
                    type, name, value = getVar(userInput, '%')
                    try:
                        value = TypeRegistry.types[TypeRegistry.nicknames[type]](value)
                    except KeyError:
                        cli.print(f"There is no type named '{type}'")

                    if not isinstance(value, str):
                        self.setVar(f"%{name}", value)
                        json = importFromJSON(jsonPath)
                        strOfBytes = lambda data: "".join([bit for byte in data for bit in f'{byte:08b} ']).removesuffix(" ")
                        try:
                            json['vars'][name]
                            json['vars'][name] = {"name": name, "type": type, "data": strOfBytes(value.__json__())}

                        except TypeError:
                            json['vars'].append({"name": name, "type": type, "data": strOfBytes(value.__json__())})

                        exportToJSON(json, jsonPath)
                        return

                if printVarPattern.match(userInput):
                    print(self.vars[userInput])
                    return

                if userInput != "":
                    cli.print(f"The command [bold][cyan]{userInput.split(" ", 1)[0]}[/cyan][/bold] is invalid.")
                return

            save = userInput.split(" ")[1] == "save" or userInput.split(" ")[1] == "-s"
            alias, command = [string.strip(" ") for string in userInput.split(" ", 2 if save else 1)[-1].split("=", 1)]
            if alias.__contains__(" "):
                cli.print(f"Failed to make alias '{alias}', contains a space.")

            self.aliases[alias] = command
            if save:
                json = importFromJSON(jsonPath)
                json["aliases"][alias] = command
                exportToJSON(json, jsonPath)

            return

        if command.names != ['record'] and self.recording:
            recordedCommands.append(userInput)

        match command.parserPreset:
            case "default":
                pui = self.changeVarArgs(self.parseCommand(userInput))

            case "base-split":
                parse = userInput.split(" ", 1)
                if len(parse) == 1:
                    pui = {"args": ''}

                else:
                    pui = {"args": parse[1]}

            case _:
                raise ValueError(f"Command '{command.names[0]}' has an invalid parser preset.")

        if numOfNonDefaultArgs(command.func) == 0:
            command.run()
        else:
            command.run(**pui)

        if stdout != __stdout__ and mode != 1:
            stdout.__close__()
            stdout = ConsoleStdout(cli)

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

#------------------------------------------------------

def lambdaWithKWArgsSetup(lambdaFunc: Callable):
    def runLambdaWithKWArgs(**kwargs):
        lambdaFunc(kwargs)

    return runLambdaWithKWArgs

def lambdaWithArgsSetup(lambdaFunc: Callable):
    def runLambdaWithArgs(**kwargs):
        lambdaFunc(kwargs['args'][0])

    return runLambdaWithArgs

def needsArgsSetup(command: str, args: int, comparison: str = ">=") -> Callable[..., bool] | Callable[..., Callable[..., bool]]:
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

    def checkRangeOfArgs(min: int, max: int) -> Callable[..., bool]:
        def checkArgs(**kwargs) -> bool:
            if (kwargs['args'] == None and min > 0) or len(kwargs["args"]) < min or len(kwargs["args"]) > max:
                cli.print(f"The command [bold][cyan]{command}[/bold][/cyan] needs between {min} arguments and {max} arguments.")
                return False
            return True

        return checkArgs

    if args == 0:
        return checkNoArgs

    if comparison == ">=":
        return checkAtLeastArgs

    if comparison == "<=":
        return checkAtMostArgs

    if comparison == "=":
        return checkExactArgs

    if re.compile(r"[0123456789]*-[0123456789]*").match(comparison):
        return checkRangeOfArgs(int(comparison.split("-")[0]), int(comparison.split("-")[1]))

    raise ValueError(f"Invalid Comparison. Can only accept '>=', '<=', '=', or a range ('[int]-[int]')")

def needsKWArgsSetup(command: str, neededkwargs: list[str]) -> Callable[..., bool]:
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
            if kwargs[arg] != None:
                if isinstance(kwargs['args'], list):
                    kwargs["args"].append(kwargs[arg])

                elif kwargs["args"] == None:
                    kwargs['args'] = [kwargs[arg]]
            kwargs[arg] = True
        except KeyError:
            kwargs[arg] = False

    return kwargs


#---------------------------------------------------

addonClasses: list = []

def importPlugins() -> None:
    config = importFromJSON(jsonPath)
    if config["addondir"] == "":
        return None
    os.chdir(Path.home())
    addondir = Path(config["addondir"]).resolve()
    os.chdir(curdir)


    global addonClasses

    for file in addondir.iterdir():
        if file.is_file() and file.suffix == ".cshplugin":
            with open(file, "r") as filecontent:
                exec(deCypher(deCypher(filecontent.read(), "alphabet", 13), "numeric", 3), globals())
                addonClasses.append(globals()[list(PluginRegistry.plugins.keys())[-1]](file.name))
                exec(f"{list(PluginRegistry.plugins.keys())[-1]}('{(file.name)}').run()", globals())

def managePlugins(**kwargs) -> None:
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
                addonClasses = []

                importPlugins()

#---------------------------------------------------

def SysStats(**kwargs) -> None:
    stats: dict[str, Any] = SystemStats()
    kwargs = defaultArgs({"-asciiversion": stats["osv"], "-asciiart": "windows"}, **kwargs)

    displayStats: dict[str, Any] = {"Windows Version": stats['osv'], "Kernel Build": stats['winv'], "Uptime": stats['uptime'], "Custom-Shell Version": Version("-"),
                    "CPU": f"{stats['cpu']['name']} @ {stats['cpu']['frequency']}", "GPU": stats['gpu'],
                    "Memory": f"{stats['memory']['used']} / {stats['memory']['total']}", "Disk": f"{stats['disk']['used']} / {stats['disk']['total']}"}

    tst = f"""
[green bold]Charl[/green bold]@[blue bold]{stats["hostname"]}[/blue bold]
{"-"*(len(f"Charl@{stats['hostname']}") + 4)}
 {"\n ".join([f"[blue bold]{stat}[/blue bold]: {val}" for stat, val in displayStats.items()])}"""

    if (kwargs['-asciiversion'] == '8' or kwargs['-asciiversion'] == '10') and kwargs['-asciiart'] == "windows": kwargs["-asciiversion"] = "8,10"

    cli.print(display.HorizontalLayout(f"{kwargs["-asciiart"]}-{kwargs['-asciiversion']}", "left").combineText(tst, "blue bold"))

def printPipeline(text: str) -> str:
    return text.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")

def showStartingPrints(startup : bool = False, **kwargs) -> None:
    if not startup:
        kwargs = booleanArgs(["r", "-reset"], **kwargs)
        if kwargs["r"] == True or kwargs["-reset"] == True:
            startup = True
    os.system("powershell clear")
    if startup:
        cli.print(f"  Welcome to the Custom Shell\nBy: [green][bold]Minemario64[/bold][/green]   Ver: [bold][red]{Version(" ")}[/red][/bold]")
        cli.print("\nType [bold][yellow]help all[/bold][/yellow] to find all the commands.")
        cli.print("Type [bold][yellow]help env[/bold][/yellow] to find all the environment variables.")
        cli.print("Type [bold][yellow]help *[/bold][/yellow] to find both the commands and the environment variables.")
        cli.print("═"*TERMINAL_WIDTH)
    cli.print()

def println(**kwargs) -> None:
    if not needsArgsSetup("print", 1)(**kwargs):
        return None

    kwargs = defaultArgs({"s": " ", "-color": None}, **kwargs)

    print(printPipeline(kwargs["s"].join(kwargs["args"])), style=kwargs["-color"])

def printFile(**kwargs) -> None:
    if not needsArgsSetup("cat", 1, "=")(**kwargs):
        return None

    if not Path(kwargs["args"][0]).is_file():
        cli.print("Cannot read a folder or a file that does not exist.")
        return

    with open(kwargs['args'][0], "r") as file:
        print(file.read().rstrip("\n"))

def execRunCom(filepath : Path, language : str) -> None:
    match language:
        case "python":
            runPyFile(**{"args": filepath})

        case "bin" | "exe":
            os.system(f"start '{filepath}'")

        case "web" | "website":
            os.system(f"start http://{filepath}")

        case "html":
            os.system(f"start '{filepath}'")

def runWConfig(**kwargs) -> None:
    if not needsArgsSetup("run", 1, "=")(**kwargs):
        return None

    config = importFromJSON(jsonPath)["run"]
    for runConfig in config:
        if runConfig["names"].__contains__(kwargs["args"][0]):
            execRunCom(Path(runConfig["path"]), runConfig["language"])

def webcutWConfig(**kwargs) -> None:
    if not needsArgsSetup("webcut", 1, "="):
        return None

    config = importFromJSON(jsonPath)["webcut"]
    for webConfig in config:
        if webConfig["names"].__contains__(kwargs["args"][0]):
            execRunCom(Path(webConfig["url"]), "website")

def listdir(**kwargs) -> None:
    try:
        kwargs["ps"]
        os.system("powershell ls")
        return

    except KeyError:
        pass

    kwargs = defaultArgs({"t": "all", "s": " "*2, "-folder-color": "blue bold", "-file-color": None}, **kwargs)
    kwargs["s"] = kwargs["s"].replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")
    kwargs = booleanArgs(['a', "-all", "nq", "-noquote"], **kwargs)
    path = curdir
    if kwargs['args'] != None:
        path = Path(kwargs['args'][0]).resolve()
        if not path.is_dir():
            cli.print("Cannot list all files of a file or a directory that does not exist.")

    def checkPath(path: Path, mode: int) -> bool:
        try:
            if path.is_dir():
                os.scandir(str(path))

            if path.is_file():
                if path.parent == Path.home() and path.name.lower().startswith("ntuser"):
                    return False

                path.read_bytes()

            match mode:
                case 0:
                    if is_hidden(path):
                        return False

                    return True

                case 1:
                    return True

                case _:
                    raise ValueError(f"mode cannot be {mode}, it can either be 1 or 0.")

        except PermissionError:
            return False

    folders = []
    files = []
    for file in (p for p in path.iterdir() if checkPath(p, int(kwargs['a'] or kwargs['-all']))):
        if file.is_dir():
            folders.append((f'"{file.name}"' if file.name.__contains__(" ") else file.name) if not (kwargs["nq"] or kwargs["-noquote"]) else file.name)

        elif file.is_file():
            files.append((f'"{file.name}"' if file.name.__contains__(" ") else file.name) if not (kwargs["nq"] or kwargs["-noquote"]) else file.name)

    match kwargs["t"]:
        case "all":
            if len(folders) > 0:
                print(f"{kwargs["s"].join(folders)}", end=kwargs["s"], style=kwargs["-folder-color"])

            if len(files) > 0:
                print(f"{kwargs["s"].join(files)}", style=kwargs["-file-color"])

        case "files" | "file" | "f":
            print(f"{kwargs["s"].join(files)}", style=kwargs["-file-color"])

        case "folders" | "dirs" | "folder" | "dir" | "d":
            print(f"{kwargs["s"].join(folders)}", style=kwargs["-folder-color"])

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
    if not needsArgsSetup("notepad", 1, "<=")(**kwargs):
        return None

    os.system(f'notepad{f' {kwargs["args"][0]}' if kwargs["args"] != None else ""}')

def changeDir(**kwargs) -> None:
    global curdir
    if kwargs["args"] == None:
        cli.print(curdir)
        return None

    if not Path(kwargs["args"][0]).is_dir():
        cli.print(f"'{kwargs['args'][0]}' is a file or does not exist.")
        return

    os.chdir(kwargs["args"][0])
    curdir = Path.cwd()

def makeAndChangeDir(**kwargs) -> None:
    global curdir
    if not needsArgsSetup("mcd", 1, "=")(**kwargs):
        return None

    path = Path(kwargs['args'][0]).resolve()
    path.mkdir(parents=True)
    os.chdir(kwargs['args'][0])
    curdir = Path.cwd()

def executeFile(**kwargs) -> None:
    if kwargs["args"] == '':
        cli.print("The command execute needs an argument.")
        return None

    os.system(f'powershell ./{kwargs["args"]}')

def runPyFile(**kwargs) -> None:

    config = importFromJSON(jsonPath)
    if not config["needpypath"]:
        os.system(f'{config["pycommand"]}{f' {kwargs["args"]}' if not kwargs["args"] == '' else ''}')
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

    with open(kwargs["args"][0], "rb") as file:
        fileContent = file.read()

    for file in kwargs["args"][1:]:
        with open(file, "wb") as newFile:
            newFile.write(fileContent)

def removeContent(**kwargs) -> None:
    kwargs = booleanArgs(["rf"], **kwargs)
    if not needsArgsSetup("remove", 1)(**kwargs):
        return None

    if kwargs["rf"]:
        for folder in kwargs['args']:
            os.system(f"powershell Remove-Item -Path {folder} -Recurse -Force")
    else:
        for file in kwargs['args']:
            os.system(f"powershell Remove-Item -Path {file} -Force")

def changeConfig(**kwargs) -> None:
    kwargs = booleanArgs(["u", "-update", "f", "-file"], **kwargs)
    if kwargs["u"] or kwargs["-update"]:
        for var, val in configUpdates.items():
            print(f"Updating {var}..." if var != "$func" else f"Running {val}...")
            if var == "$func":
                exec(val)
                print(f"Ran {val}")
                continue

            exec(f"{var} = {val}")
            print(f"Updated {var}")
        return

    if not needsArgsSetup("config", 2, "1-2")(**kwargs):
        return

    json = importFromJSON(jsonPath)
    jsonCopy = json.copy()
    kwargs["args"][0] = kwargs['args'][0].replace(str(ENVIRONMENT_VARS["~"]), "~")

    names = [name for name in json.keys()]
    if not names.__contains__(kwargs['args'][0]):
        cli.print("Invalid config field.")
        return

    if len(kwargs["args"]) == 1:
        inp = ''
    else:
        inp = kwargs["args"][1]

    try:
        if configTypes[kwargs["args"][0]] == "managed":
            cli.print(f"The config field '{kwargs["args"][0]}' is managed by another command.")
            return

        types = configTypes[kwargs["args"][0]].split('/')

    except KeyError:
        cli.print(configTypes[kwargs["args"][0]])
        cli.print("Cannot configure a field not added by Custom-Shell.")
        return

    for type in types:
        match type:
            case "":
                if inp == '':
                    json[kwargs["args"][0]] = ""

            case "bool":
                if inp.lower() == "false":
                    json[kwargs["args"][0]] = False
                    continue

                if inp.lower() == "true":
                    json[kwargs["args"][0]] = True
                    continue

            case "dirpath":
                if Path(inp).is_dir():
                    json[kwargs["args"][0]] = str(Path(inp).resolve(True))
                    continue

            case "str":
                json[kwargs["args"][0]] = inp

            case _:
                if DEBUG:
                    cli.print(f"Type '{type}' is currently not supported by config.")

    if json == jsonCopy:
        cli.print(f"Cannot set field '{kwargs['args'][0]}' to a value of '{inp}'. The said field can only be set to a {", ".join([f"{"a " if i != len(types) - 1 else "or a "}{configTypeUsr[type]}" for i, type in enumerate(types)])}.")
        return

    exportToJSON(json, jsonPath)

helpCommand = Command(["help"], lambdaWithKWArgsSetup(lambda kwargs: showHelp(commands, **kwargs)), {"name": "help", "description": "lets you know how to use a command and what that command does.", "has-kwargs": False})

def showHelp(commands : list[Command], prefix: str = '', **kwargs) -> None:
    commandNames = [command.names for command in commands]
    if kwargs["args"] == None:
        if prefix == '':
            commands[commands.index(helpCommand)].help(prefix)

        else:
            commands[indexIntoLayeredList(commandNames, "help")].help(prefix)

        return None

    if prefix == '':
        r = False
        if kwargs["args"][0] == "all" or kwargs["args"][0] == "*":
            print(f"\t[bold][cyan]all commands[/bold][/cyan]\n\n[bold][green]{"[/green], [green]".join([command.names[0] for command in commands])}[/green]\n\tRun [yellow]help {"\\[command]"}[/yellow] to learn more.[/bold]")
            r = True

        if kwargs["args"][0] == "*":
            print("\n-------------------------------------------------------------------------")

        if kwargs["args"][0] == "env" or kwargs["args"][0] == "*":
            print(f"\t[bold][cyan]environment variables[/bold][/cyan]\n\n[bold]{"\n".join([f"[yellow]{k}[/yellow]: [green]{repr(v)}[/green]" for k, v in ENVIRONMENT_VARS.items()])}[/bold]")
            r = True

        if r:
            return

    else:
        if kwargs["args"][0] == "all":
            print(f"\t[bold][cyan]all commands[/bold][/cyan]\n\n[bold][green]{"[/green], [green]".join([command.names[0] for command in commands])}[/green]\n\tRun [yellow]help {"\\[command]"}[/yellow] to learn more.[/bold]")
            return

    if flatten(commandNames).__contains__(kwargs["args"][0]):
        commands[indexIntoLayeredList(commandNames, kwargs["args"][0])].help(prefix)

def sysCommand(**kwargs) -> None:
    os.system(kwargs["args"])

def psCommand(**kwargs) -> None:
    kwargs["args"] = f"powershell {kwargs["args"]}"
    sysCommand(**kwargs)

def cmdCommand(**kwargs) -> None:
    kwargs["args"] = f"cmd /c {kwargs["args"]}"
    sysCommand(**kwargs)

def execCommand(**kwargs) -> None:
    comm.run(kwargs['args'].strip())

def ManageProj(**kwargs) -> None:

    def run(**kwargs) -> None:
        path = curdir.parent.joinpath(f"{curdir.name}:language")
        if not path.exists():
            cli.print("Cannot run commands while not in a project.")
            return

        with path.open("r", encoding="utf-8") as stream:
            projVer = stream.readline()
            if projVer.startswith("1.0"):
                lang = langs[stream.readline().removeprefix("Language: ")]
                runCommand(kwargs['args'].split(" ")[0], lang, kwargs['args'].split(" ")[1:])

    def addProj(**kwargs) -> None:
        if not needsArgsSetup("mkproj", 2, "2-3")(**kwargs):
            return

        if len(kwargs["args"]) == 2:
            langs[kwargs["args"][0]].makeProject(Path(kwargs["args"][1]))

        else:
            langs[kwargs["args"][0]].makeProject(Path(kwargs["args"][1]), kwargs["args"][2])

    def makeTmplate(**kwargs) -> None:
        if not needsArgsSetup("mktmp", 3, "2-3")(**kwargs):
            return

        try:
            langs[kwargs["args"][0]]

        except KeyError:
            cli.print(f"'{kwargs['args'][0]}' is not a created language.")

        path = Path(kwargs["args"][1])
        if not path.is_dir():
            cli.print(f"Cannot make a Template with a file or a directory that does not exist.")
            return

        if len(kwargs["args"]) == 3:
            if not langs[kwargs["args"][0]].makeTemplate(path, kwargs["args"][2]):
                cli.print("Failed to make template.")

        else:
            if not langs[kwargs["args"][0]].makeTemplate(path):
                cli.print("Failed to make template.")

    def addLang(**kwargs) -> None:
        if not needsArgsSetup("add", 2, "="):
            return

        kwargs = booleanArgs(["s", "-suspend"], **kwargs)

        config = importFromJSON(configPath)
        config["languages"][kwargs['args'][0]] = kwargs["args"][1]
        langs[kwargs["args"][0]] = Language(kwargs["args"][0], kwargs["args"][1])
        lang = langs[kwargs["args"][0]]
        if not (kwargs['s'] or kwargs['-suspend']):
            lang.init()

        exportToJSON(config, configPath)

    projCommands = []

    @lambda _: _()
    def loadCommands():
        projCommands.append(Command(["run"], run, {"name": "run", "description": "Runs a Project command.", "has-kwargs": False}, 'base-split'))
        projCommands.append(Command(["version", "ver"], lambda: cli.print(f"[bold][red]{Version("-")}[/bold][/red]"), {"name": "version", "description": "Prints the version of the Custom-Shell Project Manager", "has-kwargs": False}))

        projCommands.append(Command(["makeproject", "makeproj", "mkproject", "mkproj"], addProj, {"name": "make-project", "description": "Makes a project based on the language and project template you give.", "has-kwargs": False}))
        projCommands.append(Command(["help"], lambdaWithKWArgsSetup(lambda kwargs: showHelp(projCommands, "pm ", **kwargs)), {"name": "help", "description": "lets you know how to use a Custom-Shell Project Manager command and what that command does.", "has-kwargs": False}))
        projCommands.append(Command(['maketemplate', 'mktemplate', 'maketmp', 'mktmp'], makeTmplate, {"name": "make-template", "description": "Makes a template with a given language, a given directory, and a given name.", "has-kwargs": False}))
        projCommands.append(Command(['add', "lang", "addlang"], addLang, {"name": "add-language", "description": "Adds a Language with the given name and file extension.", "has-kwargs": True, "kwargs": {"-s / -suspend": "Suspends the language from initializing until the next time you run this shell."}}))

    comM = CommandManager(projCommands)
    comM.run(kwargs["args"])

def bookmark(**kwargs) -> None:
    if not needsArgsSetup("bookmarks", 2, "1-3")(**kwargs):
        return

    match kwargs["args"][0]:
        case "add":
            json = importFromJSON(jsonPath)
            if len(kwargs["args"]) == 3 and not Path(kwargs["args"][2]).is_dir():
                cli.print("Cannot set a bookmark to a file or a directory that does not exist.")

            json["bookmarks"][kwargs["args"][1]] = str(Path.cwd() if len(kwargs["args"]) == 2 else Path(kwargs["args"][2]).resolve())
            exportToJSON(json, jsonPath)

        case "goto":
            json = importFromJSON(jsonPath)
            if not list(json["bookmarks"].keys()).__contains__(kwargs["args"][1]):
                cli.print("Invalid bookmark name.")

            changeDir(**{"args": [json["bookmarks"][kwargs["args"][1]]]})

        case "list":
            json = importFromJSON(jsonPath)
            kwargs = defaultArgs({"s": " "*2, "-color": "bold cyan"}, **kwargs)
            print(kwargs["s"].join(list(json["bookmarks"].keys())), style=kwargs["-color"])

        case "dir":
            json = importFromJSON(jsonPath)
            if not list(json["bookmarks"].keys()).__contains__(kwargs["args"][1]):
                cli.print("Invalid bookmark name.")

            print(json["bookmarks"][kwargs["args"][1]])

        case _:
            cli.print("Invalid Mode. Modes can be either 'add', 'goto', or 'list', 'dir'.")

def crypt(**kwargs) -> None: # pyright: ignore[reportRedeclaration]

    def dupWidth(text: str, width: int) -> str:
        repeating, part = divmod(width, len(text))
        return (text*repeating) + text[0:part]

    def encypher(data: bytes, amount: int) -> bytes:
        if amount < -255 or amount > 255 or (not isinstance(amount, int)):
            raise ValueError("Cannot encypher - amount must be an integer from -255 to 255")

        return bytes([(byte + amount) % 256 for byte in data])

    def encrypt(data: bytes, key: str) -> bytes:
        p1: bytes = bytes([x ^ y for x, y in zip(data, bytes(dupWidth(key, len(data)), "utf-8"))])
        result: bytes = bytes([x ^ y for x, y in zip([len(data) % 256 for _ in range(len(data))], p1)])
        return result

    def decrypt(content: bytes, key: str) -> bytes:
        return bytes([(x ^ y) ^ z for x, y, z in zip(content, [len(content) % 256 for _ in range(len(content))], bytes(dupWidth(key, len(content)), 'utf-8'))])

    kwargs: dict = booleanArgs(["e", "d"], **kwargs)

    if not needsArgsSetup("crypt", 1):
        return

    path: Path = Path(kwargs['args'][0])

    if not path.is_file():
        cli.print(f"'{path}' is a directory or it doesn't exist")

    if kwargs["e"]:

        key: str = getpass("Encryption Key: ")

        with path.open("rb") as unencryptedFile:
            unencryptedText = unencryptedFile.read()

        encryptedText = encrypt(unencryptedText, key)

        try:
            filepath: Path = Path(kwargs['f'])
            filepath.touch()
            with filepath.open("wb") as encryptedFile:
                encryptedFile.write(encryptedText)

        except KeyError:
            while True:
                inp = input("This will override the original file. Do you want to continue (y/n): ")
                if inp.lower() in ['y', "yes"]:
                    break

                if inp.lower() in ["n", "no"]:
                    print("Cancelling...")
                    return

                print("You need to ether y, n, yes, or no.")
                time.sleep(1)

            with path.open("wb") as encryptedFile:
                encryptedFile.write(encryptedText)

    if kwargs['d']:
        key: str = getpass("Encryption Key: ")

        with path.open("rb") as encryptedFile:
            content = encryptedFile.read()

        unencryptedContent = decrypt(content, key)

        try:
            filepath: Path = Path(kwargs['f'])
            filepath.touch()
            with filepath.open("wb") as encryptedFile:
                encryptedFile.write(unencryptedContent)

        except KeyError:
            while True:
                inp = input("This will override the original file. Do you want to continue (y/n): ")
                if inp.lower() in ['y', "yes"]:
                    break

                if inp.lower() in ["n", "no"]:
                    print("Cancelling...")
                    return

                print("You need to ether y, n, yes, or no.")
                time.sleep(1)

            with path.open("wb") as encryptedFile:
                encryptedFile.write(unencryptedContent)

def initRecording(comM: CommandManager) -> None:
    def record(**kwargs):
        global recordedCommands
        if not needsArgsSetup("record", 1, "<=")(**kwargs):
            return None

        kwargs = booleanArgs(["l"], **kwargs)
        kwargs = defaultArgs({"f": None}, **kwargs)

        if kwargs["l"]:
            print("\n".join(recordedCommands))

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

    comM.commands.append(Command(["record"], record, {"name": "record", "description": "Records Your commands to save as a .csh file.", "has-kwargs": True, "kwargs": {"-l": "Lists all currently recorded commands", "-f": "Saves the recorded commands in given filepath as a .csh file"}}))
    comM.commandNames = [command.names for command in comM.commands]

#--------------------

commands: list[Command] = []

comm = CommandManager(commands)

def runShellFile(filepath : Path) -> None:
    with filepath.open("r") as file:
        commands = [command for command in file.read().split("\n") if len(command) > 0]

    for command in commands:
        comm.run(command.strip(" "))

@runImmediately
def initCommands() -> None:
    commands.append(Command(["print", 'echo'], println, {"name": "print", "description": "Prints the arguments you give it.", "has-kwargs": True, "kwargs": {"-s": "Separating string between each argument", "--color": "Style the printed text"}}))
    commands.append(Command(["exit", "stop"], lambda: os._exit(0), {"name": "exit", "description": "Exits the terminal.", "has-kwargs": False}))

    commands.append(Command(["cat", "read", "printf"], printFile, {"name": "read-file", "description": "Prints the contents of a file.", "has-kwargs": False}))

    commands.append(Command(["clear", "cls"], showStartingPrints, {"name": "clear", "description": "Clears the terminal.", "has-kwargs": True, "kwargs": {"-r": "Loads the starting text after clearing the screen."}}))
    commands.append(Command(["list", "ls"], listdir, {"name": "list", "description": "Lists all files in the current directory.", "has-kwargs": True, "kwargs": {"-ps": "Runs the powershell version of ls instead of the shell's version", "-t": "Filter to both files and folders 'all', only files 'files', or only folders 'folders'", "--folder-color": "Styles the color of the names of the folders", "--file-color": "Styles the color of the names of the files", "-a / --all": "Lists all files even if they are hidden", "-nq / --noquote": "Doesn't add quotes to directory names if they have spaces"}}))

    commands.append(Command(["makefile", "mkf", "touch"], makeFile, {"name": "touch", "description": "Makes files.", "has-kwargs": False}))
    commands.append(Command(["makedir", "mkdir"], makeDir, {"name": "makedir", "description": "Makes directories.", "has-kwargs": False}))

    commands.append(Command(["vscode", "code"], openVSCode, {"name": "vscode", "description": "Opens the given file or folder in vscode.", "has-kwargs": False}))
    commands.append(Command(["website", "web"], openWebsite, {"name": "website", "description": "Opens the given websites in your default browser.", "has-kwargs": False}))

    commands.append(Command(["wait", "sleep"], wait, {"name": "sleep", "description": "Waits the given amount of time.", "has-kwargs": True, "kwargs": {"--format": "Takes the given argument and gives it a different unit of time: 'secs', 'mins'"}}))
    commands.append(Command(["notepad", "note", "txt"], openNotepad, {"name": "notepad", "description": "Opens a file in notepad.", "has-kwargs": False}))

    commands.append(Command(["execute", "start", "exe"], executeFile, {"name": "execute", "description": "Runs an executable file", "has-kwargs": False}, 'base-split'))
    commands.append(Command(["cd"], changeDir, {"name": "changedir", "description": "Changes the current directory.", "has-kwargs": False}))
    commands.append(Command(["mcd"], makeAndChangeDir, {"name": "makedir-changedir", "description": "Makes the given path as a directory and changes the current directory", "has-kwargs": False}))

    commands.append(Command(["python", "python3", "py"], runPyFile, {"name": "python", "description": "Runs a python file.", "has-kwargs": False}, 'base-split'))
    commands.append(Command(["html"], runHTML, {"name": "html", "description": "Runs the given HTML files.", "has-kwargs": False}))

    commands.append(Command(["rename", "ren"], renameFile, {"name": "rename", "description": "Renames a given file.", "has-kwargs": False}))
    commands.append(Command(["copy"], copyFile, {"name": "copy", "description": "Copies the contents of a text file to the other given files.", "has-kwargs": False}))

    commands.append(Command(["remove", "rm"], removeContent, {"name": "remove", "description": "Removes a file or folder and all it's content.", "has-kwargs": False}))
    commands.append(Command(["run"], runWConfig, {"name": "run", "description": "Runs a set file via a config.", "has-kwargs": False}))

    commands.append(Command(["webcut", "webc"], webcutWConfig, {"name": "webcut", "description": "Opens up a set website via a config.", "has-kwargs": False}))
    commands.append(Command(["version", "ver"], lambda: print(f"[bold][red]{Version(" ")}[/bold][/red]"), {"name": "version", "description": "Prints the current version of the shell.", "has-kwargs": False}))

    commands.append(Command(["addons"], managePlugins, {"name": "addons", "description": "Manages all imported addons.", "has-kwargs": True, "kwargs": {"-l": "Lists the currently imported addons."}}))
    commands.append(Command(["system", "sys"], sysCommand, {"name":"system", "description": "Runs the given system command.", "has-kwargs": False}, "base-split"))

    commands.append(Command(["powershell", "ps"], psCommand, {"name": "system-powershell", "description": "Runs the given system command in powershell.", "has-kwargs": False}, 'base-split'))
    commands.append(Command(["cmd"], cmdCommand, {"name": "system-cmd", "description": "Runs the given system command in command prompt.", "has-kwargs": False}, 'base-split'))

    commands.append(Command(["config"], changeConfig, {"name": "configure", "description": "Changes the config file", "has-kwargs": True, "kwargs": {"-u / -update": "Updates all the items that use the config fields."}}))
    commands.append(Command(['csh', 'shell', 'sh'], lambdaWithArgsSetup(runShellFile), {'name': 'shell', 'description': 'Runs a .csh file', 'has-kwargs': False}))

    commands.append(Command(["project", "projmanager", "manager", "proj", "pm"], ManageProj, {"name": "project-manager", "description": "Runs the Custom-Shell Project Manager CLI.", "has-kwargs": False}, 'base-split'))
    commands.append(Command(["bookmarks", "marks"], bookmark, {"name": "bookmarks", "description": "Manages bookmarks, allowing you to add, go to, and list your bookmarks.", "has-kwargs": True, "kwargs": {"-s": "When listing bookmarks, this is used for the separating characters between bookmarks", "--color": "When listing bookmarks, this is used to style the bookmarks."}}))

    commands.append(Command(["release"], lambda: release(), {"name": "release", "description": "Runs all the commands that were redirected to hold.", "has-kwargs": False}))
    commands.append(Command(["neofetch", "sysinfo"], SysStats, {"name": "system-info", "description": "Prints the system info of your computer.", "has-kwargs": False}))
    commands.append(Command(["crypt", "gpg", "enc"], crypt, {"name": "Crypt", "description": "Encrypts and decrypts files, with gpg like syntax.", "has-kwargs": True, "kwargs": {"-e": "Encryption mode (encrypts the file)", "-d": "Decryption mode", "-f": "Makes the result be saved in a different file"}}))
    commands.append(Command(["exec", "execute", "com", "command"], execCommand, {"name": "execute", "description": "Executes the command that you give it", "has-kwargs": False}, 'base-split'))
    commands.append(helpCommand)

def showCWDAndGetInput() -> str:
    cli.print(f"[blue]{ENVIRONMENT_VARS["%USER%"]}@{HOSTNAME}[/blue]:[green3]{(str(curdir).replace(str(Path.home()), "~")) if importFromJSON(jsonPath)["~:Home"] else curdir}{str(b"\x00", 'ascii')}[green3][magenta]$", end=' ', style='bold')
    return cli.input('')

def inputLoop(comM: CommandManager) -> None:
    while True:
        ui = showCWDAndGetInput()
        comM.run(ui.strip(" "))

def changeToInterpreter(comM: CommandManager):
    commands.insert(-1, Command(["startinput"], lambda: inputLoop(comM), {"name": "startinput", "description": "Starts the user input from a .csh file.", "has-kwargs": False}))
    comM.commands = commands
    comM.commandNames = [command.names for command in comM.commands]

importPlugins()

configUpdates = {"comm.aliases": "{alias: command for alias, command in importFromJSON(jsonPath)['aliases'].items()}",
                 "cli": "Console(highlight=importFromJSON(jsonPath)[\"Auto-Highlighting\"])",
                 "envVars[\"PYDIR\"]": "PathVar(str(Path(importFromJSON(jsonPath)[\"pypath\"]))) if importFromJSON(jsonPath)[\"needpypath\"] else StrVar(''),",
                 "ENVIRONMENT_VARS": "{f\"%{name}%\": value for name, value in envVars.items()} | {\"~\": PathVar(str(Path.home()))}",
                 "comm.vars": "ENVIRONMENT_VARS | {f\"%{dct[\"name\"]}\": TypeRegistry.types[TypeRegistry.nicknames[dct['type']]](TypeRegistry.types[TypeRegistry.nicknames[dct['type']]].__jload__(jsonTypesToBytes(dct[\"data\"]))) for dct in importFromJSON(jsonPath)['vars']}",
                 "$func": "comm.run('addons restart all')"
}