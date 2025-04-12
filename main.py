from commands import *

comm = CommandManager(commands)

initRecording(comm)

def main():
    showStartingPrints(True)
    inputLoop(comm)

if __name__ == "__main__":
    main()