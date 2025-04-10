from commands import *

comm = CommandManager(commands)

def showCWDAndGetInput() -> str:
    return input(f"{str(curdir)}> ")

def main():
    showStartingPrints(True)
    while True:
        ui = showCWDAndGetInput()
        comm.run(ui)

if __name__ == "__main__":
    main()