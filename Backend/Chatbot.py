import json  # Ensure the import is used
from json import load, dump
from dotenv import dotenv_values
import requests
import datetime
from groq import Groq

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

messages = []

System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
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

def ChatBot(Query):
    """ This function sends the user's query to the chatbot and returns the AI's response """

    # Check if Groq client is available
    if client is None:
        return "AI service is not configured. Please set up your Groq API key in the .env file."

    try:
        with open(r"Data\ChatLog.json", "r") as f:
            messages = load(f)

        # Filter out timestamps from messages as Groq API doesn't support them
        filtered_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]

        filtered_messages.append({"role": "user", "content": f"{Query}"})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
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

        Answer = Answer.replace("</s>", "")

        return Answer  # Return the answer to the main function

    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        return "Connection error, please try again."
    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred, please try again."

if __name__ == "__main__":
    while True:
        user_input = input("Enter Your Question: ")
        response = ChatBot(user_input)
        print(response)  # Print the response to the user