from dataclasses import dataclass
from typing import Literal
from io import TextIOBase

@dataclass
class Diff:
    struct: dict[int, tuple[list[str], list[str]]]
    includeStyling: bool = False

    def __str__(self) -> str:
        result: str = ""
        for i, (rms, adds) in self.struct.items():
            result += f"\n{"[cyan bold]" if self.includeStyling else ''}@@ Line {i}{"[/cyan bold]" if self.includeStyling else ''}\n{"\n".join([f"{"[red bold]" if self.includeStyling else ''}-- {ln}{"[/red bold]" if self.includeStyling else ''}" for ln in rms])}\n{"\n".join([f"{"[green bold]" if self.includeStyling else ''}++ {ln}{"[/green bold]" if self.includeStyling else ''}" for ln in adds])}\n"

        return result.strip("\n")

def genDiffVT(text1: str, text2: str, lnStr: Literal['LF', 'CRLF'] = 'LF', includeStyling: bool = True) -> Diff:
    result: Diff = Diff({}, includeStyling)
    lnSpl: str | None = "\n" if lnStr.upper() == 'LF' else '\r\n' if lnStr.upper() == "CRLF" else None
    if lnStr is None:
        raise ValueError("lnStr must either be 'LF' or 'CRLF'")

    lastLn: int = -1
    secIdx: int = 0
    for i, (ln1, ln2) in enumerate(zip(text1.split(lnSpl), text2.split(lnSpl)), 1):
        if ln1 != ln2:
            if lastLn + 1 == i:
                result.struct[secIdx] = (result.struct[secIdx][0] + [ln1], result.struct[secIdx][1] + [ln2])
                lastLn = i
                continue

            result.struct[i] = ([ln1], [ln2])
            secIdx = i

    if len(text1.split(lnSpl)) < len(text2.split(lnSpl)):
        for ln in text2.split(lnSpl)[lastLn:]:
            result.struct[secIdx] = (result.struct[secIdx][0], result.struct[secIdx][1] + [ln])

    elif len(text1.split(lnSpl)) > len(text2.split(lnSpl)):
        for ln in text1.split(lnSpl)[lastLn:]:
            result.struct[secIdx] = (result.struct[secIdx][0] + [ln], result.struct[secIdx][1])

    return result

def genDiffFilesText(file1: TextIOBase, file2: TextIOBase, lnStr: Literal['LF', 'CRLF'] = 'LF', includeStyling: bool = True) -> Diff:
    result: Diff = Diff({}, includeStyling)
    lnSpl: str | None = "\n" if lnStr.upper() == 'LF' else '\r\n' if lnStr.upper() == "CRLF" else None
    if lnStr is None:
        raise ValueError("lnStr must either be 'LF' or 'CRLF'")

    text1, text2 = file1.read(), file2.read()

    lastLn: int = -1
    secIdx: int = 0
    for i, (ln1, ln2) in enumerate(zip(text1.split(lnSpl), text2.split(lnSpl)), 1):
        if ln1 != ln2:
            if lastLn + 1 == i:
                result.struct[secIdx] = (result.struct[secIdx][0] + [ln1], result.struct[secIdx][1] + [ln2])
                lastLn = i
                continue

            result.struct[i] = ([ln1], [ln2])
            lastLn = i
            secIdx = i

    if len(text1.split(lnSpl)) < len(text2.split(lnSpl)):
        for ln in text2.split(lnSpl)[lastLn:]:
            result.struct[secIdx] = (result.struct[secIdx][0], result.struct[secIdx][1] + [ln])

    elif len(text1.split(lnSpl)) > len(text2.split(lnSpl)):
        for ln in text1.split(lnSpl)[lastLn:]:
            result.struct[secIdx] = (result.struct[secIdx][0] + [ln], result.struct[secIdx][1])

    return result

if __name__ == "__main__":
    from pathlib import Path
    from rich.console import Console
    if input(":") == "":
        import os
        os.chdir("commandUtils/diffy")

    with Path("tst1.txt").open() as file1:
        with Path("tst2.txt").open() as file2:
            diff: Diff = genDiffFilesText(file1, file2)

    cli = Console(highlight=False)
    cli.print(str(diff))