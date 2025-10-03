import tester
import time

def replaceV2(text: str) -> str:
    replaceVars = {
        "~": "C:/Users/Charl",
        "%APPDATA%": "C:/Users/Charl/AppData/Roaming",
        "%LOCALAPPDATA%": "C:/Users/Charl/AppData/Local",
        "%TEMP%": "C:/Users/Charl/AppData/Local/Temp",
        "%TMP%": "C:/Users/Charl/AppData/Local/Temp",
    }
    for name, val in replaceVars.items():
        if text == name:
            text = text.replace(name, val)

        elif text == f"/{name}":
            text = text.replace(f"/{name}", name)

    return text

tester.GLOBALS["replaceV2"] = replaceV2
tester.GLOBALS["time"] = time
tester.describe("ReplaceV2 For Custom-Shell 2.0.0", '''
it("handles empty strings", """
    result = replaceV2("")
    passed(result == "")
""")
it("basic replacement", """
    result = replaceV2("~")
    passed(result == "C:/Users/Charl")
""")
it("Not replacing multi-replacements", """
    result = replaceV2("~ %APPDATA% %LOCALAPPDATA% %TEMP% %TMP%")
    passed(result == "~ %APPDATA% %LOCALAPPDATA% %TEMP% %TMP%")
""")
it("Not replacing escaped replacements", """
    result = replaceV2("/~")
    passed(result == "~")
""")
''')