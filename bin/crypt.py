from clicanvas.input.getpass import input as getpass
from clicanvas.input.confirm import input as confirm
from pathlib import Path
from lib import getFlags
import sys

args: list[str] = sys.argv[1:]

def dupWidth(text: str, width: int) -> str:
    repeating, part = divmod(width, len(text))
    return (text*repeating) + text[0:part]

def encypher(data: bytes, amount: int) -> bytes:
    if amount < -255 or amount > 255 or (not isinstance(amount, int)):
        raise ValueError("Cannot encypher - amount must be an integer from -255 to 255")

    return bytes([(byte + amount) % 256 for byte in data])

def decypher(content: bytes, amount: int) -> bytes:
    if amount < -255 or amount > 255 or (not isinstance(amount, int)):
        raise ValueError("Cannot encypher - amount must be an integer from -255 to 255")

    return bytes([(byte - amount) % 256 for byte in content])

def encrypt(data: bytes, key: str) -> bytes:
    p1: bytes = bytes([x ^ y for x, y in zip(data, bytes(dupWidth(key, len(data)), "utf-8"))])
    result: bytes = bytes([x ^ y for x, y in zip([len(data) % 256 for _ in range(len(data))], p1)])
    return result

def decrypt(content: bytes, key: str) -> bytes:
    return bytes([(x ^ y) ^ z for x, y, z in zip(content, [len(content) % 256 for _ in range(len(content))], bytes(dupWidth(key, len(content)), 'utf-8'))])

kwargs: dict = getFlags({"encrypt": ["-e", "--encrypt"], "decrypt": ["-d", "--decrypt"], "change": ["-c", "--change"]}, sys.argv[1:])

if not (len(args) >= 1):
    print(f"\x1b[91mNo file provided. Usage: crypt [-e|-d] <file>\x1b[0m")
    exit(1)

path: Path = Path(kwargs['args'][0])

if not path.is_file():
    print(f"\x1b[91m'{path}' is a directory or it doesn't exist\x1b[0m")
    exit(1)

if kwargs["encrypt"]:

    key: str = getpass("Encryption Key: ")

    with path.open("rb") as unencryptedFile:
        unencryptedText = unencryptedFile.read()

    encryptedText = encrypt(unencryptedText, key)

    try:
        filepath: Path = Path(kwargs['f'])
        filepath.touch()
        with filepath.open("wb") as encryptedFile:
            encryptedFile.write(encryptedText)

    except KeyError:
        inp = confirm("This will override the original file. Do you want to continue (y/n): ")
        if not inp:
            print("Cancelling...")
            exit(1)

        if kwargs["change"]:
            encryptedText = encypher(encryptedText, int(kwargs["change"]))

        with path.open("wb") as encryptedFile:
            encryptedFile.write(encryptedText)

if kwargs['decrypt']:
    key: str = getpass("Encryption Key: ")

    with path.open("rb") as encryptedFile:
        content = encryptedFile.read()

    if kwargs["change"]:
        content = decypher(content, int(kwargs["change"]))

    unencryptedContent = decrypt(content, key)

    try:
        filepath: Path = Path(kwargs['f'])
        filepath.touch()
        with filepath.open("wb") as encryptedFile:
            encryptedFile.write(unencryptedContent)

    except KeyError:
        inp = confirm("This will override the original file. Do you want to continue (y/n): ")
        if not inp:
            print("Cancelling...")
            exit(1)

        with path.open("wb") as encryptedFile:
            encryptedFile.write(unencryptedContent)