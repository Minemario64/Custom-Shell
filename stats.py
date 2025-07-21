import platform
import cpuinfo
import psutil
from GPUtil import GPU, getGPUs
from functools import cache
import socket as ip
import datetime
import time
from math import floor

def numAsBytesToStr(num: int) -> str:
    power: int = 1024
    unitIdx: int = 0
    units: list[str] = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
    while num >= power and unitIdx < len(units) - 1:
        num /= power
        unitIdx += 1

    return f"{num:.2f} {units[unitIdx]}"

def numAsFrequencyToStr(num: int) -> str:
    power: int = 1000
    unitIdx: int = 0
    units: list[str] = ['Hz', 'KHz', 'MHz', 'GHz']
    while num >= power and unitIdx < len(units) - 1:
        num /= power
        unitIdx += 1

    return f"{num:.2f} {units[unitIdx]}"

def formatSecs(seconds: int) -> str:
    return f"{floor((seconds / 60) / 60)} Hours, {floor((seconds / 60) % 60)} Mins, {seconds % 60} Seconds"

@cache
def _SysStats() -> dict[str, str | int]:
    disk = psutil.disk_usage('/')
    gpus: list[GPU] = getGPUs()
    mem = psutil.virtual_memory()
    SYSTEM_STATISTICS = {"osv": platform.release(), "winv": platform.version(), "hostname": ip.gethostname(), "cpu": {"name": cpuinfo.get_cpu_info()['brand_raw'], "cores": psutil.cpu_count(), "frequency": numAsFrequencyToStr((psutil.cpu_freq().current * 1_000) * 1_000)},
                        "memory": {"total": numAsBytesToStr(mem.total), "used": numAsBytesToStr(mem.used), "free": numAsBytesToStr(mem.free)},
                        "disk": {"total": numAsBytesToStr(disk.total), "used": numAsBytesToStr(disk.used), "free": numAsBytesToStr(disk.free)}, "gpu": gpus[0].name}
    return SYSTEM_STATISTICS

def SystemStats() -> dict[str, str | int]:

    disk = psutil.disk_usage('/')
    mem = psutil.virtual_memory()

    sysstats: dict[str, str | int] = _SysStats()

    sysstats["disk"]["used"] = numAsBytesToStr(disk.used)
    sysstats["disk"]["free"] = numAsBytesToStr(disk.free)
    sysstats["memory"]["total"] = numAsBytesToStr(mem.total)
    sysstats["memory"]["used"] = numAsBytesToStr(mem.used)
    sysstats["memory"]["free"] = numAsBytesToStr(mem.free)
    sysstats['uptime'] = formatSecs(int(time.time() - psutil.boot_time()))


    return sysstats

if __name__ == "__main__":
    print("Initializing...")
    print(SystemStats())

    time.sleep(4)

    print("Running...")
    print(SystemStats())