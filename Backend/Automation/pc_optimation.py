import psutil
import subprocess
import os
import shutil
import tempfile
import platform


def optimize_pc() -> str:
    parts = []

    freed = clean_temp_files()
    parts.append(freed)

    killed = kill_background_processes()
    parts.append(killed)

    return " ".join(parts)


def clean_temp_files() -> str:
    freed_space = 0
    temp_dirs = [
        os.environ.get('TEMP', ''),
        os.environ.get('TMP', ''),
        os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Temp'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
    ]

    for temp_dir in temp_dirs:
        if temp_dir and os.path.exists(temp_dir):
            try:
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    try:
                        if os.path.isfile(item_path):
                            freed_space += os.path.getsize(item_path)
                            os.remove(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                    except (PermissionError, OSError):
                        continue
            except Exception:
                continue

    freed_mb = freed_space / (1024 * 1024)
    if freed_mb > 1:
        return f"Cleaned {freed_mb:.1f}MB of temporary files."
    return "Temp files are already clean."


def kill_background_processes() -> str:
    unnecessary = [
        "onedrive.exe", "skype.exe", "slack.exe", "discord.exe",
        "spotify.exe", "teams.exe", "zoom.exe", "dropbox.exe",
        "steam.exe", "epicgameslauncher.exe", "gog.exe",
        "bitorrent.exe", "qbittorrent.exe", "utorrent.exe",
    ]

    killed = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in unnecessary:
                proc.terminate()
                killed.append(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if killed:
        unique = list(set(killed))
        return f"Closed {len(unique)} background programs: {', '.join(unique)}."
    return "No unnecessary background programs found."


def get_startup_programs() -> list[dict]:
    startup = []
    try:
        result = subprocess.run(
            ['powershell', '-c', 'Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location | ConvertTo-Json'],
            capture_output=True, text=True, timeout=10
        )
        if result.stdout.strip():
            import json
            data = json.loads(result.stdout)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                startup.append({
                    "name": item.get("Name", ""),
                    "command": item.get("Command", ""),
                    "location": item.get("Location", ""),
                })
    except Exception:
        pass
    return startup


def check_system_health() -> str:
    issues = []

    cpu = psutil.cpu_percent(interval=0.5)
    if cpu > 80:
        issues.append(f"High CPU usage: {cpu}%")

    ram = psutil.virtual_memory()
    if ram.percent > 80:
        issues.append(f"High RAM usage: {ram.percent}%")

    disk = psutil.disk_usage('/')
    if disk.percent > 90:
        issues.append(f"Low disk space: {disk.free // (1024**3)}GB remaining")

    if not issues:
        return "System health check passed. All systems are running optimally."

    return "System health issues found: " + ". ".join(issues) + "."


def get_battery_status() -> str:
    if not hasattr(psutil, "sensors_battery"):
        return "Battery information not available."

    battery = psutil.sensors_battery()
    if battery is None:
        return "No battery detected."

    percent = battery.percent
    charging = "charging" if battery.power_plugged else "discharging"
    time_left = ""
    if battery.secsleft and battery.secsleft != -1:
        hours = battery.secsleft // 3600
        minutes = (battery.secsleft % 3600) // 60
        time_left = f" ({hours}h {minutes}m remaining)"

    return f"Battery at {percent}%, {charging}{time_left}."
