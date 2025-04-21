from testcommands import *

comm = CommandManager(commands)

initRecording(comm)

def main():
    showStartingPrints(True)
    release()
    inputLoop(comm)

if __name__ == "__main__":
    main()