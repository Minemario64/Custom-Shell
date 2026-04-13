import time, sys
from lib import getFlags

args: list[str] = sys.argv[1:]
unitMultiplier = 1
if not args:
    print("Usage: sleep <seconds>")
    sys.exit(1)

flags = getFlags({
    "seconds": ["-s", "--seconds"],
    "minutes": ["-m", "--minutes"],
    "hours": ["-h", "--hours"],
    "days": ["-d", "--days"]
}, args)

if flags["minutes"]:
    unitMultiplier = 60

elif flags["hours"]:
    unitMultiplier = 3600

elif flags["days"]:
    unitMultiplier = 86400

elif flags["seconds"]:
    unitMultiplier = 1

try:
    seconds = float(args[0])
    time.sleep(seconds)

except ValueError:
    print(f"Invalid number: '{args[0]}'")
    sys.exit(1)

except KeyboardInterrupt:
    pass