import os
import shutil
from datetime import datetime


def file_operation(query: str) -> str:
    query = query.lower().strip()

    if "create folder" in query or "make folder" in query or "create directory" in query or "mkdir" in query:
        words = query.split()
        folder_name = None
        for i, w in enumerate(words):
            if w in ("called", "named", "as", "folder", "directory"):
                folder_name = " ".join(words[i+1:]).strip().strip('"').strip("'")
                break
        if not folder_name and len(words) > 2:
            folder_name = words[-1].strip('"').strip("'")
        if folder_name:
            try:
                os.makedirs(folder_name, exist_ok=True)
                return f"Created folder '{folder_name}'."
            except Exception as e:
                return f"Could not create folder: {e}"
        return "Please specify a folder name."

    if "create file" in query or "make file" in query:
        words = query.split()
        file_name = None
        for i, w in enumerate(words):
            if w in ("called", "named", "as", "file"):
                file_name = " ".join(words[i+1:]).strip().strip('"').strip("'")
                break
        if not file_name and len(words) > 2:
            file_name = words[-1].strip('"').strip("'")
        if file_name:
            try:
                with open(file_name, "w") as f:
                    f.write("")
                return f"Created file '{file_name}'."
            except Exception as e:
                return f"Could not create file: {e}"
        return "Please specify a file name."

    if "delete" in query or "remove" in query:
        words = query.split()
        target = None
        for i, w in enumerate(words):
            if w in ("file", "folder", "directory", "remove", "delete"):
                target = " ".join(words[i+1:]).strip().strip('"').strip("'")
                break
        if not target:
            target = words[-1].strip('"').strip("'")
        if target and target not in (".", ".."):
            try:
                if os.path.isdir(target):
                    shutil.rmtree(target)
                    return f"Deleted folder '{target}'."
                elif os.path.isfile(target):
                    os.remove(target)
                    return f"Deleted file '{target}'."
                else:
                    return f"'{target}' not found."
            except Exception as e:
                return f"Could not delete: {e}"
        return "Please specify what to delete."

    if "rename" in query:
        parts = query.replace("rename", "").strip().split("to")
        if len(parts) == 2:
            old = parts[0].strip().strip('"').strip("'")
            new = parts[1].strip().strip('"').strip("'")
            try:
                os.rename(old, new)
                return f"Renamed '{old}' to '{new}'."
            except Exception as e:
                return f"Could not rename: {e}"
        return "Please specify old name and new name (e.g., rename file.txt to new.txt)."

    if "list" in query or "show files" in query or "what's here" in query:
        target = "."
        for word in query.split():
            if os.path.isdir(word):
                target = word
                break
        try:
            items = os.listdir(target)
            if not items:
                return f"The directory '{target}' is empty."
            file_list = [f for f in items if os.path.isfile(os.path.join(target, f))]
            dir_list = [d for d in items if os.path.isdir(os.path.join(target, d))]
            parts = []
            if dir_list:
                parts.append(f"{len(dir_list)} folders: {', '.join(dir_list[:10])}")
            if file_list:
                parts.append(f"{len(file_list)} files: {', '.join(file_list[:15])}")
            if not parts:
                return f"The directory '{target}' is empty."
            return ". ".join(parts) + "."
        except Exception as e:
            return f"Could not list directory: {e}"

    if "organize" in query or "arrange" in query:
        return _organize_files()

    return f"File operation '{query}' not recognized. Try: create folder, create file, delete, rename, list, or organize."


def _organize_files() -> str:
    try:
        files = [f for f in os.listdir(".") if os.path.isfile(f)]
        if not files:
            return "No files to organize in the current directory."

        ext_map = {}
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if not ext:
                ext = "no_extension"
            if ext not in ext_map:
                ext_map[ext] = []
            ext_map[ext].append(f)

        for ext, ext_files in ext_map.items():
            folder_name = ext[1:] if ext != "no_extension" else "misc"
            if ext == ".jpg" or ext == ".jpeg" or ext == ".png" or ext == ".gif" or ext == ".bmp":
                folder_name = "Images"
            elif ext == ".mp4" or ext == ".mkv" or ext == ".avi" or ext == ".mov":
                folder_name = "Videos"
            elif ext == ".mp3" or ext == ".wav" or ext == ".flac" or ext == ".aac":
                folder_name = "Audio"
            elif ext == ".pdf" or ext == ".doc" or ext == ".docx" or ext == ".txt":
                folder_name = "Documents"
            elif ext == ".zip" or ext == ".rar" or ext == ".7z":
                folder_name = "Archives"
            elif ext == ".py" or ext == ".js" or ext == ".ts" or ext == ".html" or ext == ".css":
                folder_name = "Code"
            elif ext == ".exe" or ext == ".msi":
                folder_name = "Installers"

            os.makedirs(folder_name, exist_ok=True)
            for f in ext_files:
                shutil.move(f, os.path.join(folder_name, f))

        return f"Organized {len(files)} files into categorized folders."
    except Exception as e:
        return f"Could not organize files: {e}"


def advanced_automation(query: str) -> str:
    return file_operation(query)


def realtime_type(text: str) -> str:
    try:
        import keyboard
        import time
        keyboard.write(text, delay=0.02)
        return "Typing completed."
    except ImportError:
        return "Keyboard module not available."
    except Exception as e:
        return f"Error typing: {e}"


def realtime_click(x: int | None = None, y: int | None = None) -> str:
    try:
        import pyautogui
        if x is not None and y is not None:
            pyautogui.click(x, y)
            return f"Clicked at ({x}, {y})."
        else:
            pyautogui.click()
            return "Clicked at current mouse position."
    except ImportError:
        return "PyAutoGUI not available."
    except Exception as e:
        return f"Error clicking: {e}"
