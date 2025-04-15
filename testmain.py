from testcommands import *

comm = CommandManager(commands)

def main():
    showStartingPrints(True)
    inputLoop(comm)

if __name__ == "__main__":
    main()