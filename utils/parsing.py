from typing import Literal

def combineQuotes(args: list[str]) -> list[str]:
    newargs = []
    inquote = False
    quote = ""
    text = ""
    if 2 in DEBUG_MODE: print(",".join(args))
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
                    if 2 in DEBUG_MODE: print(f"Just 1 arg with {quote}, {arg}")
                    text = text[0:-1]
                    inquote = False
                    newargs.append(text)
                    text = ""
                    quote = ""

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

def parseVar(text: str, mode: Literal['$', '%', '%%']) -> tuple[str, str, str]:
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

if __name__ == "__main__":
    DEBUG_MODE = [2]

else:
    DEBUG_MODE = []