import platform
import cpuinfo
import psutil
import wmi
from functools import cache
import socket as ip
import datetime
import time
from math import floor

def numAsBytesToStr(num: int | float) -> str:
    power: int = 1024
    unitIdx: int = 0
    units: list[str] = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
    while num >= power and unitIdx < len(units) - 1:
        num //= power
        unitIdx += 1

    return f"{num:.2f} {units[unitIdx]}"

def numAsFrequencyToStr(num: int | float) -> str:
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
def _SysStats() -> dict[str, str | int | dict[str, str | int]]:
    disk = psutil.disk_usage('/')
    gpu = wmi.WMI().Win32_VideoController()[0]
    mem = psutil.virtual_memory()
    SYSTEM_STATISTICS = {"osv": platform.release(), "winv": platform.version(), "hostname": ip.gethostname(), "cpu": {"name": cpuinfo.get_cpu_info()['brand_raw'], "cores": psutil.cpu_count(), "frequency": numAsFrequencyToStr((psutil.cpu_freq().current * 1_000) * 1_000)},
                        "memory": {"total": numAsBytesToStr(mem.total), "used": numAsBytesToStr(mem.used), "free": numAsBytesToStr(mem.free)},
                        "disk": {"total": numAsBytesToStr(disk.total), "used": numAsBytesToStr(disk.used), "free": numAsBytesToStr(disk.free)}, "gpu": gpu.Name}
    return SYSTEM_STATISTICS

def SystemStats() -> dict[str, str | int | dict[str, str | int]]:

    disk = psutil.disk_usage('/')
    mem = psutil.virtual_memory()

    sysstats: dict[str, str | int | dict[str, str | int]] = _SysStats()

    sysstats["disk"]["used"] = numAsBytesToStr(disk.used) # pyright: ignore[reportIndexIssue]
    sysstats["disk"]["free"] = numAsBytesToStr(disk.free) # pyright: ignore[reportIndexIssue]
    sysstats["memory"]["total"] = numAsBytesToStr(mem.total) # pyright: ignore[reportIndexIssue]
    sysstats["memory"]["used"] = numAsBytesToStr(mem.used) # pyright: ignore[reportIndexIssue]
    sysstats["memory"]["free"] = numAsBytesToStr(mem.free) # pyright: ignore[reportIndexIssue]
    sysstats['uptime'] = formatSecs(int(time.time() - psutil.boot_time()))


    return sysstats

if __name__ == "__main__":
    print("Initializing...")
    print(SystemStats())

    time.sleep(4)

    print("Running...")
    print(SystemStats())