# Custom-Shell

A custom, bash-like shell in python that takes inspiration from both bash, and windows shells like powershell and cmd.

## How to Install

Ways to Use Custom-Shell:
1. Get the latest release from github releases
2. Clone the main branch and setup a virtual environment with the dependencies in `pyproject.toml` and python >= 3.13. Then run main.py

### Known Issues

If you are using uv and cloned this project and just run `uv run main.py`, the project with automatically clear the screen on 'startup' (when you run it). Idk how to actually fix it, but go into `[venv path]/Lib/site-packages/clicanvas-[VERSION].dist-info/METADATA` and remove the line that says `Provides-Extra: thonny`.

## How to Contribute

TODO: Make contribution path and instructions