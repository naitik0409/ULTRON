import sys
import os
from .agentic_ai import CodingAgent
from . import workflow as wf


def handle_command(cmd: str, agent: CodingAgent):
    parts = cmd.split(maxsplit=1)
    action = parts[0].lower()
    target = parts[1].strip() if len(parts) > 1 else "."

    if action == "/read":
        result = wf.read_file(target)
        if result["success"]:
            print(f"  --- {target} ---")
            print(f"  {result['content']}")
            if not result["content"].endswith("\n"):
                print()
        else:
            print(f"  Error: {result['error']}")
        return True

    if action == "/write":
        print("  Paste content. Ctrl+Z then Enter to finish:")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        content = "\n".join(lines)
        result = wf.write_file(target, content)
        if result["success"]:
            print(f"  written {target}")
        else:
            print(f"  Error: {result['error']}")
        return True

    if action == "/list":
        result = wf.list_files(target)
        if result["success"]:
            for f in result["files"]:
                print(f"  {f}")
            if not result["files"]:
                print("  (empty)")
        else:
            r2 = wf.read_directory(target)
            if r2["success"]:
                for e in r2["entries"]:
                    marker = "/" if e["type"] == "directory" else ""
                    print(f"  {e['name']}{marker}")
            else:
                print(f"  Error: {r2['error']}")
        return True

    if action == "/delete":
        result = wf.delete_file(target)
        if result["success"]:
            print(f"  deleted {target}")
        else:
            print(f"  Error: {result['error']}")
        return True

    if action == "/analyze":
        result = wf.analyze_file(target)
        if result["success"]:
            print(f"  {target}: {result['size_bytes']} bytes, {result['lines']} lines, {result['extension'] or '(no ext)'}")
        else:
            print(f"  Error: {result['error']}")
        return True

    return False


def display_result(result: dict):
    rtype = result.get("type", "")

    if rtype == "clarify":
        for q in result.get("questions", []):
            print(f"  ? {q}")
        return

    explanation = result.get("explanation") or result.get("response") or result.get("root_cause", "")

    if rtype == "answer":
        print(f"  {explanation}")
        return

    if result.get("root_cause"):
        print(f"  root cause: {result['root_cause']}")

    if explanation:
        print(f"  {explanation}")

    saved = result.get("saved", [])
    if saved:
        print(f"  written {len(saved)} files:")
        for path in saved:
            print(f"    {path}")

    files = result.get("files", {})
    if files and not saved:
        print(f"  generated {len(files)} files:")
        for path in files:
            print(f"    {path}")


def main():
    start_dir = os.getcwd()
    agent = CodingAgent(project_dir=start_dir)
    print(f"  coding agent — {start_dir}")
    print()

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  goodbye!")
            break

        if not raw:
            continue

        if raw == "/exit":
            print("  goodbye!")
            break

        if raw == "/help":
            print("  /exit              Exit")
            print("  /read <file>       Read a file")
            print("  /write <file>      Write to a file")
            print("  /list [dir]        List files")
            print("  /delete <file>     Delete a file")
            print("  /analyze <file>    Show file stats")
            print("  or just ask what to do in natural language")
            continue

        if raw.startswith("/"):
            handled = handle_command(raw, agent)
            if handled:
                continue
            print(f"  unknown: {raw.split()[0]}. try /help")
            continue

        result = agent.process(raw)
        display_result(result)


if __name__ == "__main__":
    main()
