from commands import *
import sys

comm = CommandManager(commands)

changeToInterpreter(comm)

def runShellFile(filepath : str) -> None:
    with open(filepath, "r") as file:
        commands = [command for command in file.read().split("\n") if len(command) > 0]

    for command in commands:
        comm.run(command)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python Custom-Shell.py <file.cmcs>")
    else:
        runShellFile(sys.argv[1])