import threading as thr
from typing import Literal
import atexit

class ConsoleQueuePacket:

    def __init__(self, mode: Literal['print', 'input', 'clear'], /, *args, **parameters) -> None:
        self.mode = mode
        self.args = args
        if mode == 'print':
            self.parameters = parameters if parameters else {'sep': ' ', 'end': '\n', 'style': None}
        else:
            self.parameters = parameters

class ConsoleQueue:

    def __init__(self) -> None:
        self.queue: list[ConsoleQueuePacket] = []
        self.returnQueue: str | None = None

    def __len__(self) -> int:
        return len(self.queue)

    def addQueue(self, packet: ConsoleQueuePacket) -> None:
        self.queue.append(packet)

    def getItem(self) -> ConsoleQueuePacket:
        return self.queue.pop(0)

    def getReturnedStr(self) -> str | None:
        return self.returnQueue

class KillFlag:

    def __init__(self) -> None:
        self._flag = False

    def kill(self) -> None:
        self._flag = True

    def is_alive(self) -> bool:
        return not self._flag

def parseStyles(styles: str) -> list[str]:
    result: list[str] = []
    bg: bool = False
    for style in [style for style in styles.split(" ") if style != '']:
        match style:
            case 'underline':
                if len(result) == 0:
                    result.append('underline')
                    continue

                if result[-1] == 'default':
                    result[-1] = 'underline'
                    continue

                result[-1] = f"{result[-1]}-underline"

            case 'on':
                bg = True

            case _:
                if bg:
                    result.append(f"{style}-bg")
                    bg = False
                    continue

                result.append(style)

    return result

def parseColoredPrint(text: str, globalStyle: str = '') -> list[str | tuple[str, str]]:
    instyle = False
    style = ""
    styles = ['']

    for char in text:
        if char == '[':
            instyle = True
        elif char == ']':
            instyle = False
            if style.startswith("/"):
                if styles[-1][0].__contains__(style.removeprefix("/")):
                    if not styles[-1][0] == style.removeprefix("/"):
                        styles.append([styles[-1][0].replace(style.removeprefix("/"), " ").strip(' '), ''])
                    else:
                        styles.append('')

            elif isinstance(styles[-1], list):
                if styles[-1][1] == '':
                    styles[-1][0] += f" {style}"
                else:
                    styles.append([f"{styles[-1][0]} {style}", ''])
            else:
                styles.append([f'{f'{globalStyle} ' if globalStyle != '' else ''}{style}', ''])
            style = ''
        else:
            if instyle:
                style += char
            else:
                if isinstance(styles[-1], list):
                    styles[-1][1] += char
                else:
                    styles[-1] += char

    styles = [tuple(stylePart) if isinstance(stylePart, list) else stylePart for stylePart in styles]
    if globalStyle != '':
        styles = [(globalStyle, text) if isinstance(text, str) else text for text in styles]

    return styles

tagColors: tuple[dict[str: str], dict[str: str]] = ({'red': '#DF2F00', 'green': '#20D220', "blue": '#0A70FF', 'yellow': '#CFCF00', 'cyan': "#00CAC0", "orange": "#CF7000", "magenta": "#B000B0", "purple": "#802AD0", "white": "#DDD", "lime": "#5C5", 'black': '#000000', 'grey': '#777'},
                                                    {'red': '#FF4D22', 'green': '#40F240', "blue": '#10A0F0', 'yellow': "#FFFF00", 'cyan': "#1AFFCF", "orange": "#F0A000", "magenta": "#EA00EA", "purple": "#A000F0", "white": "#FFF", "lime": "#9F9", 'black': '#2A2A2A', 'grey': '#AAA'})

from pathlib import Path
import re

class Console:

    _allConsoles: list = []

    @atexit.register
    def closeAllConsoles():
        for console in Console._allConsoles:
            console.closeConsole()

    def __init__(self, consoleName: str = 'Console', /, geometry: str = '800x450', icon: Path | None = None, bgColor: str = '#191919', defaultTextColor: str = '#FFF', font = ('Consolas', 12), boldStyle: Literal['width', 'brightness'] = 'width', colorTheme: tuple[dict[str: str], dict[str: str]] | None = None) -> None:
        def is_hexColor(s: str) -> bool:
            hex_pattern = re.compile(r"^#([0-9A-Fa-f]{3}){1,2}$")
            return hex_pattern.match(s)

        if not is_hexColor(bgColor):
            raise ValueError('bgColor needs to be a valid hex color value')

        if not is_hexColor(defaultTextColor):
            raise ValueError('defaultTextColor needs to be a valid hex color value')

        Console._allConsoles.append(self)

        self.__inputTextStack__: list[str] = []
        self.__inputString__: str = ""
        self.__getInput__: bool = False

        def _consoleThread(queue: ConsoleQueue, killFlag: KillFlag) -> None:
            import tkinter as tk
            from typing import Callable
            import os
            import sys

            def TextBoxEnable(textBox: tk.Text):
                def decorator(func: Callable):
                    def wrapper(*args, **kwargs):
                            textBox.config(state='normal')
                            result = func(*args, **kwargs)
                            textBox.config(state='disabled')
                            if result != None:
                                return result

                    return wrapper
                return decorator

            def on_close():
                root.destroy()
                os._exit(0)

            root = tk.Tk()
            if icon != None:
                root.iconbitmap(str(icon.absolute()))
            root.protocol("WM_DELETE_WINDOW", on_close)
            root.geometry(geometry)
            root.title(consoleName)
            root.config(bg=bgColor)

            textBox = tk.Text(root, bg=bgColor, fg=defaultTextColor, font=font, insertbackground=defaultTextColor, state='disabled')
            if isinstance(colorTheme, tuple):
                colors = (tagColors[0] | (colorTheme[0] if isinstance(colorTheme[0], dict) else {}), tagColors[1] | (colorTheme[1] if isinstance(colorTheme[1], dict) else {}))

            else:
                colors = tagColors

            for name, colorVal in colors[0].items():
                textBox.tag_config(name, foreground=colorVal)
                textBox.tag_config(f"{name}-bg", background=colorVal)
                textBox.tag_config(f"{name}-underline", underlinefg=colorVal, underline=True)

            match boldStyle:
                case 'width':
                    textBox.tag_config("bold", font=font + ('bold',))

                case 'brightness':
                    for name, colorVal in colors[1].items():
                        textBox.tag_config(f"bright-{name}", foreground=colorVal)
                        textBox.tag_config(f"bright-{name}-bg", background=colorVal)
                        textBox.tag_config(f"bright-{name}-underline", underlinefg=colorVal, underline=True)

            textBox.tag_config('underline', underline=True)

            textBox.pack(fill=tk.BOTH, expand=True)

            def parseStyles(styles: str) -> list[str]:
                result: list[str] = []
                bg: bool = False
                bold: bool = False
                for style in [style for style in styles.split(" ") if style != '']:
                    match style:
                        case 'underline':
                            if len(result) == 0:
                                result.append('underline')
                                continue

                            if result[-1] == 'default':
                                result[-1] = 'underline'
                                continue

                            result[-1] = f"{result[-1]}-underline"

                        case 'on':
                            bg = True

                        case 'default':
                            bold = False

                        case 'bold':
                            bold = True

                        case _:
                            if bg:
                                if bold:
                                    result.append(f"bright-{style}-bg")

                                else:
                                    result.append(f"{style}-bg")

                                bg = False
                                continue

                            if bold:
                                result.append(f"bright-{style}")

                            else:
                                result.append(style)

                return result

            class TkTextBoxStdout:

                def __init__(self, TextBox: tk.Text) -> None:
                    self.textBox = TextBox

                @TextBoxEnable(textBox)
                def write(self, text: str, tags: str | None = None) -> None:
                    if tags != None and (text.__contains__('\n') and tags.split(' ').__contains__("on")):
                        for line in [ln for ln in text.split("\n") if ln != '']:
                            self.textBox.insert(tk.END, line, parseStyles(tags) if tags != None else None)
                            self.textBox.insert(tk.END, '\n')
                    else:
                        self.textBox.insert(tk.END, text, parseStyles(tags) if tags != None else None)
                    self.textBox.see(tk.END)

                @TextBoxEnable(textBox)
                def clear(self) -> None:
                    self.textBox.delete("1.0", tk.END)

                @TextBoxEnable(textBox)
                def delete(self, index1, index2) -> None:
                    self.textBox.delete(index1, index2)

                def flush(self) -> None:
                    pass

            sys.stdout = TkTextBoxStdout(textBox)

            def FinalizeInput(stack: list[str]) -> str:
                result = ''
                for item in stack:
                    if item == "/-":
                        result = result[0:-1]

                    else:
                        result += item

                return result

            def on_key(event: tk.Event):
                match event.keycode:
                    case 13:
                        self.__inputTextStack__.append('\n')

                    case 8:
                        self.__inputTextStack__.append("/-")

                    case _:
                        self.__inputTextStack__.append(event.char)

                if self.__getInput__:
                    if self.__inputTextStack__[-1] != '/-':
                        sys.stdout.write(self.__inputTextStack__[-1])
                        self.__inputString__ += self.__inputTextStack__[-1]
                    else:
                        if self.__inputString__ != '':
                            sys.stdout.delete("end-2c", "end")
                        self.__inputString__ = self.__inputString__[0:-1]

                    if self.__inputTextStack__[-1] == "\n":
                        self.__getInput__ = False
                    self.__inputTextStack__.clear()

            textBox.bind("<Key>", on_key)

            def print(*args, sep: str = " ", end: str = "\n", style: str = '') -> None:
                parsedText = parseColoredPrint(sep.join(map(str, args)) + end, style)
                if len(parsedText) > 1:
                    for item in parsedText:
                        if isinstance(item, str):
                            sys.stdout.write(item, style)

                        elif isinstance(item, tuple):
                            sys.stdout.write(item[1], item[0])

                elif isinstance(parsedText[0], tuple):
                    sys.stdout.write(parsedText[0][1], parsedText[0][0])

                else:
                    sys.stdout.write(parsedText[0])

            def input(initialText: str, /) -> str:
                sys.stdout.write(initialText)
                if self.__inputTextStack__.__contains__("\n"):
                    sys.stdout.write(FinalizeInput(self.__inputTextStack__[0:self.__inputTextStack__.index("\n") + 1]))
                    self.__inputString__ = FinalizeInput(self.__inputTextStack__[0:self.__inputTextStack__.index("\n") + 1])
                    self.__inputTextStack__ = self.__inputTextStack__[self.__inputTextStack__.index("\n")::]
                else:
                    sys.stdout.write(FinalizeInput(self.__inputTextStack__))
                    self.__inputString__ = FinalizeInput(self.__inputTextStack__)
                    self.__getInput__ = True

                    while self.__getInput__:
                        root.update()

                return self.__inputString__

            while killFlag.is_alive():
                if len(queue) > 0:
                    item = queue.getItem()
                    match item.mode:
                        case "print":
                            print(*item.args, **item.parameters)

                        case "input":
                            queue.returnQueue = input(item.args[0])
                            self.__inputString__ = ''

                        case 'clear':
                            sys.stdout.clear()
                root.update()

        self.Queue = ConsoleQueue()
        self.killThreadFlag = KillFlag()

        self._console = thr.Thread(target=_consoleThread, args=(self.Queue, self.killThreadFlag))
        self._console.daemon = True
        self._console.start()

    def closeConsole(self) -> None:
        self.killThreadFlag.kill()
        self._console.join()

    def print(self, *args, sep: str = " ", end: str = "\n", style: str | None = None) -> None:
        self.Queue.addQueue(ConsoleQueuePacket("print", *args, sep=sep, end=end, style=style if isinstance(style, str) else ''))

    def input(self, text: str, /) -> str:
        self.Queue.addQueue(ConsoleQueuePacket("input", text, ''))
        self.Queue.returnQueue = None
        while not self.Queue.returnQueue:
            pass
        return self.Queue.returnQueue.removesuffix("\n")

    def clear(self) -> None:
        self.Queue.addQueue(ConsoleQueuePacket('clear'))