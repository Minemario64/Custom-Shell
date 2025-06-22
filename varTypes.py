import struct
from pathlib import Path

class TypeRegistry(type):
    types: dict = {}
    nicknames: dict[str:str] = {}

    def __new__(cls, name, bases, dct):

        try:
            TypeRegistry.types[name]

        except KeyError:
            newTypeClass = super().__new__(cls, name, bases,  dct)

            try:
                TypeRegistry.nicknames[dct['name']] = name
                TypeRegistry.types[name] = newTypeClass

            except KeyError:
                pass

            return newTypeClass

class VarType(metaclass=TypeRegistry):

    def __init__(self, text: str) -> None:
        raise NotImplementedError

    def __str__(self) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:
        raise NotImplementedError

    def __json__(self) -> bytes:
        raise NotImplementedError

    @staticmethod
    def __jload__(data: bytes) -> str:
        raise NotImplementedError

class StrVar(VarType):
    name: str = 'str'

    def __init__(self, text: str):
        self.value = text

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"'{self.value}'"

    def __json__(self) -> bytes:
        return bytes(self.value, encoding="utf-8")

    @staticmethod
    def __jload__(data: bytes) -> str:
        return data.decode()

class PathVar(VarType):
    name: str = 'path'

    def __init__(self, text: str) -> None:
        self.value = Path(text).resolve()

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return self.__str__()

    def __json__(self) -> bytes:
        return bytes(str(self.value), encoding="utf-8")

    @staticmethod
    def __jload__(data: bytes) -> str:
        return data.decode()

class IntVar(VarType):
    name: str = 'int'

    def __init__(self, text: str) -> None:
        self.value = int(text)

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return self.__str__()

    def __json__(self) -> bytes:
        return bytes([self.value])

    @staticmethod
    def __jload__(data: bytes) -> str:
        return str(int(data.hex(), 16))

class FloatVar(VarType):
    name: str = 'float'

    def __init__(self, text: str) -> None:
        self.value = float(text)

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return self.__str__()

    def __json__(self) -> bytes:
        return struct.pack("d", self.value)

    @staticmethod
    def __jload__(data: bytes) -> str:
        return str(struct.unpack('d', data))