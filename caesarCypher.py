from typing import Callable

charLists: dict[str, str] = {
    "alphabet": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "alphanumeric": "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
    "qwerty": "QWERTYUIOPASDFGHJKLZXCVBNM",
    "numeric": "1234567890"
}

def customCypherPreset(charListName, turns : int, *extra, keepCase : bool = True, addInfo : bool = False, getInfo : bool = True, customCharList : list[str] | None = None) -> tuple[Callable, Callable]:
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

def cypher(text : str, charListID : str = "alphabet", turns : int = 1,*, keepCase : bool = True, addInfo : bool = False, customCharList : list[str] | None = None) -> str:
    if not customCharList:
        charList: list[str] = list(charLists[charListID])
    else:
        charList: list[str] = customCharList
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

def deCypher(text : str, charListID : str = "alphabet", turns : int = 1,*, keepCase : bool = True, addInfo : bool = False, customCharList : list[str] | None = None) -> str:
    if not customCharList:
        charList = list(charLists[charListID])
    else:
        charList = customCharList
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