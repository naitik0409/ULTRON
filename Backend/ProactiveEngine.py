import asyncio
import json
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Callable

from Backend.brain import personality
from Backend.WebServices import get_weather, get_news, get_date_info
from Backend.brain.memory import get_recent_chat, get_all_preferences

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "Data")
REMINDERS_FILE = os.path.join(DATA_DIR, "reminders.json")


class ProactiveEngine:
    def __init__(self, username: str = "User"):
        self.username = username
        self._briefing_done_today = False
        self._last_activity = time.time()
        self._idle_threshold = 300
        self._reminder_callbacks: list[Callable] = []
        self._running = False

    def register_reminder_callback(self, callback: Callable):
        self._reminder_callbacks.append(callback)

    def set_idle_threshold(self, seconds: int):
        self._idle_threshold = seconds

    def mark_activity(self):
        self._last_activity = time.time()

    def get_idle_seconds(self) -> float:
        return time.time() - self._last_activity

    def should_proactive(self) -> bool:
        return self.get_idle_seconds() > self._idle_threshold

    def get_briefing(self) -> str:
        parts = [personality.get_greeting()]
        parts.append(get_date_info())

        try:
            weather = get_weather()
            parts.append(weather)
        except Exception:
            pass

        try:
            news = get_news(count=3)
            if len(news) < 100:
                parts.append(news)
        except Exception:
            pass

        reminders = self._get_due_reminders()
        if reminders:
            parts.append(f"You have {len(reminders)} reminder(s) pending.")

        self._briefing_done_today = True
        return " ".join(parts)

    def check_reminders(self) -> list[dict]:
        due = self._get_due_reminders()
        if due:
            self._clear_reminders(due)
        return due

    def _get_due_reminders(self) -> list[dict]:
        try:
            if not os.path.exists(REMINDERS_FILE):
                return []
            with open(REMINDERS_FILE, "r") as f:
                reminders = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

        now = datetime.now()
        due = []
        remaining = []

        for r in reminders:
            try:
                reminder_time = datetime.strptime(r["time"], "%H:%M")
                reminder_time = reminder_time.replace(
                    year=now.year, month=now.month, day=now.day
                )
                if reminder_time <= now:
                    due.append(r)
                else:
                    remaining.append(r)
            except (ValueError, KeyError):
                remaining.append(r)

        with open(REMINDERS_FILE, "w") as f:
            json.dump(remaining, f, indent=2)

        return due

    def _clear_reminders(self, cleared: list[dict]):
        try:
            if not os.path.exists(REMINDERS_FILE):
                return
            with open(REMINDERS_FILE, "r") as f:
                reminders = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return

        cleared_times = {r["time"] for r in cleared}
        remaining = [r for r in reminders if r["time"] not in cleared_times]

        with open(REMINDERS_FILE, "w") as f:
            json.dump(remaining, f, indent=2)

    def get_proactive_suggestion(self) -> str | None:
        idle = self.get_idle_seconds()

        if idle < 60:
            return None

        if idle < 180:
            return None

        if idle < 600:
            return personality.get_proactive_prompt()

        return f"{self.username}, I haven't heard from you in a while. Is there anything I can help with?"

    def get_contextual_prompt(self) -> str | None:
        try:
            prefs = get_all_preferences()
            last_chat = get_recent_chat(5)

            if not last_chat:
                return None

            user_messages = [m["content"] for m in last_chat if m["role"] == "user"]
            if not user_messages:
                return None

            recent_topics = " ".join(user_messages[-3:]).lower()

            if any(w in recent_topics for w in ("weather", "temperature", "rain")):
                return f"{self.username}, would you like today's weather update?"

            if any(w in recent_topics for w in ("news", "headlines", "happening")):
                return f"{self.username}, shall I fetch the latest headlines for you?"

            if any(w in recent_topics for w in ("time", "date", "day")):
                return f"The time is {datetime.now().strftime('%I:%M %p')}. Anything else?"

            return None
        except Exception:
            return None

    def get_reminder_message(self, reminder: dict) -> str:
        return f"Reminder: {reminder.get('message', 'You have a reminder.')}"


proactive = ProactiveEngine()


def get_proactive() -> ProactiveEngine:
    return proactive
