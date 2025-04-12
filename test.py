from pathlib import Path

print(Path().home().joinpath("config.json").suffix)