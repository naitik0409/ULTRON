import psutil
import platform
import subprocess
import json
import os


def get_system_status() -> str:
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        cpu_freq = psutil.cpu_freq()
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net = psutil.net_io_counters()
        boot_time = psutil.boot_time()
        import datetime
        uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(boot_time)

        parts = [f"System Status Report:"]
        parts.append(f"CPU: {cpu}% used")
        if cpu_freq:
            parts.append(f"{cpu_freq.current:.0f}MHz")
        parts.append(f"RAM: {ram.percent}% used")
        parts.append(f"{ram.available // (1024**3)}GB free of {ram.total // (1024**3)}GB")
        parts.append(f"Disk: {disk.percent}% used")
        parts.append(f"{disk.free // (1024**3)}GB free of {disk.total // (1024**3)}GB")
        parts.append(f"Network: {net.bytes_sent // (1024**2)}MB sent")
        parts.append(f"{net.bytes_recv // (1024**2)}MB received")
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        parts.append(f"Uptime: {hours}h {minutes}m")
        parts.append(f"OS: {platform.system()} {platform.release()}")

        return ". ".join(parts) + "."
    except Exception as e:
        return f"Could not read system status: {e}"


def get_cpu_info() -> dict:
    cpu = psutil.cpu_percent(interval=0.5)
    cpu_freq = psutil.cpu_freq()
    return {
        "usage_percent": cpu,
        "cores": psutil.cpu_count(logical=True),
        "physical_cores": psutil.cpu_count(logical=False),
        "frequency_mhz": cpu_freq.current if cpu_freq else None,
    }


def get_ram_info() -> dict:
    ram = psutil.virtual_memory()
    return {
        "total_gb": round(ram.total / (1024**3), 2),
        "used_gb": round(ram.used / (1024**3), 2),
        "free_gb": round(ram.available / (1024**3), 2),
        "percent_used": ram.percent,
    }


def get_disk_info() -> list[dict]:
    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "device": part.device,
                "mount": part.mountpoint,
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent_used": usage.percent,
            })
        except PermissionError:
            continue
    return disks


def get_installed_apps() -> list[dict]:
    apps = []
    try:
        result = subprocess.run(
            ['powershell', '-c', 'Get-ItemProperty HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Select-Object DisplayName, Publisher, DisplayVersion | ConvertTo-Json'],
            capture_output=True, text=True, timeout=10
        )
        if result.stdout.strip():
            data = json.loads(result.stdout)
            if isinstance(data, dict):
                data = [data]
            for app in data:
                if app.get("DisplayName"):
                    apps.append({
                        "name": app["DisplayName"],
                        "publisher": app.get("Publisher", ""),
                        "version": app.get("DisplayVersion", ""),
                    })
    except Exception:
        pass

    try:
        result = subprocess.run(
            ['powershell', '-c', 'Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Select-Object DisplayName, Publisher, DisplayVersion | ConvertTo-Json'],
            capture_output=True, text=True, timeout=10
        )
        if result.stdout.strip():
            data = json.loads(result.stdout)
            if isinstance(data, dict):
                data = [data]
            for app in data:
                if app.get("DisplayName") and not any(a["name"] == app["DisplayName"] for a in apps):
                    apps.append({
                        "name": app["DisplayName"],
                        "publisher": app.get("Publisher", ""),
                        "version": app.get("DisplayVersion", ""),
                    })
    except Exception:
        pass

    return sorted(apps, key=lambda a: a["name"].lower())


def get_running_processes_count() -> int:
    return len(psutil.pids())
