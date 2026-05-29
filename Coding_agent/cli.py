import sys
import os
from .agentic_ai import CodingAgent
from . import workflow as wf


def handle_command(cmd: str, agent: CodingAgent) -> dict:
    parts = cmd.split(maxsplit=1)
    action = parts[0].lower()
    target = parts[1].strip() if len(parts) > 1 else "."

    if action == "/read":
        result = wf.read_file(target)
        return result

    if action == "/write":
        return {"success": False, "error": "Use natural language to describe what to write, or use /read first.", "needs_content": True}

    if action == "/list":
        result = wf.list_files(target)
        if result["success"]:
            return result
        return wf.read_directory(target)

    if action == "/delete":
        return wf.delete_file(target)

    if action == "/analyze":
        return wf.analyze_file(target)

    return {"success": False, "error": f"Unknown command: {action}. Try /read, /write, /list, /delete, /analyze"}


def display_result(result: dict) -> str:
    rtype = result.get("type", "")

    if rtype == "clarify":
        questions = result.get("questions", [])
        if questions:
            return "I need some clarification. " + " ".join(f" {q}" for q in questions)
        return "Could you clarify what you need?"

    explanation = result.get("explanation") or result.get("response") or result.get("root_cause", "")

    if rtype == "answer":
        return explanation

    parts = []
    if result.get("root_cause"):
        parts.append(f"Root cause: {result['root_cause']}")
    if explanation:
        parts.append(explanation)

    saved = result.get("saved", [])
    if saved:
        parts.append(f"Written {len(saved)} files: {', '.join(saved)}")

    files = result.get("files", {})
    if files and not saved:
        parts.append(f"Generated {len(files)} files: {', '.join(files.keys())}")

    return " ".join(parts) if parts else "Done."


def format_for_speech(result: dict) -> str:
    text = display_result(result)
    sentences = text.split(".")
    if len(sentences) > 3:
        return ". ".join(sentences[:3]) + "."
    return text


def main():
    start_dir = os.getcwd()
    agent = CodingAgent(project_dir=start_dir)
    print(f"  coding agent - {start_dir}")
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
            result = handle_command(raw, agent)
            if result.get("success"):
                if raw.startswith("/read"):
                    print(f"  --- {raw.split(maxsplit=1)[1]} ---")
                    print(f"  {result['content']}")
                elif raw.startswith("/list"):
                    files = result.get("files", [])
                    entries = result.get("entries", [])
                    if files:
                        for f in files:
                            print(f"  {f}")
                    elif entries:
                        for e in entries:
                            marker = "/" if e["type"] == "directory" else ""
                            print(f"  {e['name']}{marker}")
                    if not files and not entries:
                        print("  (empty)")
                elif raw.startswith("/analyze"):
                    target = raw.split(maxsplit=1)[1]
                    print(f"  {target}: {result['size_bytes']} bytes, {result['lines']} lines, {result['extension'] or '(no ext)'}")
                else:
                    print(f"  {result.get('action', 'done')} {raw.split(maxsplit=1)[1]}")
            else:
                print(f"  Error: {result.get('error', 'unknown error')}")
            continue

        result = agent.process(raw)
        print(f"  {display_result(result)}")


if __name__ == "__main__":
    main()
