import subprocess
import os
import shlex


def open_application(query: str) -> str:
    query = query.lower().strip()

    app_map = {
        "chrome": "chrome",
        "google chrome": "chrome",
        "browser": "chrome",
        "firefox": "firefox",
        "edge": "msedge",
        "notepad": "notepad",
        "calculator": "calc",
        "cmd": "cmd",
        "command prompt": "cmd",
        "terminal": "cmd",
        "explorer": "explorer",
        "file explorer": "explorer",
        "settings": "ms-settings:",
        "control panel": "control",
        "task manager": "taskmgr",
        "vscode": "code",
        "visual studio code": "code",
        "paint": "mspaint",
        "snipping tool": "snippingtool",
        "word": "winword",
        "excel": "excel",
        "powerpoint": "powerpnt",
        "outlook": "outlook",
        "spotify": "spotify",
        "vlc": "vlc",
        "discord": "discord",
        "slack": "slack",
        "zoom": "zoom",
        "calculator": "calc",
    }

    for name, command in app_map.items():
        if name in query:
            try:
                if command.endswith(":"):
                    subprocess.Popen(["start", command], shell=True)
                else:
                    subprocess.Popen(["start", command], shell=True)
                return f"Opening {name.title()}."
            except Exception as e:
                return f"Could not open {name}: {e}"

    return f"I don't know how to open '{query}'. You can add it to the application list."


def close_application(query: str) -> str:
    query = query.lower().strip()

    app_map = {
        "chrome": "chrome.exe",
        "google chrome": "chrome.exe",
        "browser": "chrome.exe",
        "firefox": "firefox.exe",
        "edge": "msedge.exe",
        "notepad": "notepad.exe",
        "calculator": "calculator.exe",
        "cmd": "cmd.exe",
        "explorer": "explorer.exe",
        "vscode": "code.exe",
        "visual studio code": "code.exe",
        "paint": "mspaint.exe",
        "word": "winword.exe",
        "excel": "excel.exe",
        "powerpoint": "powerpnt.exe",
        "spotify": "spotify.exe",
        "vlc": "vlc.exe",
        "discord": "discord.exe",
        "slack": "slack.exe",
        "zoom": "zoom.exe",
        "task manager": "taskmgr.exe",
        "settings": "SystemSettings.exe",
    }

    for name, process in app_map.items():
        if name in query:
            try:
                subprocess.run(["taskkill", "/f", "/im", process], capture_output=True, text=True)
                return f"Closed {name.title()}."
            except Exception as e:
                return f"Could not close {name}: {e}"

    return f"I don't know how to close '{query}'."


def play_media(query: str) -> str:
    query = query.lower().strip()

    if "pause" in query or "stop" in query:
        try:
            import keyboard
            keyboard.press_and_release("space")
            return "Pausing media."
        except ImportError:
            return "Keyboard module not installed for media control."

    if "next" in query or "skip" in query:
        try:
            import keyboard
            keyboard.press_and_release("next track")
            return "Skipping to next track."
        except ImportError:
            return "Keyboard module not installed."

    if "previous" in query or "back" in query:
        try:
            import keyboard
            keyboard.press_and_release("previous track")
            return "Going back to previous track."
        except ImportError:
            return "Keyboard module not installed."

    if "volume up" in query or "increase volume" in query:
        try:
            import keyboard
            keyboard.press_and_release("volume up")
            return "Increasing volume."
        except ImportError:
            return "Keyboard module not installed."

    if "volume down" in query or "decrease volume" in query:
        try:
            import keyboard
            keyboard.press_and_release("volume down")
            return "Decreasing volume."
        except ImportError:
            return "Keyboard module not installed."

    if "mute" in query:
        try:
            import keyboard
            keyboard.press_and_release("volume mute")
            return "Toggling mute."
        except ImportError:
            return "Keyboard module not installed."

    try:
        subprocess.Popen(["start", query], shell=True)
        return f"Trying to play {query}."
    except Exception as e:
        return f"Could not play media: {e}"


def system_control(query: str) -> str:
    query = query.lower().strip()

    if "shutdown" in query or "turn off" in query:
        try:
            subprocess.run(["shutdown", "/s", "/t", "10"], capture_output=True)
            return "System will shut down in 10 seconds. Say 'cancel shutdown' to abort."
        except Exception as e:
            return f"Could not shutdown: {e}"

    if "restart" in query or "reboot" in query:
        try:
            subprocess.run(["shutdown", "/r", "/t", "10"], capture_output=True)
            return "System will restart in 10 seconds."
        except Exception as e:
            return f"Could not restart: {e}"

    if "cancel shutdown" in query or "abort" in query:
        try:
            subprocess.run(["shutdown", "/a"], capture_output=True)
            return "Shutdown cancelled."
        except Exception as e:
            return f"Could not cancel: {e}"

    if "sleep" in query or "hibernate" in query:
        try:
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], capture_output=True)
            return "Putting system to sleep."
        except Exception as e:
            return f"Could not sleep: {e}"

    if "lock" in query:
        try:
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], capture_output=True)
            return "Locking the system."
        except Exception as e:
            return f"Could not lock: {e}"

    if "log off" in query or "sign out" in query or "logout" in query:
        try:
            subprocess.run(["shutdown", "/l"], capture_output=True)
            return "Signing out."
        except Exception as e:
            return f"Could not sign out: {e}"

    if "brightness" in query:
        try:
            import screen_brightness_control as sbc
            if "up" in query or "increase" in query:
                current = sbc.get_brightness()[0]
                sbc.set_brightness(min(current + 20, 100))
                return f"Increased brightness to {min(current + 20, 100)} percent."
            elif "down" in query or "decrease" in query:
                current = sbc.get_brightness()[0]
                sbc.set_brightness(max(current - 20, 0))
                return f"Decreased brightness to {max(current - 20, 0)} percent."
            else:
                words = query.split()
                for w in words:
                    if w.isdigit():
                        sbc.set_brightness(int(w))
                        return f"Brightness set to {w} percent."
                current = sbc.get_brightness()[0]
                return f"Current brightness is {current} percent."
        except ImportError:
            return "Screen brightness control not available. Install with: pip install screen-brightness-control"

    return f"System control command '{query}' not recognized."
