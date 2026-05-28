import cohere
from dotenv import dotenv_values
from enum import Enum

env_vars = dotenv_values(".env")
CohereAPIKey = env_vars.get("CohereAPIKey")
CohereModel = env_vars.get("CohereModel", "command-r-plus-08-2024")

if not CohereAPIKey:
    print("Warning: CohereAPIKey not found in .env. The decision model will default to 'general' for all queries.")
    co = None
else:
    try:
        co = cohere.Client(api_key=CohereAPIKey)
    except Exception as e:
        print(f"Error initializing Cohere client: {e}")
        co = None


class QueryType(str, Enum):
    EXIT = "exit"
    GENERAL = "general"
    REALTIME = "realtime"
    OPEN = "open"
    CLOSE = "close"
    PLAY = "play"
    GENERATE_IMAGE = "generate image"
    SYSTEM = "system"
    CONTENT = "content"
    GOOGLE_SEARCH = "google search"
    YOUTUBE_SEARCH = "youtube search"
    REMINDER = "reminder"


FUNCTIONS = [t.value for t in QueryType]

preamble = """
You are an accurate decision-making model for a voice assistant named ULTRON AI.
Your ONLY task is to classify the user query into one or more of the categories below.
Do NOT answer the query. Do NOT add explanations. Output ONLY the category label(s).

CATEGORIES:
- general (query) — conversational, opinion, or time/date queries answerable by an LLM without live data
- realtime (query) — queries requiring up-to-date internet information
- open (app/site) — open an application or website
- close (app/site) — close an application
- play (song name) — play a song
- generate image (prompt) — generate an image from a description
- system (task) — system control (mute, unmute, volume up/down)
- content (topic) — write content (code, email, essay, letter)
- google search (topic) — search Google
- youtube search (topic) — search YouTube
- reminder (datetime with message) — set a reminder
- exit — user wants to end the conversation

RULES:
1. For multi-intent queries, output comma-separated categories.
2. If unsure or the task isn't listed, output 'general (query)'.
3. Output as a single line. No markdown. No extra text.

EXAMPLES:
User: how are you ?
Assistant: general how are you ?
User: open chrome and tell me about mahatma gandhi
Assistant: open chrome, general tell me about mahatma gandhi
User: who is the prime minister of india
Assistant: realtime who is the prime minister of india
User: set a reminder at 9pm on 25th june for business meeting
Assistant: reminder 9:00pm 25th june business meeting
User: bye
Assistant: exit
"""

ChatHistory = [
    {"role": "USER", "message": "how are you ?"},
    {"role": "CHATBOT", "message": "general how are you ?"},
    {"role": "USER", "message": "open chrome and tell me about mahatma gandhi"},
    {"role": "CHATBOT", "message": "open chrome, general tell me about mahatma gandhi"},
    {"role": "USER", "message": "open chrome and firefox"},
    {"role": "CHATBOT", "message": "open chrome, open firefox"},
    {"role": "USER", "message": "what is today's date and remind me about dancing performance on 5th at 11pm"},
    {"role": "CHATBOT", "message": "general what is today's date, reminder 11:00pm 5th aug dancing performance"},
]

MAX_RECURSION_DEPTH = 3


def FirstLayerDMM(prompt: str = "test", _depth: int = 0) -> list[str]:
    if co is None:
        return ["general " + prompt]

    if _depth >= MAX_RECURSION_DEPTH:
        return ["general " + prompt]

    try:
        response = co.chat(
            model=CohereModel,
            message=prompt,
            temperature=0.7,
            chat_history=ChatHistory,
            prompt_truncation='OFF',
            connectors=[],
            preamble=preamble
        )

        raw = response.text.replace("\n", "").split(",")
        raw = [item.strip() for item in raw]

        result = [item for item in raw if any(item.startswith(func) for func in FUNCTIONS)]

        if not result:
            if "(query)" in raw:
                return FirstLayerDMM(prompt=prompt, _depth=_depth + 1)
            return ["general " + prompt]

        return result

    except Exception as e:
        print(f"Error in FirstLayerDMM: {e}")
        return ["general " + prompt]


if __name__ == "__main__":
    while True:
        print(FirstLayerDMM(input(">>> ")))
