from pathlib import Path
from json import load, dumps, dump
import os
import time

def parse(text: str) -> list[str]:
    splitText = text.split(" ")
    txtIn = 0
    inTxt = ''
    quoteIdx = [0, 0]
    chars = ["", ""]
    parsedText = splitText.copy()
    for txt in splitText:
        if txtIn > 0:
            parsedText.remove(txt)
        for ltxt in list(txt):
            if ltxt == '"' or ltxt == "'":
                if inTxt == ltxt:
                    if txtIn == 2:
                        txtIn -= 1
                        inTxt = '"' if ltxt == "'" else "'"
                    elif txtIn == 1:
                        parsedText.insert(quoteIdx[txtIn - 1], chars[txtIn - 1])
                        txtIn -= 1
                        inTxt = ''
                else:
                    quoteIdx[txtIn] = splitText.index(txt)
                    print(quoteIdx)
                    parsedText.remove(txt)
                    txtIn += 1
                    inTxt = ltxt
            elif txtIn > 0:
                chars[txtIn - 1] += ltxt
        if txtIn > 0:
            chars[txtIn - 1] += " "
    return parsedText

comText = 'print "Hello, World!"'
print(parse(comText))