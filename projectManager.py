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