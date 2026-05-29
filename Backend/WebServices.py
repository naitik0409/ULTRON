import os
import json
import requests
from datetime import datetime
from dotenv import dotenv_values

env = dotenv_values(".env")

WEATHER_API_KEY = env.get("WeatherAPIKey", "")
NEWS_API_KEY = env.get("NewsAPIKey", "")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "Data")


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def get_weather(city: str | None = None) -> str:
    if not city:
        city = "New York"

    if WEATHER_API_KEY:
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                temp = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                humidity = data["main"]["humidity"]
                description = data["weather"][0]["description"]
                wind = data["wind"]["speed"]
                return f"The weather in {city} is {description}. Temperature is {temp:.0f} degrees, feels like {feels_like:.0f}. Humidity is {humidity} percent. Wind speed is {wind} meters per second."
            else:
                return f"Could not fetch weather for {city}."
        except Exception as e:
            return f"Weather service error: {e}"

    try:
        url = f"https://wttr.in/{city}?format=%C+%t+%h+%w"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            text = resp.text.strip()
            return f"The weather in {city}: {text}."
        return f"Could not get weather for {city}."
    except Exception as e:
        return f"Weather service unavailable: {e}"


def get_news(topic: str | None = None, count: int = 5) -> str:
    if NEWS_API_KEY:
        try:
            url = "https://newsapi.org/v2/top-headlines"
            params = {"apiKey": NEWS_API_KEY, "pageSize": count, "language": "en"}
            if topic and topic not in ("news", "headlines", "latest"):
                params["q"] = topic
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                articles = resp.json().get("articles", [])
                if not articles:
                    return "No news articles found."
                parts = [f"Here are the latest headlines:"]
                for i, a in enumerate(articles[:count], 1):
                    title = a.get("title", "")
                    source = a.get("source", {}).get("name", "")
                    parts.append(f"{i}. {title} — {source}")
                return ". ".join(parts) + "."
            return "News service unavailable."
        except Exception as e:
            return f"News error: {e}"

    try:
        url = f"https://newsapi.org/v2/top-headlines?country=us&pageSize={count}&apiKey=demo"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            articles = resp.json().get("articles", [])
            if not articles:
                return "No news found."
            parts = ["Latest headlines:"]
            for i, a in enumerate(articles[:count], 1):
                parts.append(f"{i}. {a.get('title', '')}")
            return ". ".join(parts) + "."
        return "Could not fetch news."
    except Exception as e:
        return f"News unavailable: {e}"


def get_time_for(city: str) -> str:
    try:
        url = f"http://worldtimeapi.org/api/timezone/Etc/GMT"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            dt = data.get("datetime", "")
            return f"The current time is {dt[11:16]}."
        return f"Could not get time for {city}."
    except Exception:
        try:
            from datetime import datetime
            now = datetime.now()
            return f"The current time is {now.strftime('%I:%M %p')}."
        except Exception:
            return "Time service unavailable."


def get_date_info() -> str:
    now = datetime.now()
    return now.strftime("Today is %A, %B %d, %Y.")


def get_stock(symbol: str = "AAPL") -> str:
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            result = data["chart"]["result"][0]
            meta = result["meta"]
            price = meta.get("regularMarketPrice", meta.get("previousClose", "N/A"))
            prev_close = meta.get("previousClose", "N/A")
            currency = meta.get("currency", "USD")
            return f"{symbol} is at {price} {currency}. Previous close was {prev_close}."
        return f"Could not fetch stock data for {symbol}."
    except Exception as e:
        return f"Stock service error: {e}"


def get_ip_info() -> str:
    try:
        resp = requests.get("https://ipapi.co/json/", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            ip = data.get("ip", "Unknown")
            city = data.get("city", "Unknown")
            region = data.get("region", "Unknown")
            country = data.get("country_name", "Unknown")
            isp = data.get("org", "Unknown")
            return f"Your IP is {ip}. Location: {city}, {region}, {country}. ISP: {isp}."
        return "Could not get IP information."
    except Exception as e:
        return f"IP service error: {e}"
