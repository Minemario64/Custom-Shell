from pathlib import Path
import importlib, importlib.util

def importFromJSON(filename: str | Path) -> dict:
    from json import load

    filepath = Path(filename) if isinstance(filename, str) else filename
    if filepath.exists():
        with open(filepath, "r") as file:
            return load(file)

    raise FileNotFoundError(f"'{str(filepath)}' does not exist")

def exportToJSON(data: dict, filename: str | Path, indent : bool = True) -> None:
    from json import dumps, dump

    filepath = Path(filename) if isinstance(filename, str) else filename
    if filepath.exists():
        if indent:
            with open(filepath, "w") as file:
                file.write(dumps(data, indent=4))
        else:
            with open(filepath, "w") as file:
                dump(data, file)


def loadModule(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec) # type: ignore
    spec.loader.exec_module(module) # type: ignore
    return module