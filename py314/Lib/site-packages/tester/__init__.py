from rich import traceback ; traceback.install()
from typing import Callable, NamedTuple, Iterator
from rich.console import Console
from utils import *
from draw import *
import re
from shutil import get_terminal_size
from enum import Enum
from math import ceil
from io import StringIO
import sys

class TestingTheme(Enum):
    White = "white bold"
    Default = "cyan"

cli = Console(highlight=False)
CLEAR: str = "\033[2J\033[H"
THEME = TestingTheme.Default
GLOBALS = globals()

class xtrastdout:

    def __init__(self):
        self.buffer: StringIO = StringIO()

    def write(self, s: str) -> None:
        self.buffer.write(s)

    def flush(self) -> None:
        pass

    def writeObjs(self, *objects, sep: str = " ", end: str = "\n") -> None:
        self.write(sep.join(str(obj) for obj in objects) + end)

    def print(self) -> None:
        cli.print(self.buffer.getvalue())

class TestResults(NamedTuple):
    description: str
    result: bool | None

stdout = xtrastdout()

def printFeatureStyled(description: str, tests: list[TestResults] | None) -> None:
    COLOR: TestingTheme = THEME
    TERMINAL_WIDTH = get_terminal_size().columns

    LENGTH = max(([len(test.description) for test in tests] if not tests is None else []) + [len(description)]) + 8

    rectangle: list[str] | str = rect(LENGTH, 5 if tests is None else 4 + (len(tests) * 5), lengthMultiplier=1).split("\n")
    rectangle[1] = f"{RECT_CHARS[EDGE_X]}{" "*(((LENGTH - len(description)) - 2) // 2)}[bold]{description}[/bold]{" "*ceil((((LENGTH - len(description)) - 2) / 2))}{RECT_CHARS[EDGE_X]}"
    rectangle[2] = f"├{"─"*(len(rectangle[2]) - 2)}┤"

    if not tests is None:
        for i, test in enumerate(tests):
            lns = rect(LENGTH - 4, 5, lengthMultiplier=1).split("\n")
            lns[1] = f"{RECT_CHARS[EDGE_X]}[bold]{centerStr(test.description, len(lns[0]) - 2)}[/bold]{RECT_CHARS[EDGE_X]}"
            lns[2] = f"├{"─"*(len(lns[2]) - 2)}┤"
            lns[3] = f"{RECT_CHARS[EDGE_X]}{centerStr(f"[/{COLOR.value}][sea_green2 bold]Passed[/sea_green2 bold][{COLOR.value}]" if test.result else f"[/{COLOR.value}][red bold]Failed[/red bold][{COLOR.value}]", len(lns[2]) - 2, styled=True)}{RECT_CHARS[EDGE_X]}"
            lns = [f"{RECT_CHARS[EDGE_X]} {content} {RECT_CHARS[EDGE_X]}" for content in lns]
            rectangle[3+(5*i):3+(5*i)+len(lns)] = lns

    rectangle = f"[{COLOR.value}]{centerStr("\n".join(rectangle), TERMINAL_WIDTH, styled=True)}[/{COLOR.value}]"
    cli.print(CLEAR + rectangle)
    stdout.print()

def it(testDescription: str, codePlusExpectations: str) -> TestResults:

    def process(funcStr: str) -> str:
        lns = funcStr.split("\n")
        for i, ln in enumerate(lns):
            passedPattern = re.compile(r" *passed\(.*\)")
            if passedPattern.match(ln):
                lns[i] = f"{" "*countUntilLand(ln)}if passed({ln.lstrip(" ").removeprefix("passed(").removesuffix(")")}): return True"

        lns.append(f"{" "*countUntilLand(lns[1])}return False")
        return "\n".join(lns)

    testStr: str = f"def test() -> bool:\n    {"\n    ".join([ln for ln in codePlusExpectations.split("\n") if ln != ""])}"
    testStr = process(testStr)
    exec(testStr, GLOBALS)
    return TestResults(testDescription, GLOBALS["test"]())

def describe(featureDescription: str, tests: str) -> None:
    printFeatureStyled(featureDescription, None)

    def process(funcStr: str) -> str:
        lns = funcStr.split("\n")
        for i, ln in enumerate(lns):
            passedPattern = re.compile(r" *it\(")
            matched = passedPattern.match(ln)
            if matched:
                text = f"{" "*countUntilLand(ln)}testResults.append(it({traverseFuncStr("\n".join(lns), matched.pos + (len("\n".join(lns[0:i]))))}))"
                for exi, chars in enumerate(text.split("\n"), 0):
                    lns[i + exi] = chars

                lns.insert(i + text.count("\n") + 1, f"{" "*countUntilLand(ln)}printFeatureStyled(featureDesc, testResults)")

        lns.append(f"{" "*countUntilLand(lns[1])}return not False in testResults")
        return "\n".join(lns)

    testStrs: str = f"def testFeature() -> bool:\n    testResults: list[TestResults] = []\n    {"\n    ".join([ln.lstrip(" ") for ln in tests.split("\n") if ln != ""])}\n    return not testResults.__contains__(False)"
    scope: dict = GLOBALS
    scope["featureDesc"] = featureDescription
    exec(process(testStrs), scope)
    print(scope["testFeature"]())

passed: Callable[[bool], bool] = lambda passed: passed

if __name__ == "__main__":
    def add(a: int, b: int) -> int:
        return a + b

    def multiply(a: int, b: int) -> int:
        return a * b

    describe("Basic Arithmetic", '''
it("Adds 2 numbers", """
    import time
    time.sleep(1.2)
    result = add(2, 2)
    passed(result == 4)
""")
it("Multiplies 2 numbers", """
    result = multiply(4, 8)
    passed(result == 32)
""")
''')