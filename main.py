print("Running...")

from commands import *
import sys

initRecording(comm)

def main():
    showStartingPrints(True)
    release()
    inputLoop(comm)

if __name__ == "__main__":
    sysArgv: list[str] = []
    for i, arg in enumerate(sys.argv[1:]):
        if not arg.startswith("-") and not (arg in KWARGS):
            if not sys.argv[1:][i-1] in NON_BOOL_KWARGS:
                sysArgv.append(arg)

    match len(sysArgv):
        case 0:
            if sys.argv[1:].__contains__("--version"):
                comm.run("echo Custom-Shell Version: [red bold]%V%[/red bold]")
                os._exit(0)

            main()

        case 1:
            os.chdir(cwd)
            path = Path(sysArgv[0]).resolve()
            os.chdir(curdir)

            if path.is_file():
                changeToInterpreter(comm)
                release()
                runShellFile(path)

            elif path.is_dir():
                if 4 in DEBUG_MODE: print(f"cd '{path}'")
                comm.run(f"cd '{path}'")
                main()

            else:
                comm.run(f"{sysArgv[0]}{" && > hold" if sys.argv[1:].__contains__("-k") or sys.argv[1:].__contains__("--keep") else ""}")
                if sys.argv[1:].__contains__("-k") or sys.argv[1:].__contains__("--keep"):
                    main()

        case 2:
            os.chdir(cwd)
            path = Path(sysArgv[0]).resolve()
            os.chdir(curdir)

            if 4 in DEBUG_MODE: print(f"cd '{path}'")
            comm.run(f"cd '{path}'")
            comm.run(f"{sysArgv[1]}{" && > hold" if sys.argv[1:].__contains__("-k") or sys.argv[1:].__contains__("--keep") else ""}")
            if sys.argv[1:].__contains__("-k") or sys.argv[1:].__contains__("--keep"):
                main()

        case _:
            if not DEBUG:
                print(f"Usage: 'Custom-Shell {Version(" ")}.exe' OR 'Custom-Shell {Version(" ")}.exe' <file.csh>")

            else:
                print(f"Usage: python {__file__} OR python {__file__} <file.csh> OR {__file__} <directory> OR {__file__} \"<command>\"")