def PMVer(sep: str) -> str:
    ver = [1, 0, 0, ""]
    version = (".".join([str(num) for num in ver[0:3]]), ver[3])
    return f"{version[0]}{sep}{version[1]}" if version[1] != '' else version[0]



from pathlib import Path
from json import load, dumps, dump
import os
from utils import *

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
                os.system(f'rm -rf "{templatePath}"')

            else:
                return False

        templatePath.mkdir()
        os.system(f'cp -R "{directory}" "{templatePath}"')
        return True

    def makeProject(self, projectPath: Path, templateName: str = 'default') -> None:
        """Makes a project from a given template

        Args:
            projectPath (Path): The path of the project
            templateName (str, optional): The name of the template to copy from. Defaults to 'default'.
        """
        if not self.templatesPath.joinpath(templateName).exists():
            raise ValueError("Cannot make a project with a template that doesn't exist")

        os.system(f'cp -R "{self.templatesPath.joinpath(templateName)}" "{projectPath}"')

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
    os.system(f"{LANG_LOOKUP[obj[1]["language"]]}{language.commandsPath.joinpath(obj[0]).resolve()} {" ".join(args)}")


if not globalCommandsPath.exists():
    globalCommandsPath.mkdir()

if not globalTemplatesPath.exists():
    globalTemplatesPath.mkdir()

defaultConfig = {"languages": {}, "command-languages": {}}

def updatePMConfig() -> None:
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
    updatePMConfig()

LANG_LOOKUP = LANG_LOOKUP | importFromJSON(configPath)["command-languages"]

langs: dict[str, Language] = {name: Language(name, ext) for name, ext in importFromJSON(configPath)["languages"].items()}

for lang in langs.values():
    if not (lang.commandsPath.exists() and lang.commandsPath.exists()):
        lang.init()