import json
from json import load, dump
from dotenv import dotenv_values
import datetime
from groq import Groq

env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")
GroqAPIKey = env_vars.get("GroqAPIKey")
GroqChatModel = env_vars.get("GroqChatModel", "llama-3.3-70b-versatile")
GroqChatFallback = env_vars.get("GroqChatFallback", "llama-3.1-8b-instant")

client = Groq(api_key=GroqAPIKey) if GroqAPIKey else None

messages = []

System = f"""You are {Assistantname}, a professional AI assistant created for {Username}. You are precise, intelligent, and conversational.

CORE RULES:
- Respond naturally and professionally — concise but complete
- Answer in English regardless of input language
- Never mention your training data or that you're an AI
- Do not add notes, markdown, or formatting
- Keep responses well-structured and clear
- *** Use the conversation history for context. The user may ask follow-up questions that refer to previous messages (e.g. "what about monday?" refers to a topic discussed earlier). ALWAYS look at recent messages to understand the context. ***
- If the query is unclear on its own, infer the meaning from the conversation history
"""

SystemChatBot = [
    {"role": "system", "content": System}
]

try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
except FileNotFoundError:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)
except json.JSONDecodeError:
    print("ChatLog.json is empty or corrupted. Initializing with an empty list.")
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)

def RealtimeInformation():
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")

    data = f"Please use this real-time information if needed:\n"
    data += f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Time: {hour} hours, {minute} minutes, {second} seconds.\n"
    return data

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

def _chat_query(model: str, query: str) -> str:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)

    filtered_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
    filtered_messages.append({"role": "user", "content": f"{query}"})

    completion = client.chat.completions.create(
        model=model,
        messages=SystemChatBot + [{"role": "system", "content": RealtimeInformation()}] + filtered_messages,
        max_tokens=1024,
        temperature=0.7,
        top_p=1,
        stream=True,
        stop=None
    )

    Answer = ""
    for chunk in completion:
        if chunk.choices[0].delta.content:
            Answer += chunk.choices[0].delta.content

    return Answer.replace("</s>", "")

def ChatBot(Query):
    if client is None:
        return "AI service is not configured. Please set up your Groq API key in the .env file."

    models = [GroqChatModel, GroqChatFallback]

    for model in models:
        try:
            return _chat_query(model, Query)
        except Exception as e:
            print(f"Groq error on {model}: {e}")
            continue

    return "AI service is currently unavailable. Please try again later."

if __name__ == "__main__":
    while True:
        user_input = input("Enter Your Question: ")
        response = ChatBot(user_input)
        print(response)  # Print the response to the user