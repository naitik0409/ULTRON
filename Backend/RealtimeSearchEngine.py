from tavily import TavilyClient
from bs4 import BeautifulSoup
from groq import Groq
from json import load, dump
import datetime
import requests
import itertools
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")
GroqAPIKey = env_vars.get("GroqAPIKey")
GroqSearchModel = env_vars.get("GroqSearchModel", "llama-3.1-8b-instant")
GroqSearchFallback = env_vars.get("GroqSearchFallback", "llama-3.3-70b-versatile")

client = Groq(api_key=GroqAPIKey) if GroqAPIKey else None

TavilyAPIKey1 = env_vars.get("TavilyAPIKey1")
TavilyAPIKey2 = env_vars.get("TavilyAPIKey2")
tavily_keys = [k for k in [TavilyAPIKey1, TavilyAPIKey2] if k]
tavily_clients = [TavilyClient(api_key=k) for k in tavily_keys] if tavily_keys else []
key_cycle = itertools.cycle(tavily_clients) if tavily_clients else None

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

System = f"""You are {Assistantname}, a professional research assistant for {Username}. You synthesize search results into clear, accurate answers.

CORE RULES:
- Answer based only on the provided search results
- Cite sources naturally when relevant
- Be concise and professional
- If the search results don't contain the answer, say so
- Never mention your training data or that you're an AI
"""

try:
    with open(r"Data/ChatLog.json", "r") as f:
        messages = load(f)
except:
    with open(r"Data/ChatLog.json", "w") as f:
        dump([], f)


def scrape_page(url: str, max_chars: int = 2000) -> str | None:
    try:
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:max_chars]
    except Exception:
        return None


def TavilySearch(query: str) -> str:
    if not tavily_clients:
        return f"No Tavily API keys configured. Please set TavilyAPIKey1 in .env"

    client_instance = next(key_cycle)
    response = client_instance.search(query=query, search_depth="advanced", max_results=5)
    results = response.get("results", [])

    answer = f"The search results for '{query}' are :\n[start]\n"

    for r in results[:3]:
        title = r.get("title", "")
        url = r.get("url", "")
        snippet = r.get("content", "")

        full_content = scrape_page(url)
        content = full_content if full_content else snippet

        answer += f"Title: {title}\nURL: {url}\nContent: {content}\n\n"

    answer += "[end]"
    return answer


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


def _search_query(model: str, prompt: str, chat_history: list) -> str:
    filtered_messages = [{"role": msg["role"], "content": msg["content"]} for msg in chat_history]

    SystemChatBot.append({"role": "system", "content": TavilySearch(prompt)})

    completion = client.chat.completions.create(
        model=model,
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


def RealtimeSearchEngine(prompt: str, chat_history: list) -> str:
    if client is None:
        return "AI service is not configured. Please set up your Groq API key in the .env file."

    models = [GroqSearchModel, GroqSearchFallback]

    for model in models:
        try:
            return _search_query(model, prompt, chat_history)
        except Exception as e:
            print(f"Groq error on {model}: {e}")
            continue

    return "AI service is currently unavailable. Please try again later."


if __name__ == "__main__":
    while True:
        prompt = input(">>> ")
        print(RealtimeSearchEngine(prompt))
