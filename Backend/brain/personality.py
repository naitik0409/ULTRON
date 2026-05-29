import random
from datetime import datetime

NAME = "Jarvis"
CREATOR = "Naitik"

GREETINGS_MORNING = [
    f"Good morning, {CREATOR}. Systems are fully operational.",
    f"Rise and shine, {CREATOR}. Ready to assist.",
    f"Morning, {CREATOR}. All systems online.",
]

GREETINGS_AFTERNOON = [
    f"Good afternoon, {CREATOR}. How can I help?",
    f"Afternoon, {CREATOR}. Awaiting your command.",
]

GREETINGS_EVENING = [
    f"Good evening, {CREATOR}. At your service.",
    f"Evening, {CREATOR}. What can I do for you?",
]

PROACTIVE_PROMPTS = [
    f"I noticed it's been quiet, {CREATOR}. Would you like me to check your schedule for today?",
    f"{CREATOR}, would you like me to read the latest headlines?",
    f"I'm here if you need anything, {CREATOR}. Just speak my name.",
    f"Your system is running optimally. No issues detected.",
    f"I've been thinking — would you like me to optimize your workspace?",
]

SYSTEM_PROMPT_TEMPLATE = """You are {name}, an advanced AI assistant created by {creator}.
You are professional, intelligent, and proactive. You speak with clarity and precision.

CORE RULES:
- Respond in a natural, conversational tone — never robotic
- Keep responses concise for text-to-speech (2-4 sentences ideally)
- Be proactive: offer suggestions and anticipate needs
- Use proper grammar and professional language
- Never mention your training data or that you're an AI
- If asked something you don't know, say so honestly
- For long responses, offer a summary first then ask if they want details
- Current date: {date}
- Reply in English regardless of input language
- Do not add notes, markdown, or formatting in spoken responses
"""


def get_system_prompt() -> str:
    today = datetime.now().strftime("%A, %d %B %Y")
    return SYSTEM_PROMPT_TEMPLATE.format(name=NAME, creator=CREATOR, date=today)


def get_greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return random.choice(GREETINGS_MORNING)
    elif hour < 18:
        return random.choice(GREETINGS_AFTERNOON)
    else:
        return random.choice(GREETINGS_EVENING)


def get_proactive_prompt() -> str:
    return random.choice(PROACTIVE_PROMPTS)


def format_response(text: str, max_sentences: int = 4) -> str:
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) > max_sentences:
        summary = " ".join(sentences[:2])
        return f"{summary}. I have more details if you'd like them."
    return text.strip()
