from pathlib import Path

with Path("meta.txt").open("r") as file:
    content = "\n".join([ln.replace("    ", " ") for ln in file.read().split("\n") if ln != ""])

with Path("meta.txt").open("w") as file:
    file.write(content)