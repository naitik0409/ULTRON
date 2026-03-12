from googlesearch import search
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values

try:
    env_vars = dotenv_values(".env")
    Username = env_vars.get("Username", "User")
    Assistantname = env_vars.get("Assistantname", "Assistant")
    GroqAPIKey = env_vars.get("GroqAPIKey")
except Exception:
    Username = "User"
    Assistantname = "Assistant"
    GroqAPIKey = None

# Initialize Groq client only if API key is available
client = Groq(api_key=GroqAPIKey) if GroqAPIKey else None

System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which has real-time up-to-date information from the internet.
*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar.***
*** Just answer the question from the provided data in a professional way. ***"""

try:
    with open(r"Data/ChatLog.json", "r") as f:
        messages = load(f)
except:
    with open(r"Data/ChatLog.json", "w") as f:
        dump([], f)

def GoogleSearch(query: str) -> str:
    """
    Performs a Google search and returns a formatted string of the results.

    Args:
        query (str): The search query.

    Returns:
        str: A formatted string of the search results.
    """
    try:
        results = list(search(query, advanced=True, num_results=5))
        Answer = f"The search results for '{query}' are :\n[start]\n"

        for i in results:
            Answer += f"Title: {i.title}\nDescription: {i.description}\nURL: {i.url}\n\n"

        Answer += "[end]"
        return Answer
    except Exception as e:
        return f"An error occurred during the search: {e}"

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, Sir, how can I help you?"}
]

def Information():
    data = ""
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")
    data += f"Use This Real-time Information if needed:\n"
    data += f"Day: {day}\n"
    data += f"Date: {date}\n"
    data += f"Month: {month}\n"
    data += f"Year: {year}\n"
    data += f"Time: {hour} hours: {minute} minutes: {second} seconds.\n"
    return data

def RealtimeSearchEngine(prompt: str, chat_history: list) -> str:
    """
    Processes a real-time search query using the Groq API and returns the AI's response.

    Args:
        prompt (str): The user's search query.
        chat_history (list): The chat history.

    Returns:
        str: The AI's response.
    """
    if client is None:
        return "AI service is not configured. Please set up your Groq API key in the .env file."

    # Filter out the timestamp from the messages
    filtered_messages = [{"role": msg["role"], "content": msg["content"]} for msg in chat_history]

    SystemChatBot.append({"role": "system", "content": GoogleSearch(prompt)})

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=SystemChatBot + [{"role": "system", "content": Information()}] + filtered_messages,
        max_tokens=2048,
        temperature=0.7,
        top_p=1,
        stream=True,
        stop=None
    )

    Answer = ""

    for chunk in completion:
        if chunk.choices[0].delta.content:
            Answer += chunk.choices[0].delta.content

    Answer = Answer.strip().replace("</s>", "")

    SystemChatBot.pop()
    return AnswerModifier(Answer=Answer)

if __name__ == "__main__":
    while True:
        prompt = input(">>> ")
        print(RealtimeSearchEngine(prompt))