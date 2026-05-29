from dotenv import dotenv_values
import asyncio
import os

from Backend.TextToSpeech import TextToSpeech, TTS
from Backend.STT import SpeechRecognition, voice_analysis
from Backend.STT.recorder import record_audio
from Backend.MicControl import is_active, start_listener
from Backend.brain import Brain
from Backend.brain.memory import store_chat_message, initialize_chat_log
from Coding_agent.agentic_ai import CodingAgent
from Coding_agent.cli import handle_command, format_for_speech

env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")

initialize_chat_log()
brain = Brain(username=Username, assistant_name=Assistantname)
coding_agent = CodingAgent(project_dir=os.getcwd())
brain.load_coding_agent(coding_agent)


async def handle_coding_mode():
    print(f"\n  {Assistantname}: Coding mode active. Speak naturally or type your request.")
    print(f"  Commands: /read, /write, /list, /delete, /analyze, /exit to return to voice")
    print()

    while True:
        try:
            print("  [coding] ", end="", flush=True)
            raw = input().strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not raw:
            continue

        if raw == "/exit":
            print(f"  Returning to voice mode.")
            break

        if raw.startswith("/"):
            result = handle_command(raw, coding_agent)
            if result.get("success"):
                if raw.startswith("/read"):
                    print(f"  --- {raw.split(maxsplit=1)[1]} ---")
                    print(f"  {result['content']}")
                elif raw.startswith("/list"):
                    files = result.get("files", [])
                    if files:
                        for f in files:
                            print(f"  {f}")
                    else:
                        entries = result.get("entries", [])
                        if entries:
                            for e in entries:
                                marker = "/" if e["type"] == "directory" else ""
                                print(f"  {e['name']}{marker}")
                        else:
                            print("  (empty)")
                elif raw.startswith("/analyze"):
                    target = raw.split(maxsplit=1)[1]
                    print(f"  {target}: {result['size_bytes']} bytes, {result['lines']} lines, {result['extension'] or '(no ext)'}")
                else:
                    target = raw.split(maxsplit=1)[1] if len(raw.split()) > 1 else ""
                    print(f"  {result.get('action', 'done')} {target}")
            else:
                print(f"  Error: {result.get('error', 'unknown error')}")
                if result.get("needs_content"):
                    print("  Paste content. Ctrl+Z then Enter to finish:")
                    lines = []
                    try:
                        while True:
                            line = input()
                            lines.append(line)
                    except EOFError:
                        pass
                    content = "\n".join(lines)
                    from Coding_agent import workflow as wf
                    target = raw.split(maxsplit=1)[1] if len(raw.split()) > 1 else "output.txt"
                    res = wf.write_file(target, content)
                    if res["success"]:
                        print(f"  written {target}")
                    else:
                        print(f"  Error: {res['error']}")
            continue

        result = coding_agent.process(raw)
        speech = format_for_speech(result)
        print(f"  {Assistantname}: {speech}")

        if result.get("saved") or result.get("files"):
            print(f"  {Assistantname}: I've written the files. Type /read to review them, or keep describing what you want.")

        if len(speech) < 200:
            try:
                await TextToSpeech(speech)
            except Exception:
                pass


async def main():
    start_listener()
    print(f"  {Assistantname} — voice assistant")
    print("  " + "-" * 40)
    print("  Ctrl+Shift+M  toggle mic  |  say 'exit' to quit")
    print()

    greeting = brain.get_greeting()
    print(f"  {Assistantname}: {greeting}")
    try:
        await TextToSpeech(greeting)
    except Exception:
        pass

    idle_counter = 0

    while True:
        try:
            if not is_active():
                print("  . sleep mode (Ctrl+Shift+M to wake)")
                while not is_active():
                    await asyncio.sleep(0.5)

            print("  > Listening...")

            audio = record_audio(duration=5)
            if audio is not None:
                voice_analysis.analyze(audio)

            user_input = SpeechRecognition().strip()

            if not user_input:
                idle_counter += 1
                if idle_counter >= 30:
                    proactive = brain.get_proactive_prompt()
                    print(f"  {Assistantname}: {proactive}")
                    try:
                        await TextToSpeech(proactive)
                    except Exception:
                        pass
                    idle_counter = 0
                continue

            idle_counter = 0

            print(f"\n  {Username}: {user_input}")

            voice_summary = voice_analysis.get_summary()
            if voice_summary:
                augmented_input = f"{user_input} [voice: {voice_summary}]"
            else:
                augmented_input = user_input

            result = brain.process(augmented_input)

            if result["action"] == "exit":
                print(f"\n  {Assistantname}: {result['response']}")
                try:
                    await TextToSpeech(result['response'])
                except Exception:
                    pass
                break

            if result["coding"]:
                await handle_coding_mode()
                print()
                continue

            response = result["response"]
            print(f"  {Assistantname}: {response}")

            if response:
                try:
                    await TextToSpeech(response)
                except Exception as e:
                    print(f"TTS Error: {e}")

        except KeyboardInterrupt:
            print(f"\n  Goodbye, {Username}!")
            break
        except Exception as e:
            print(f"\n  Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
