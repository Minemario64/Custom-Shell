import os

def countUntilLand(ln: str) -> int:
    for i, char in enumerate(ln, 0):
        if char != " ":
            return i
    raise ValueError("Text '{ln}' has no land (non-whitespace)")

def traverseFuncStr(text: str, start: int = 0) -> str:
    funcLevel: int = 0
    result: str = ""
    for char in text[start::]:
        match char:
            case "(":
                if funcLevel > 0:
                    result += char

                funcLevel += 1

            case ")":
                if funcLevel == 0:
                    return '""'

                funcLevel -= 1
                if funcLevel > 0:
                    result += char

                if funcLevel == 0:
                    return result

            case _:
                if funcLevel > 0:
                    result += char

    return '""'

def clear() -> None:
    os.system("powershell clear")