from cshApi import getStdout

def launcher(args: list[str]):
    print("Launchung pytan...")
    stdout = getStdout()
    stdout.write("HeHe, secret message\n")

def pyrun(args: list[str]):
    print("Running 'python'...")

def pyrun3(args: list[str]):
    print("Linux I see...")