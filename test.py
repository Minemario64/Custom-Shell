from asciiart import fixedWidth, display
from rich.console import Console
from stats import SystemStats
from commands import Version

cli = Console(highlight=False)
stats = SystemStats()

displayStats = {"Windows Version": stats['osv'], "Kernel Build": stats['winv'], "Uptime": stats['uptime'], "Custom-Shell Version": Version("-"),
                "CPU": f"{stats['cpu']['name']} @ {stats['cpu']['frequency']}", "GPU": stats['gpu'],
                "Memory": f"{stats['memory']['used']} / {stats['memory']['total']}", "Disk": f"{stats['disk']['used']} / {stats['disk']['total']}"}

tst = f"""
  [green bold]Charl[/green bold]@[blue bold]{stats["hostname"]}[/blue bold]
{"-"*(len(f"Charl@{stats['hostname']}") + 4)}
 {"\n ".join([f"[blue bold]{stat}[/blue bold]: {val}" for stat, val in displayStats.items()])}"""

cli.print(display.HorizontalLayout("windows-11", "left").combineText(tst, "blue bold"))