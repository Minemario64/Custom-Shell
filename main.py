from commands import *

comm = CommandManager(commands)

def main():
    showStartingPrints(True)
    while True:
        ui = showCWDAndGetInput()
        comm.run(ui)

if __name__ == "__main__":
    main()