from rich.console import Console

cli = Console()

dct = {"args": ["Hello, World!"], "-color": "yellow"}

def println(**kwargs) -> None:
    if kwargs["args"] == None:
        cli.print("The command [bold][cyan]print[/bold][/cyan] needs at least one argument.")
        return None

    defaultArgs = {"s": " ", "-color": None}
    for arg, default in defaultArgs.items():
        try:
            kwargs[arg]
        except KeyError:
            kwargs[arg] = default
    cli.print(*tuple(kwargs["args"]), sep=kwargs["s"], style=kwargs["-color"])

println(**dct)