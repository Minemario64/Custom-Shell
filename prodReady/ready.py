ver = [1, 2, 0, ""]

version = (".".join([str(num) for num in ver[0:3]]), ver[3])
def Version(sep: str) -> str:
    return f"{version[0]}{sep}{version[1]}" if version[1] != '' else version[0]

DEBUG: bool = True
GUIC: bool = False

import os
import time
if not GUIC:
    from rich.console import Console
    from rich.text import Text
from pathlib import Path
from json import load, dumps, dump
import inspect
import re
def PMVer(sep: str) -> str:
    ver = [1, 0, 0, ""]
    version = (".".join([str(num) for num in ver[0:3]]), ver[3])
    return f"{version[0]}{sep}{version[1]}" if version[1] != '' else version[0]



from pathlib import Path
from json import load, dumps, dump
import win32file
import win32con
import os

def importFromJSON(filename: str | Path) -> dict | None:
    filepath = Path(filename) if isinstance(filename, str) else filename
    if filepath.exists():
        with open(filepath, "r") as file:
            return load(file)

def exportToJSON(data: dict | list, filename: str | Path, indent : bool = True) -> None:
    filepath = Path(filename) if isinstance(filename, str) else filename
    if filepath.exists():
        if indent:
            with open(filepath, "w") as file:
                file.write(dumps(data, indent=4))
        else:
            with open(filepath, "w") as file:
                dump(data, file)

def flatten(l : list) -> list:
    newList : list = []
    for item in l:
        if not isinstance(item, list):
            newList.append(item)
        else:
            for extraItem in flatten(item):
                newList.append(extraItem)
    return newList

def indexIntoLayeredList(l : list, targetVal, start : bool = True, idxStart : int = 0) -> int | None:
    idx : int = 0 if start else idxStart
    for item in l:
        if (item == targetVal) and (type(item) == type(targetVal)):
            return idx
        if isinstance(item, list):
            itemResult = indexIntoLayeredList(item, targetVal, False, idx)
            if isinstance(itemResult, int):
                return itemResult
        idx += 1 if start else 0
    return None

def hidePath(path: Path) -> None:
   if path.exists():
       flags = win32file.GetFileAttributes(str(path))
       win32file.SetFileAttributes(str(path), win32con.FILE_ATTRIBUTE_HIDDEN | flags)

home = Path.home()
globalCommandsPath = home.joinpath(".codeCommands/")
globalTemplatesPath = home.joinpath(".codeTemplates/")
configPath = globalTemplatesPath.joinpath(".config")

LANG_LOOKUP = {
    "python": "python ",
    "exe": "./",
}

class Language:

    def __init__(self, name: str, fileExtension: str) -> None:
        self.name = name
        self.fileExtension = fileExtension

    @property
    def commandsPath(self) -> Path:
        return globalCommandsPath.joinpath(self.fileExtension)

    @property
    def templatesPath(self) -> Path:
        return globalTemplatesPath.joinpath(self.fileExtension)

    def init(self) -> None:
        self.commandsPath.mkdir(exist_ok=True)
        self.commandsPath.joinpath("metadata.json").touch()
        exportToJSON({}, self.commandsPath.joinpath("metadata.json"))

        self.templatesPath.mkdir(exist_ok=True)
        self.templatesPath.joinpath("default").mkdir(exist_ok=True)

    def makeTemplate(self, directory: Path, name: str = "default", overwrite: bool = True) -> bool:
        """Makes a language template

        Args:
            directory (Path): The directory of the template to copy.
            name (str, optional): The name of the template to save as. Defaults to "default".
            overwrite (bool, optional): Overwrite the template if there is already one with the same name. Defaults to True.

        Returns:
            bool: If the template was able to be added.
        """
        templatePath = self.templatesPath.joinpath(name)
        if templatePath.exists():
            if overwrite:
                os.system(f'powershell Remove-Item -Path "{templatePath}" -Recurse -Force')

            else:
                return False

        templatePath.mkdir()
        os.system(f'powershell Copy-Item -Path "{directory}" -Destination "{templatePath}" -Recurse')

    def makeProject(self, projectPath: Path, templateName: str = 'default') -> None:
        """Makes a project from a given template

        Args:
            projectPath (Path): The path of the project
            templateName (str, optional): The name of the template to copy from. Defaults to 'default'.
        """
        if not self.templatesPath.joinpath(templateName).exists():
            raise ValueError("Cannot make a project with a template that doesn't exist")

        os.system(f'powershell Copy-Item -Path "{self.templatesPath.joinpath(templateName)}" -Destination "{projectPath}" -Recurse')

        with open(f"{projectPath.absolute().resolve()}:language", "x", encoding="utf-8") as stream:
            stream.write(f"{PMVer("-")}\nLanguage: {self.name}")

    def addCommand(self, filepath: Path, language: str, nicknames: list[str]) -> None:
        with filepath.open("rb") as file:
            content = file.read()

        with self.commandsPath.joinpath(filepath.name).open("wb") as file:
            file.write(content)

        json = importFromJSON(self.commandsPath.joinpath('metadata.json'))
        json[filepath.name] = {"names": [filepath.name] + nicknames, "language": language}

        exportToJSON(json, self.commandsPath.joinpath("metadata.json"))

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Language: {self.name} | .{self.fileExtension}>"

def runCommand(command: str, language: Language, args: list[str]) -> bool | None:
    names = [v["names"] for v in importFromJSON(language.commandsPath.joinpath("metadata.json")).values()]
    objs = list(importFromJSON(language.commandsPath.joinpath("metadata.json")).items())
    if not flatten(names).__contains__(command):
        return False

    obj = objs[indexIntoLayeredList(names, command)]
    os.system(f"powershell {LANG_LOOKUP[obj[1]["language"]]}{language.commandsPath.joinpath(obj[0]).resolve()} {" ".join(args)}")


if not globalCommandsPath.exists():
    globalCommandsPath.mkdir()
    hidePath(globalCommandsPath)

if not globalTemplatesPath.exists():
    globalTemplatesPath.mkdir()
    hidePath(globalTemplatesPath)

defaultConfig = {"languages": {}, "command-languages": {}}

def updateConfig() -> None:
    config = importFromJSON(configPath)
    result = {}
    for setting, default in defaultConfig.items():
        try:
            config[setting]
            result[setting] = config[setting]

        except KeyError:
            result[setting] = default

    exportToJSON(result, configPath)

if not configPath.exists():
    configPath.touch()
    exportToJSON(defaultConfig, configPath)

else:
    updateConfig()

LANG_LOOKUP = LANG_LOOKUP | importFromJSON(configPath)["command-languages"]

langs: dict[str, Language] = {name: Language(name, ext) for name, ext in importFromJSON(configPath)["languages"].items()}

for lang in langs.values():
    if not (lang.commandsPath.exists() and lang.commandsPath.exists()):
        lang.init()
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
        sys.__stdout__.write(data)

    def clear(self):
        os.system("powershell clear")

    def flush(self):
        sys.__stdout__.flush()

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
import struct
from pathlib import Path

class TypeRegistry(type):
    types: dict = {}
    nicknames: dict[str:str] = {}

    def __new__(cls, name, bases, dct):

        try:
            TypeRegistry.types[name]

        except KeyError:
            newTypeClass = super().__new__(cls, name, bases,  dct)

            try:
                TypeRegistry.nicknames[dct['name']] = name
                TypeRegistry.types[name] = newTypeClass

            except KeyError:
                pass

            return newTypeClass

class VarType(metaclass=TypeRegistry):

    def __init__(self, text: str) -> None:
        raise NotImplementedError

    def __str__(self) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:
        raise NotImplementedError

    def __json__(self) -> bytes:
        raise NotImplementedError

    @staticmethod
    def __jload__(data: bytes) -> str:
        raise NotImplementedError

class StrVar(VarType):
    name: str = 'str'

    def __init__(self, text: str):
        self.value = text

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"'{self.value}'"

    def __json__(self) -> bytes:
        return bytes(self.value, encoding="utf-8")

    @staticmethod
    def __jload__(data: bytes) -> str:
        return data.decode()

class PathVar(VarType):
    name: str = 'path'

    def __init__(self, text: str) -> None:
        self.value = Path(text).resolve()

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return self.__str__()

    def __json__(self) -> bytes:
        return bytes(str(self.value), encoding="utf-8")

    @staticmethod
    def __jload__(data: bytes) -> str:
        return data.decode()

class IntVar(VarType):
    name: str = 'int'

    def __init__(self, text: str) -> None:
        self.value = int(text)

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return self.__str__()

    def __json__(self) -> bytes:
        return bytes([self.value])

    @staticmethod
    def __jload__(data: bytes) -> str:
        return str(int(data.hex(), 16))

class FloatVar(VarType):
    name: str = 'float'

    def __init__(self, text: str) -> None:
        self.value = float(text)

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return self.__str__()

    def __json__(self) -> bytes:
        return struct.pack("d", self.value)

    @staticmethod
    def __jload__(data: bytes) -> str:
        return str(struct.unpack('d', data))
import shutil
if GUIC:
    import threading as thr
    from typing import Literal
    import atexit
    
    class ConsoleQueuePacket:
    
        def __init__(self, mode: Literal['print', 'input', 'clear'], /, *args, **parameters) -> None:
            self.mode = mode
            self.args = args
            if mode == 'print':
                self.parameters = parameters if parameters else {'sep': ' ', 'end': '\n', 'style': None}
            else:
                self.parameters = parameters
    
    class ConsoleQueue:
    
        def __init__(self) -> None:
            self.queue: list[ConsoleQueuePacket] = []
            self.returnQueue: str | None = None
    
        def __len__(self) -> int:
            return len(self.queue)
    
        def addQueue(self, packet: ConsoleQueuePacket) -> None:
            self.queue.append(packet)
    
        def getItem(self) -> ConsoleQueuePacket:
            return self.queue.pop(0)
    
        def getReturnedStr(self) -> str | None:
            return self.returnQueue
    
    class KillFlag:
    
        def __init__(self) -> None:
            self._flag = False
    
        def kill(self) -> None:
            self._flag = True
    
        def is_alive(self) -> bool:
            return not self._flag
    
    def parseStyles(styles: str) -> list[str]:
        result: list[str] = []
        bg: bool = False
        for style in [style for style in styles.split(" ") if style != '']:
            match style:
                case 'underline':
                    if len(result) == 0:
                        result.append('underline')
                        continue
    
                    if result[-1] == 'default':
                        result[-1] = 'underline'
                        continue
    
                    result[-1] = f"{result[-1]}-underline"
    
                case 'on':
                    bg = True
    
                case _:
                    if bg:
                        result.append(f"{style}-bg")
                        bg = False
                        continue
    
                    result.append(style)
    
        return result
    
    def parseColoredPrint(text: str, globalStyle: str = '') -> list[str | tuple[str, str]]:
        instyle = False
        style = ""
        styles = ['']
    
        for char in text:
            if char == '[':
                instyle = True
            elif char == ']':
                instyle = False
                if style.startswith("/"):
                    if styles[-1][0].__contains__(style.removeprefix("/")):
                        if not styles[-1][0] == style.removeprefix("/"):
                            styles.append([styles[-1][0].replace(style.removeprefix("/"), " ").strip(' '), ''])
                        else:
                            styles.append('')
    
                elif isinstance(styles[-1], list):
                    if styles[-1][1] == '':
                        styles[-1][0] += f" {style}"
                    else:
                        styles.append([f"{styles[-1][0]} {style}", ''])
                else:
                    styles.append([f'{f'{globalStyle} ' if globalStyle != '' else ''}{style}', ''])
                style = ''
            else:
                if instyle:
                    style += char
                else:
                    if isinstance(styles[-1], list):
                        styles[-1][1] += char
                    else:
                        styles[-1] += char
    
        styles = [tuple(stylePart) if isinstance(stylePart, list) else stylePart for stylePart in styles]
        if globalStyle != '':
            styles = [(globalStyle, text) if isinstance(text, str) else text for text in styles]
    
        return styles
    
    tagColors: tuple[dict[str: str], dict[str: str]] = ({'red': '#DF2F00', 'green': '#20D220', "blue": '#0A70FF', 'yellow': '#CFCF00', 'cyan': "#00CAC0", "orange": "#CF7000", "magenta": "#B000B0", "purple": "#802AD0", "white": "#DDD", "lime": "#5C5", 'black': '#000000', 'grey': '#777'},
                                                        {'red': '#FF4D22', 'green': '#40F240', "blue": '#10A0F0', 'yellow': "#FFFF00", 'cyan': "#1AFFCF", "orange": "#F0A000", "magenta": "#EA00EA", "purple": "#A000F0", "white": "#FFF", "lime": "#9F9", 'black': '#2A2A2A', 'grey': '#AAA'})
    
    from pathlib import Path
    import re
    
    class Console:
    
        _allConsoles: list = []
    
        @atexit.register
        def closeAllConsoles():
            for console in Console._allConsoles:
                console.closeConsole()
    
        def __init__(self, consoleName: str = 'Console', /, geometry: str = '800x450', icon: Path | None = None, bgColor: str = '#191919', defaultTextColor: str = '#FFF', font = ('Consolas', 12), boldStyle: Literal['width', 'brightness'] = 'width', colorTheme: tuple[dict[str: str], dict[str: str]] | None = None) -> None:
            def is_hexColor(s: str) -> bool:
                hex_pattern = re.compile(r"^#([0-9A-Fa-f]{3}){1,2}$")
                return hex_pattern.match(s)
    
            if not is_hexColor(bgColor):
                raise ValueError('bgColor needs to be a valid hex color value')
    
            if not is_hexColor(defaultTextColor):
                raise ValueError('defaultTextColor needs to be a valid hex color value')
    
            Console._allConsoles.append(self)
    
            self.__inputTextStack__: list[str] = []
            self.__inputString__: str = ""
            self.__getInput__: bool = False
    
            def _consoleThread(queue: ConsoleQueue, killFlag: KillFlag) -> None:
                import tkinter as tk
                from typing import Callable
                import os
                import sys
    
                def TextBoxEnable(textBox: tk.Text):
                    def decorator(func: Callable):
                        def wrapper(*args, **kwargs):
                                textBox.config(state='normal')
                                result = func(*args, **kwargs)
                                textBox.config(state='disabled')
                                if result != None:
                                    return result
    
                        return wrapper
                    return decorator
    
                def on_close():
                    root.destroy()
                    os._exit(0)
    
                root = tk.Tk()
                if icon != None:
                    root.iconbitmap(str(icon.absolute()))
                root.protocol("WM_DELETE_WINDOW", on_close)
                root.geometry(geometry)
                root.title(consoleName)
                root.config(bg=bgColor)
    
                textBox = tk.Text(root, bg=bgColor, fg=defaultTextColor, font=font, insertbackground=defaultTextColor, state='disabled')
                if isinstance(colorTheme, tuple):
                    colors = (tagColors[0] | (colorTheme[0] if isinstance(colorTheme[0], dict) else {}), tagColors[1] | (colorTheme[1] if isinstance(colorTheme[1], dict) else {}))
    
                else:
                    colors = tagColors
    
                for name, colorVal in colors[0].items():
                    textBox.tag_config(name, foreground=colorVal)
                    textBox.tag_config(f"{name}-bg", background=colorVal)
                    textBox.tag_config(f"{name}-underline", underlinefg=colorVal, underline=True)
    
                match boldStyle:
                    case 'width':
                        textBox.tag_config("bold", font=font + ('bold',))
    
                    case 'brightness':
                        for name, colorVal in colors[1].items():
                            textBox.tag_config(f"bright-{name}", foreground=colorVal)
                            textBox.tag_config(f"bright-{name}-bg", background=colorVal)
                            textBox.tag_config(f"bright-{name}-underline", underlinefg=colorVal, underline=True)
    
                textBox.tag_config('underline', underline=True)
    
                textBox.pack(fill=tk.BOTH, expand=True)
    
                def parseStyles(styles: str) -> list[str]:
                    result: list[str] = []
                    bg: bool = False
                    bold: bool = False
                    for style in [style for style in styles.split(" ") if style != '']:
                        match style:
                            case 'underline':
                                if len(result) == 0:
                                    result.append('underline')
                                    continue
    
                                if result[-1] == 'default':
                                    result[-1] = 'underline'
                                    continue
    
                                result[-1] = f"{result[-1]}-underline"
    
                            case 'on':
                                bg = True
    
                            case 'default':
                                bold = False
    
                            case 'bold':
                                bold = True
    
                            case _:
                                if bg:
                                    if bold:
                                        result.append(f"bright-{style}-bg")
    
                                    else:
                                        result.append(f"{style}-bg")
    
                                    bg = False
                                    continue
    
                                if bold:
                                    result.append(f"bright-{style}")
    
                                else:
                                    result.append(style)
    
                    return result
    
                class TkTextBoxStdout:
    
                    def __init__(self, TextBox: tk.Text) -> None:
                        self.textBox = TextBox
    
                    @TextBoxEnable(textBox)
                    def write(self, text: str, tags: str | None = None) -> None:
                        if tags != None and (text.__contains__('\n') and tags.split(' ').__contains__("on")):
                            for line in [ln for ln in text.split("\n") if ln != '']:
                                self.textBox.insert(tk.END, line, parseStyles(tags) if tags != None else None)
                                self.textBox.insert(tk.END, '\n')
                        else:
                            self.textBox.insert(tk.END, text, parseStyles(tags) if tags != None else None)
                        self.textBox.see(tk.END)
    
                    @TextBoxEnable(textBox)
                    def clear(self) -> None:
                        self.textBox.delete("1.0", tk.END)
    
                    @TextBoxEnable(textBox)
                    def delete(self, index1, index2) -> None:
                        self.textBox.delete(index1, index2)
    
                    def flush(self) -> None:
                        pass
    
                sys.stdout = TkTextBoxStdout(textBox)
    
                def FinalizeInput(stack: list[str]) -> str:
                    result = ''
                    for item in stack:
                        if item == "/-":
                            result = result[0:-1]
    
                        else:
                            result += item
    
                    return result
    
                def on_key(event: tk.Event):
                    match event.keycode:
                        case 13:
                            self.__inputTextStack__.append('\n')
    
                        case 8:
                            self.__inputTextStack__.append("/-")
    
                        case _:
                            self.__inputTextStack__.append(event.char)
    
                    if self.__getInput__:
                        if self.__inputTextStack__[-1] != '/-':
                            sys.stdout.write(self.__inputTextStack__[-1])
                            self.__inputString__ += self.__inputTextStack__[-1]
                        else:
                            if self.__inputString__ != '':
                                sys.stdout.delete("end-2c", "end")
                            self.__inputString__ = self.__inputString__[0:-1]
    
                        if self.__inputTextStack__[-1] == "\n":
                            self.__getInput__ = False
                        self.__inputTextStack__.clear()
    
                textBox.bind("<Key>", on_key)
    
                def print(*args, sep: str = " ", end: str = "\n", style: str = '') -> None:
                    parsedText = parseColoredPrint(sep.join(map(str, args)) + end, style)
                    if len(parsedText) > 1:
                        for item in parsedText:
                            if isinstance(item, str):
                                sys.stdout.write(item, style)
    
                            elif isinstance(item, tuple):
                                sys.stdout.write(item[1], item[0])
    
                    elif isinstance(parsedText[0], tuple):
                        sys.stdout.write(parsedText[0][1], parsedText[0][0])
    
                    else:
                        sys.stdout.write(parsedText[0])
    
                def input(initialText: str, /) -> str:
                    sys.stdout.write(initialText)
                    if self.__inputTextStack__.__contains__("\n"):
                        sys.stdout.write(FinalizeInput(self.__inputTextStack__[0:self.__inputTextStack__.index("\n") + 1]))
                        self.__inputString__ = FinalizeInput(self.__inputTextStack__[0:self.__inputTextStack__.index("\n") + 1])
                        self.__inputTextStack__ = self.__inputTextStack__[self.__inputTextStack__.index("\n")::]
                    else:
                        sys.stdout.write(FinalizeInput(self.__inputTextStack__))
                        self.__inputString__ = FinalizeInput(self.__inputTextStack__)
                        self.__getInput__ = True
    
                        while self.__getInput__:
                            root.update()
    
                    return self.__inputString__
    
                while killFlag.is_alive():
                    if len(queue) > 0:
                        item = queue.getItem()
                        match item.mode:
                            case "print":
                                print(*item.args, **item.parameters)
    
                            case "input":
                                queue.returnQueue = input(item.args[0])
                                self.__inputString__ = ''
    
                            case 'clear':
                                sys.stdout.clear()
                    root.update()
    
            self.Queue = ConsoleQueue()
            self.killThreadFlag = KillFlag()
    
            self._console = thr.Thread(target=_consoleThread, args=(self.Queue, self.killThreadFlag))
            self._console.daemon = True
            self._console.start()
    
        def closeConsole(self) -> None:
            self.killThreadFlag.kill()
            self._console.join()
    
        def print(self, *args, sep: str = " ", end: str = "\n", style: str | None = None) -> None:
            self.Queue.addQueue(ConsoleQueuePacket("print", *args, sep=sep, end=end, style=style if isinstance(style, str) else ''))
    
        def input(self, text: str, /) -> str:
            self.Queue.addQueue(ConsoleQueuePacket("input", text, ''))
            self.Queue.returnQueue = None
            while not self.Queue.returnQueue:
                pass
            return self.Queue.returnQueue.removesuffix("\n")
    
        def clear(self) -> None:
            self.Queue.addQueue(ConsoleQueuePacket('clear'))
import socket as ip

heldCommands: list[list] = []
stdout = basicConsoleStdout()

def runImmediately(func):
    func()

    return func

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
        if (item == targetVal) and (type(item) == type(targetVal)):
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
        if (item == targetVal) and (type(item) == type(targetVal)):
            return idx
        if isinstance(item, list):
            itemResult = indexIntoLayeredList(item, targetVal, False, idx)
            if isinstance(itemResult, int):
                return itemResult
        idx += 1 if start else 0
    return None

def is_hidden(path: Path) -> bool:
    try:
        return bool(os.stat(path).st_file_attributes & 0x2)

    except FileNotFoundError:
        return False

class ConsoleStdout(basicConsoleStdout):
    style: bool = True

    def __init__(self, console: Console) -> None:
        self.console = console

    def write(self, text: str):
        self.console.print(text, end="")

    def clear(self):
        os.system("powershell clear")

    def flush(self):
        sys.__stdout__.flush()

    def __close__(self):
        pass

def removeRichStyling(text: str) -> None:
    return "".join([l[0] for l in [text.split("[") for text in text.split("]")]])

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

jsonTypesToBytes = lambda data, sep=" ": bytes([int(binStr, 2) for binStr in data.split(sep)])

TERMINAL_WIDTH = shutil.get_terminal_size().columns

curdir = Path.home()
cwd = Path.cwd()
pyPath = Path(__file__).parent if DEBUG else Path.cwd()
jsonPath = Path.home().joinpath(".csconfig")

os.chdir(curdir)

configExport = {"~:Home": False, "Auto-Highlighting": True, "needpypath": False, "pycommand": "python", "pypath": "", "addondir": "", "run": [], "webcut": [], "vars": [], "aliases": {"la": "ls -a"}, "bookmarks": {}}
configTypes = {"~:Home": "bool", "Auto-Highlighting": "bool", "needpypath": "bool", "pycommand": "str", "pypath": "dirpath/", "addondir": "dirpath", "run": "managed", "webcut": "managed", "vars": "managed", "aliases": "managed", "bookmarks": "managed"}
configTypeUsr = {"bool": "Boolean", "": "Nothing", "dirpath": "Directory", "str": "String"}

def updateConfig() -> None:
    config = importFromJSON(jsonPath)
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
    if cwd.joinpath(".config").exists():
        json = importFromJSON(cwd.joinpath(".config"))
        exportToJSON(json, jsonPath)
        updateConfig()

    else:
        exportToJSON(configExport, jsonPath)

else:
    updateConfig()

envVars = {
    "FILEDIR": PathVar(str(pyPath)),
    "USER": StrVar(Path.home().name),
    "PYDIR": PathVar(str(Path(importFromJSON(jsonPath)["pypath"]))) if importFromJSON(jsonPath)["needpypath"] else StrVar(''),
    "V": StrVar(Version("-"))
}

ENVIRONMENT_VARS = {f"%{name}%": value for name, value in envVars.items()} | {"~": PathVar(str(Path.home()))}

if GUIC:
    cli = Console('Custom-Shell', bgColor='#000', font=('Cascadia Mono', 12), boldStyle='brightness', colorTheme=({'green3': "#00A700"}, {'green3': '#00d700'}))
else:
    cli = Console(highlight=importFromJSON(jsonPath)["Auto-Highlighting"])

stdout = ConsoleStdout(cli)
__stdout__ = stdout

class Command:

    def __init__(self, names : list[str], func : callable, helpInfo : dict, parserPreset: Literal["default", "base-split"] = "default"):
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
        self.vars: dict[str: VarType] = ENVIRONMENT_VARS | {f"%{dct["name"]}": TypeRegistry.types[TypeRegistry.nicknames[dct['type']]](TypeRegistry.types[TypeRegistry.nicknames[dct['type']]].__jload__(jsonTypesToBytes(dct["data"]))) for dct in importFromJSON(jsonPath)['vars']}
        self.recording: bool = False

    def parseCommand(self, userInput : str) -> dict[str:str]:
        output: dict[str:str] = {"args": None}
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
                        output["args"].append(arg)
            if kwarg != None:
                output[kwarg] = None

        return output

    def changeVarArgs(self, parsedUserInput: dict[str, str | list[str] | None]) -> dict:
        result = list(parsedUserInput.values())
        for idx, item in enumerate(result):
            if isinstance(item, list):
                for i, arg in enumerate(item):
                    for name, val in self.vars.items():
                        item[i] = arg.replace(name, str(val))
                        arg = item[i]
                result[idx] = item
                continue

            elif isinstance(item, str):
                for name, val in self.vars.items():
                    result[idx] = item.replace(name, str(val))

        return {key: value for key, value in zip(parsedUserInput.keys(), result)}

    def parseStdout(self, text: str) -> Stdout:
        match text:
            case "basic":
                return basicConsoleStdout()

            case "nul" | "null":
                return nullStdout()

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
            for command in userInput.split("&&"):
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
            stdout = self.parseStdout(stdoutStr)

        if flatten(self.commandNames).__contains__(userInput.split(" ", 1)[0]):
            command : Command = self.commands[indexIntoLayeredList(self.commandNames, userInput.split(" ", 1)[0].lower())]
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

def lambdaWithKWArgsSetup(lambdaFunc: callable):
    def runLambdaWithKWArgs(**kwargs):
        lambdaFunc(kwargs)

    return runLambdaWithKWArgs

def lambdaWithArgsSetup(lambdaFunc: callable):
    def runLambdaWithArgs(**kwargs):
        lambdaFunc(kwargs['args'][0])

    return runLambdaWithArgs

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

    def checkRangeOfArgs(min: int, max: int) -> callable:
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

    print(kwargs["s"].join(kwargs["args"]), style=kwargs["-color"])

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
            execRunCom(f'"{Path(runConfig["path"])}"', runConfig["language"])

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
            print(f"{kwargs["s"].join(folders)}", end=kwargs["s"], style=kwargs["-folder-color"])
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
    if not needsArgsSetup("vscode", 1, "<=")(**kwargs):
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
    kwargs = booleanArgs(["u", "-update"], **kwargs)
    if kwargs["u"] or kwargs["-update"]:
        for var, val in configUpdates.items():
            if var == "$func":
                exec(val)
                continue

            exec(f"{var} = {val}")
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

def runShellFile(filepath : str) -> None:
    with open(filepath, "r") as file:
        commands = [command for command in file.read().split("\n") if len(command) > 0]

    for command in commands:
        comm.run(command.strip(" "))

@runImmediately
def initCommands() -> None:
    commands.append(Command(["print", 'echo'], println, {"name": "print", "description": "Prints the arguments you give it.", "has-kwargs": True, "kwargs": {"-s": "Separating string between each argument", "--color": "Style the printed text"}}))
    commands.append(Command(["exit", "stop"], lambda: os._exit(0), {"name": "exit", "description": "Exits the terminal.", "has-kwargs": False}))

    commands.append(Command(["cat", "read", "printf"], printFile, {"name": "read-file", "description": "Prints the contents of a file.", "has-kwargs": False}))

    commands.append(Command(["clear", "cls"], showStartingPrints, {"name": "clear", "description": "Clears the terminal.", "has-kwargs": True, "kwargs": {"-r": "Loads the starting text after clearing the screen."}}))
    commands.append(Command(["list", "ls"], listdir, {"name": "list", "description": "Lists all files in the current directory.", "has-kwargs": True, "kwargs": {"-ps": "Runs the powershell version of ls instead of the shell's version", "-t": "Filter to both files and folders 'all', only files 'files', or only folders 'folders'", "--folder-color": "Styles the color of the names of the folders", "--file-color": "Styles the color of the names of the files"}}))

    commands.append(Command(["makefile", "mkf", "touch"], makeFile, {"name": "touch", "description": "Makes files.", "has-kwargs": False}))
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
    commands.append(Command(["version", "ver"], lambda: print(f"[bold][red]{Version(" ")}[/bold][/red]"), {"name": "version", "description": "Prints the current version of the shell.", "has-kwargs": False}))

    commands.append(Command(["addons"], managePlugins, {"name": "addons", "description": "Manages all imported addons.", "has-kwargs": True, "kwargs": {"-l": "Lists the currently imported addons."}}))
    commands.append(Command(["system", "sys"], sysCommand, {"name":"system", "description": "Runs the given system command.", "has-kwargs": False}, "base-split"))

    commands.append(Command(["powershell", "ps"], psCommand, {"name": "system-powershell", "description": "Runs the given system command in powershell.", "has-kwargs": False}, 'base-split'))
    commands.append(Command(["cmd"], cmdCommand, {"name": "system-cmd", "description": "Runs the given system command in command prompt.", "has-kwargs": False}, 'base-split'))

    commands.append(Command(["config"], changeConfig, {"name": "configure", "description": "Changes the config file", "has-kwargs": True, "kwargs": {"-u / -update": "Updates all the items that use the config fields."}}))
    commands.append(Command(['csh', 'shell', 'sh'], lambdaWithArgsSetup(runShellFile), {'name': 'shell', 'description': 'Runs a .csh file', 'has-kwargs': False}))

    commands.append(Command(["project", "projmanager", "manager", "proj", "pm"], ManageProj, {"name": "project-manager", "description": "Runs the Custom-Shell Project Manager CLI.", "has-kwargs": False}, 'base-split'))
    commands.append(Command(["bookmarks", "marks"], bookmark, {"name": "bookmarks", "description": "Manages bookmarks, allowing you to add, go to, and list your bookmarks.", "has-kwargs": True, "kwargs": {"-s": "When listing bookmarks, this is used for the separating characters between bookmarks", "--color": "When listing bookmarks, this is used to style the bookmarks."}}))
    commands.append(helpCommand)

def showCWDAndGetInput() -> str:
    cli.print(f"[blue]{ENVIRONMENT_VARS["%USER%"]}@{ip.gethostname()}[/blue]:[green3]{(str(curdir).replace(str(Path.home()), "~")) if importFromJSON(jsonPath)["~:Home"] else curdir}{str(b"\x00", 'ascii')}[green3][magenta]$", end=' ', style='bold')
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
import sys

initRecording(comm)

def main():
    showStartingPrints(True)
    release()
    inputLoop(comm)

if __name__ == "__main__":
    sysArgv = [arg for arg in sys.argv[1:] if not arg.__contains__("-")]
    match len(sysArgv):
        case 0:
            main()

        case 1:
            os.chdir(cwd)
            path = Path(sysArgv[0]).resolve()
            os.chdir(curdir)

            if path.is_file():
                changeToInterpreter(comm)
                release()
                runShellFile(path)

            elif path.is_dir():
                comm.run(f"cd {path}")
                main()

            else:
                comm.run(sysArgv[0])
                if sys.argv[1:].__contains__("-k") or sys.argv[1:].__contains__("--keep"):
                    main()

        case _:
            if not DEBUG:
                print(f"Usage: 'Custom-Shell {Version(" ")}.exe' OR 'Custom-Shell {Version(" ")}.exe' <file.csh>")

            else:
                print(f"Usage: python {__file__} OR python {__file__} <file.csh> OR {__file__} <directory> OR {__file__} <command>")