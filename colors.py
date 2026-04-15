from inputkit import handleInput, Key
import sys

num: int = 0

def draw():
    sys.stdout.write(f"\r\x1b[48;5;{num}m    ")
    sys.stdout.flush()

draw()

def axis(neg: Key | str, pos: Key | str, key: Key | str) -> int:
    if key == neg: return -1
    if key == pos: return 1
    return 0

@handleInput
def inpHandler(key: Key | str) -> bool:
    global num
    match key:
        case Key.ENTER:
            return False

        case Key.DOWN | Key.UP:
            num += axis(Key.UP, Key.DOWN, key)
            draw()

    return True

print(f"\n\x1b[0m{num}")