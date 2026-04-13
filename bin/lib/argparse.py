def getFlags(flags: dict[str, list[str]], args: list[str]) -> dict[str, bool]:
    res: dict[str, bool] = {flag: False for flag in flags}
    for flag, aliases in flags.items():
        for alias in aliases:
            while alias in args:
                res[flag] = True
                args.remove(alias)

    return res

def getKwArgs(kwArgs: dict[str, list[str]], args: list[str]) -> dict[str, str | None]:
    res: dict[str, str | None] = {kwArg: None for kwArg in kwArgs}
    for kwArg, aliases in kwArgs.items():
        for alias in aliases:
            if alias in args:
                index = args.index(alias)
                if index + 1 < len(args):
                    res[kwArg] = args[index + 1]
                    del args[index:index + 2]

    return res