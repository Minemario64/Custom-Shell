from math import ceil

NON_EDGE: int = 0
CORNER: int = 1
EDGE_X: int = 2
EDGE_Y: int = 3

UP: int = 4
DOWN: int = 8
LEFT: int = 16
RIGHT: int = 32


RECT_CHARS: dict[int, str] = {CORNER | UP | LEFT: "╭", CORNER | UP | RIGHT: "╮", CORNER | DOWN | LEFT: "╰", CORNER | DOWN | RIGHT: "╯", EDGE_Y: "─", EDGE_X: "│", NON_EDGE: " "}

def rect(length: int, width: int, lengthMultiplier: int = 2, styled: bool = False, style: str = "") -> str:
    result: str = ""
    LAST_X: int = (length * lengthMultiplier) - 1
    LAST_Y: int = width - 1
    for y in range(width):
        for x in range(length * lengthMultiplier):
            ID: int = 0
            if (y == 0 or y == LAST_Y) and (x == 0 or x == LAST_X):
                ID |= CORNER

                match x, y:
                    case 0, 0:
                        ID |= UP | LEFT

                    case LAST_X, 0:
                        ID |= UP | RIGHT

                    case 0, LAST_Y:
                        ID |= DOWN | LEFT

                    case LAST_X, LAST_Y:
                        ID |= DOWN | RIGHT

            elif (y == 0 or y == LAST_Y):
                ID |= EDGE_Y

            elif (x == 0 or x == LAST_X):
                ID |= EDGE_X

            result += RECT_CHARS[ID]

        if y < LAST_Y: result += "\n"

    return result

def removeRichStyling(text: str) -> str:
    return "".join([l[0] for l in [text.split("[") for text in text.split("]")]])

def centerStr(text: str, width: int, styled: bool = False) -> str:
    return "\n".join([f"{" "*((width - len(removeRichStyling(ln) if styled else ln)) // 2)}{ln}{" "*(ceil((width - len(removeRichStyling(ln) if styled else ln)) / 2))}" for ln in text.split("\n")])