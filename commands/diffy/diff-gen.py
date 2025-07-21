from pathlib import Path
from rich.console import Console
import sys

cli: Console = Console(highlight=False)

class Diff:

    def __init__(self, state: list[tuple[int, str, str]] = []) -> None:
        self.difl: list[tuple[int, str, str]] = state

    def add(self, diff: tuple[int, str, str]) -> None:
        self.difl.append(diff)

    def display(self, mode: int | str) -> None:
        match mode:
            case 0 | 'style' | 'rich':
                strMode = 0

            case 1 | 'basic' | 'file':
                strMode = 1

            case _:
                raise ValueError("Invalid mode.")

        cli.print(self.str(strMode))

    def str(self, mode: int = 0) -> str:
        result = ""
        match mode:
            case 0:
                pastLn: int = 0
                for i, diff in enumerate(self.difl):
                    if diff[0] > pastLn:
                        result += f"\n[bold cyan]@@ Line {diff[0]} @@[/bold cyan]"

                    result += f"{f"\n[red]{diff[1]}[/red]\n" if diff[1] != "" else ""}[green]{diff[2]}[/green]\n"
                    pastLn = diff[0] + 1

            case 1:
                pass

        return result.rstrip("\n")

    def __repr__(self) -> str:
        return f"Diff({self.difl})"

def generateDiff(filepath1: Path, filepath2: Path) -> Diff:
    with filepath1.open("r") as file:
        ogContent = file.read()

    with filepath2.open("r") as file:
        newContent = file.read()

    diff = Diff()
    lastLn = 0

    for i, lns in enumerate(zip(ogContent.split("\n"), newContent.split("\n")), start=1):
        ln1, ln2 = lns
        if ln1 != ln2:
            diff.add((i, ln1, ln2))
        lastLn = i

    while len(ogContent.split('\n')) > lastLn:
        lastLn += 1
        ln = ogContent.split("\n")[lastLn - 1]
        diff.add((lastLn, ln, ''))

    while len(newContent.split('\n')) > lastLn:
        lastLn += 1
        ln = newContent.split('\n')[lastLn - 1]
        diff.add((lastLn, '', ln))

    return diff

if __name__ == "__main__":
    diff = generateDiff(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
    diff.display('rich')
