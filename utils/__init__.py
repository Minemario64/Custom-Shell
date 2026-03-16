import inspect
from json import load, dumps, dump
from pathlib import Path

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
    # Check again but I think this function is to get the index of the element as if the list was
    # flat so, [[1, 2], [3, 4]] would return 2 if target was 3, because 2 would correlate
    # to 3 in [3, 4].
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
    # Check again but I think this function is to get the index of the parent element in the first
    # layer of the list, so [[1, 2], [3, 4]] would return 1 if target was 3, because 1 would correlate
    # to [3, 4].
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