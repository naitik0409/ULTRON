from . import memory
from . import personality
from datetime import datetime
import psutil


def get_system_context() -> str:
    parts = []
    now = datetime.now()
    parts.append(f"Current time: {now.strftime('%A, %d %B %Y, %H:%M:%S')}")

    try:
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        parts.append(f"System: CPU {cpu}%, RAM {ram.percent}% used ({ram.available // (1024**3)}GB free), Disk {disk.percent}% used ({disk.free // (1024**3)}GB free)")
    except Exception:
        parts.append("System: unable to read system stats")

    return "\n".join(parts)


def build_context(
    query: str,
    short_term: list[dict],
    intent: dict | None = None,
    include_system: bool = True,
    include_facts: bool = True,
    include_preferences: bool = True,
    include_history: bool = True,
) -> list[dict]:
    messages = []

    system_prompt = personality.get_system_prompt()
    context_parts = [system_prompt]

    if include_system:
        context_parts.append(f"\n[SYSTEM CONTEXT]\n{get_system_context()}")

    if include_preferences:
        prefs = memory.get_all_preferences()
        if prefs:
            pref_str = "\n".join(f"{k}: {v}" for k, v in prefs.items())
            context_parts.append(f"\n[USER PREFERENCES]\n{pref_str}")

    if include_facts:
        facts = memory.get_relevant_facts(query, limit=8)
        if facts:
            fact_str = "\n".join(f"{f['key']}: {f['value']}" for f in facts)
            context_parts.append(f"\n[KNOWN FACTS]\n{fact_str}")

    messages.append({"role": "system", "content": "\n".join(context_parts)})

    if include_history and short_term:
        for msg in short_term[-15:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": query})

    return messages
