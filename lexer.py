from enum import IntEnum
from typing import Any
from dataclasses import dataclass
from io import StringIO

class TokenType(IntEnum):
    Text = 0
    Pipe = 2
    RedirectStdout = 3
    And = 4

@dataclass
class Token:
    type: TokenType
    data: Any | None = None

    def __repr__(self) -> str:
        return f"TokenType.{self.type.name}{f":{repr(self.data)}" if not (self.data is None) else ""}"

@dataclass
class CommandToken:
    exe: str
    args: list[str]
    stdin: "CommandToken | str | None" = None
    stdout:  str | None = None

class CshSyntaxError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)

class Lexer:
    def __call__(self, line: str) -> list[Token]:
        res: list[Token] = []
        curTokenText: StringIO = StringIO()
        inQuote: bool = False
        quoteChar: str = ''
        for char in line:
            match char:
                case " ":
                    if curTokenText.getvalue() and (not inQuote):
                        res.append(Token(TokenType.Text, curTokenText.getvalue()))
                        curTokenText = StringIO()

                    elif inQuote:
                        curTokenText.write(char)

                case "|":
                    if not inQuote:
                        res.append(Token(TokenType.Pipe))

                    else:
                        curTokenText.write(char)

                case ">":
                    if not inQuote:
                        res.append(Token(TokenType.RedirectStdout))

                    else:
                        curTokenText.write(char)

                case "&":
                    if not inQuote:
                        res.append(Token(TokenType.And))

                    else:
                        curTokenText.write(char)

                case "'" | '"':
                    if inQuote and char == quoteChar:
                        inQuote = False

                    elif inQuote:
                        curTokenText.write(char)

                    else:
                        quoteChar = char
                        inQuote = True

                case _:
                    curTokenText.write(char)

        if curTokenText.getvalue():
            res.append(Token(TokenType.Text, curTokenText.getvalue()))

        return res

class Parser:
    def __call__(self, tokens: list[Token]) -> list[CommandToken]:
        i = 0
        mode: int = 0
        res: list[CommandToken] = []
        piped: bool = False
        curCommand: CommandToken | None = None
        while i < len(tokens):
            tok = tokens[i]
            if mode == 0 and tok.type == TokenType.Text:
                mode = 1
                curCommand = CommandToken(tok.data, []) # type: ignore
                i += 1
                continue

            match tok.type:
                case TokenType.Text:
                    if mode == 1:
                        curCommand.args.append(tok.data) # type: ignore

                    elif mode == 2:
                        if (curCommand.stdout is None): # type: ignore
                            curCommand.stdout = tok.data # type: ignore

                        else:
                            raise CshSyntaxError("Cannot redirect to multiple thing")

                case TokenType.RedirectStdout:
                    if mode != 1:
                        raise CshSyntaxError("Cannot parse a Redirect Stdout here")

                    mode = 2

                case TokenType.Pipe:
                    if mode == 2:
                        raise CshSyntaxError("Cannot pipe when you are redirecting stdout")

                    if piped:
                        curCommand.stdin = res.pop() # type: ignore

                    mode = 0
                    res.append(curCommand) # type: ignore
                    curCommand = None
                    piped = True

                case TokenType.And:
                    if mode == 0:
                        raise CshSyntaxError("Cannot and a command that doesn't exist")

                    mode = 0
                    if piped:
                        curCommand.stdin = res.pop() # type: ignore

                    res.append(curCommand) # type: ignore

                    piped = False
                    curCommand = None

            i += 1

        if not (curCommand is None):
            if piped:
                curCommand.stdin = res.pop()

            res.append(curCommand)

        return res

if __name__ == "__main__":
    x = Lexer()
    y = Parser()
    while True:
        print(y(x(input("Line: "))))