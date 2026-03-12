# FastAPI Web Server for HTML GUI Integration
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import json
import asyncio
import os
import subprocess
from typing import List, Dict, Any
from datetime import datetime

# Backend modules integration
from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech, TTS
from dotenv import dotenv_values

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")

DefaultMessage = f""" {Username}: Hello {Assistantname}, How are you?
{Assistantname}: Welcome {Username}. I am doing well. How may I help you? """

functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]
subprocess_list = []
tts_process = None

# FastAPI App Initialization
app = FastAPI(title="ULTRON AI Assistant", description="AI Assistant with Web Interface")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="Data"), name="static")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str

class TTSRequest(BaseModel):
    text: str


# Chat Management Functions
def ensure_data_directory():
    """Ensure the Data directory exists"""
    os.makedirs("Data", exist_ok=True)

def initialize_chat_log():
    """Initialize chat log if it doesn't exist or is empty"""
    ensure_data_directory()
    chat_log_path = r'Data\ChatLog.json'

    try:
        if not os.path.exists(chat_log_path):
            with open(chat_log_path, "w", encoding='utf-8') as file:
                json.dump([], file)
            return []

        with open(chat_log_path, 'r', encoding='utf-8') as file:
            chat_data = json.load(file)
            return chat_data if chat_data else []
    except (FileNotFoundError, json.JSONDecodeError):
        print("ChatLog.json not found or corrupted. Creating new one.")
        with open(chat_log_path, "w", encoding='utf-8') as file:
            json.dump([], file)
        return []

def save_chat_message(role: str, content: str):
    """Save a chat message to the log"""
    chat_data = initialize_chat_log()
    chat_data.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })

    with open(r'Data\ChatLog.json', 'w', encoding='utf-8') as file:
        json.dump(chat_data, file, indent=2, ensure_ascii=False)

def get_formatted_chat_history() -> str:
    """Get formatted chat history for context"""
    chat_data = initialize_chat_log()
    formatted_history = ""

    for entry in chat_data[-20:]:  # Last 20 messages for context
        if entry["role"] == "user":
            formatted_history += f"{Username}: {entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted_history += f"{Assistantname}: {entry['content']}\n"

    return formatted_history

# Initialize chat log on startup
initialize_chat_log()

# AI Processing Logic
async def process_ai_query(query: str) -> str:
    """Process user query through AI decision making and return response"""
    try:
        # Make AI decision
        Decision = FirstLayerDMM(query)
        print(f"AI Decision: {Decision}")

        TaskExecution = False
        ImageExecution = False
        ImageGenerationQuery = ""

        # Check for different decision types
        G = any([i for i in Decision if i.startswith("general")])
        R = any([i for i in Decision if i.startswith("realtime")])

        # Merge queries for search
        Merged_query = " and ".join(
            [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
        )

        # Handle image generation
        for queries in Decision:
            if "generate" in queries:
                ImageGenerationQuery = str(queries)
                ImageExecution = True

        # Handle automation tasks
        for queries in Decision:
            if not TaskExecution:
                if any(queries.startswith(func) for func in functions):
                    try:
                        await Automation(list(Decision))
                        TaskExecution = True
                        # Return confirmation message instead of continuing to chatbot
                        return f"Task executed successfully: {', '.join([q for q in Decision if any(q.startswith(func) for func in functions)])}"
                    except Exception as e:
                        print(f"Error in automation: {e}")
                        return f"Failed to execute automation task: {e}"

        # Start image generation if needed
        if ImageExecution:
            try:
                os.makedirs("Frontend/Files", exist_ok=True)
                with open(r'Frontend\Files\ImageGeneration.data', "w") as file:
                    file.write(f"{ImageGenerationQuery},True")

                subprocess.Popen(
                    ['python', r"Backend\ImageGeneration.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    shell=False,
                )
            except Exception as e:
                print(f"Error starting ImageGeneration.py: {e}")

        # Process query based on type
        if G and R or R:
            # Real-time search
            chat_data = initialize_chat_log()
            Answer = RealtimeSearchEngine(Merged_query, chat_data)
        else:
            # Process individual decisions
            for queries in Decision:
                if "general" in queries:
                    QueryFinal = queries.replace("general", "")
                    Answer = ChatBot(QueryFinal)
                    break
                elif "realtime" in queries:
                    QueryFinal = queries.replace("realtime", "")
                    chat_data = initialize_chat_log()
                    Answer = RealtimeSearchEngine(QueryFinal, chat_data)
                    break
                elif "exit" in queries:
                    Answer = ChatBot("Okay, Bye!")
                    # Could add exit logic here if needed
                    break
            else:
                Answer = ChatBot(query)  # Fallback to general chatbot

        return Answer

    except Exception as e:
        print(f"Error in AI processing: {e}")
        return f"Sorry, I encountered an error: {str(e)}"

# WebSocket endpoint for real-time communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "chat":
                user_message = data.get("message", "").strip()
                if not user_message:
                    continue

                # Save user message
                save_chat_message("user", user_message)

                # Process through AI
                ai_response = await process_ai_query(user_message)

                # Save AI response
                save_chat_message("assistant", ai_response)

                # Send response back via WebSocket
                response_data = {
                    "type": "chat_response",
                    "assistant": Assistantname,
                    "message": ai_response
                }
                await websocket.send_json(response_data)

            elif data.get("type") == "stt_result":
                # Handle speech-to-text results from browser
                text = data.get("text", "").strip()
                if text:
                    stt_data = {
                        "type": "stt_result",
                        "text": text
                    }
                    await websocket.send_json(stt_data)
            elif data.get("type") == "cancel_tts":
                global tts_process
                if tts_process and tts_process.poll() is None:
                    tts_process.terminate()
                    tts_process = None

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# HTTP API Endpoints
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """HTTP endpoint for chat (fallback for WebSocket)"""
    try:
        user_message = request.message.strip()
        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # Save user message
        save_chat_message("user", user_message)

        # Process through AI
        ai_response = await process_ai_query(user_message)

        # Save AI response
        save_chat_message("assistant", ai_response)

        return {
            "response": ai_response,
            "assistant": Assistantname
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tts")
async def text_to_speech_endpoint(request: TTSRequest):
    """Generate speech audio from text"""
    try:
        text = request.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        # Generate speech using existing TTS module
        global tts_process
        tts_process = await TTS(text)

        return {"status": "success", "message": "Audio generated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS Error: {str(e)}")

@app.get("/api/audio/speech.mp3")
async def get_speech_audio():
    """Serve the generated speech audio file"""
    audio_path = "Data/speech.mp3"
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(audio_path, media_type="audio/mpeg", filename="speech.mp3")

@app.get("/api/config")
async def get_config():
    """Get configuration including assistant name"""
    try:
        return {
            "assistant_name": Assistantname,
            "username": Username
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/history")
async def get_chat_history():
    """Get chat history"""
    try:
        chat_data = initialize_chat_log()
        return {"history": chat_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chat/history")
async def clear_chat_history():
    """Clear chat history"""
    try:
        with open(r'Data\ChatLog.json', 'w', encoding='utf-8') as file:
            json.dump([], file)
        return {"status": "success", "message": "Chat history cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint to serve the HTML GUI
@app.get("/")
async def root():
    return FileResponse("Frontend/GUI.html", media_type="text/html")

# Entry point
if __name__ == "__main__":
    print("Starting ULTRON AI Assistant Server...")
    print("Open your browser to http://localhost:8000")

    # Start the server
    uvicorn.run(
        "Main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
