import psutil
import subprocess
import os
import signal
from datetime import datetime


def manage_tasks(query: str) -> str:
    query = query.lower().strip()

    if "list" in query or "running" in query or "show" in query or "processes" in query:
        return _list_processes(query)

    if "start" in query or "launch" in query or "run" in query:
        return _start_process(query)

    if "stop" in query or "kill" in query or "end" in query or "close" in query:
        return _stop_process(query)

    if "memory" in query or "ram" in query:
        return _memory_heavy_processes()

    if "cpu" in query:
        return _cpu_heavy_processes()

    return "Task manager commands: list processes, start [name], stop [name], memory usage, cpu usage."


def _list_processes(query: str) -> str:
    try:
        sort_by = "memory"
        if "cpu" in query:
            sort_by = "cpu"
        if "name" in query:
            sort_by = "name"

        limit = 10
        for w in query.split():
            if w.isdigit():
                limit = int(w)
                break

        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
            try:
                pinfo = proc.info
                if pinfo['name']:
                    processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if sort_by == "memory":
            processes.sort(key=lambda p: p.get('memory_percent', 0) or 0, reverse=True)
        elif sort_by == "cpu":
            processes.sort(key=lambda p: p.get('cpu_percent', 0) or 0, reverse=True)
        else:
            processes.sort(key=lambda p: p['name'].lower() if p['name'] else "")

        processes = processes[:limit]
        parts = [f"Top {len(processes)} processes:"]
        for p in processes:
            name = p['name'] or "unknown"
            mem = p.get('memory_percent', 0)
            cpu = p.get('cpu_percent', 0)
            parts.append(f"{name}: {cpu:.1f}% CPU, {mem:.1f}% RAM")

        return ". ".join(parts) + "."
    except Exception as e:
        return f"Could not list processes: {e}"


def _start_process(query: str) -> str:
    for word in query.split():
        if word not in ("start", "launch", "run", "process"):
            try:
                subprocess.Popen(["start", word], shell=True)
                return f"Starting {word}."
            except Exception:
                pass

    cmd = query.replace("start", "").replace("launch", "").replace("run", "").replace("process", "").strip()
    if cmd:
        try:
            subprocess.Popen(["start", cmd], shell=True)
            return f"Starting {cmd}."
        except Exception as e:
            return f"Could not start {cmd}: {e}"
    return "What would you like to start?"


def _stop_process(query: str) -> str:
    target = None
    for word in query.split():
        if word not in ("stop", "kill", "end", "close", "process", "the"):
            target = word
            break

    if not target:
        return "Which process should I stop?"

    killed = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and target.lower() in proc.info['name'].lower():
                proc.terminate()
                killed.append(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if killed:
        unique = list(set(killed))
        return f"Terminated {len(unique)} process(es): {', '.join(unique[:5])}."
    return f"No running process found matching '{target}'."


def _memory_heavy_processes() -> str:
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
        try:
            pinfo = proc.info
            if pinfo['name'] and pinfo.get('memory_percent', 0):
                processes.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    processes.sort(key=lambda p: p.get('memory_percent', 0) or 0, reverse=True)
    top = processes[:5]
    parts = ["Top memory using processes:"]
    for p in top:
        mem_mb = (p.get('memory_percent', 0) / 100) * psutil.virtual_memory().total / (1024**2)
        parts.append(f"{p['name']}: {mem_mb:.0f}MB")

    return ". ".join(parts) + "."


def _cpu_heavy_processes() -> str:
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            pinfo = proc.info
            if pinfo['name']:
                processes.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    processes.sort(key=lambda p: p.get('cpu_percent', 0) or 0, reverse=True)
    top = processes[:5]
    parts = ["Top CPU using processes:"]
    for p in top:
        parts.append(f"{p['name']}: {p.get('cpu_percent', 0):.1f}%")

    return ". ".join(parts) + "."


def schedule_task(query: str) -> str:
    import re
    query = query.lower().strip()

    time_pattern = r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?'
    match = re.search(time_pattern, query)
    time_str = ""
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        ampm = match.group(3)
        if ampm:
            if ampm == "pm" and hour < 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
        time_str = f"{hour:02d}:{minute:02d}"

    message = query
    for prefix in ["remind me to", "remind me that", "remind me", "schedule", "set a reminder for", "set reminder"]:
        if prefix in query:
            message = query.split(prefix, 1)[1].strip()
            break

    if time_str:
        message = re.sub(time_pattern, "", message).strip()
        message = message.strip(" at for to").strip()

        reminder_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "reminders.json")
        import json
        try:
            if os.path.exists(reminder_file):
                with open(reminder_file, "r") as f:
                    reminders = json.load(f)
            else:
                reminders = []
        except (json.JSONDecodeError, FileNotFoundError):
            reminders = []

        reminders.append({
            "time": time_str,
            "message": message,
            "created": datetime.now().isoformat(),
        })

        with open(reminder_file, "w") as f:
            json.dump(reminders, f, indent=2)

        return f"Reminder set for {time_str}: {message}."

    return f"Could not parse the schedule. Please include a time."
