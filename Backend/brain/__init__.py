from . import memory
from . import context as ctx
from . import decision as dec
from . import personality

from .memory import ShortTermMemory

from Backend.Model import FirstLayerDMM
from Backend.Chatbot import ChatBot
from Backend.RealtimeSearchEngine import RealtimeSearchEngine


class Brain:
    def __init__(self, username: str = "User", assistant_name: str = "Jarvis"):
        self.username = username
        self.assistant_name = assistant_name
        self.short_term = ShortTermMemory()
        self.coding_agent = None

    def load_coding_agent(self, agent):
        self.coding_agent = agent

    def process(self, query: str) -> dict:
        self.short_term.add("user", query)

        cohere_decisions = FirstLayerDMM(query)
        intents = dec.map_cohere_to_intent(cohere_decisions)
        intents = dec.prioritize_intents(intents)

        result = {
            "query": query,
            "intents": [(t.value, q) for t, q in intents],
            "response": "",
            "action": "none",
            "coding": False,
        }

        if dec.has_exit_intent(intents):
            result["response"] = ChatBot("Okay, Bye!")
            result["action"] = "exit"
            self._save_both(query, result["response"])
            return result

        if dec.has_coding_intent(intents):
            result["coding"] = True
            result["action"] = "coding"
            result["response"] = "Entering coding mode."
            self._save_both(query, result["response"])
            return result

        primary_intent, primary_query = intents[0] if intents else (dec.IntentType.GENERAL, query)

        if primary_intent in {dec.IntentType.OPEN_APP, dec.IntentType.CLOSE_APP, dec.IntentType.PLAY_MEDIA, dec.IntentType.SYSTEM_CONTROL, dec.IntentType.SYSTEM_STATUS, dec.IntentType.TASK_MANAGE, dec.IntentType.PC_OPTIMIZE, dec.IntentType.FILE_OPERATION, dec.IntentType.AUTOMATION, dec.IntentType.SCHEDULE}:
            result["action"] = "automation"
            result["response"] = self._route_automation(primary_intent, primary_query)
            self._save_both(query, result["response"])
            return result

        if primary_intent == dec.IntentType.GENERATE_IMAGE:
            result["action"] = "image_generation"
            result["response"] = self._handle_image_generation(primary_query)
            self._save_both(query, result["response"])
            return result

        if primary_intent == dec.IntentType.REALTIME:
            result["action"] = "realtime_search"
            chat_history = memory.get_recent_chat(20)
            response = RealtimeSearchEngine(primary_query or query, chat_history)
            result["response"] = response
            self._save_both(query, result["response"])
            return result

        if primary_intent == dec.IntentType.GENERAL:
            result["action"] = "general_chat"
            response = ChatBot(primary_query or query)
            result["response"] = response
            self._save_both(query, result["response"])
            return result

        result["response"] = ChatBot(query)
        result["action"] = "general_chat"
        self._save_both(query, result["response"])
        return result

    def _save_both(self, user_query: str, response: str):
        memory.store_chat_message("user", user_query)
        self.short_term.add("assistant", response)
        memory.store_chat_message("assistant", response)

    def _route_automation(self, intent: dec.IntentType, query: str) -> str:
        try:
            if intent == dec.IntentType.OPEN_APP:
                from Backend.Automation.simple_automation import open_application
                return open_application(query)
            elif intent == dec.IntentType.CLOSE_APP:
                from Backend.Automation.simple_automation import close_application
                return close_application(query)
            elif intent == dec.IntentType.PLAY_MEDIA:
                from Backend.Automation.simple_automation import play_media
                return play_media(query)
            elif intent == dec.IntentType.SYSTEM_CONTROL:
                from Backend.Automation.simple_automation import system_control
                return system_control(query)
            elif intent == dec.IntentType.SYSTEM_STATUS:
                from Backend.Automation.System_understanding import get_system_status
                return get_system_status()
            elif intent == dec.IntentType.TASK_MANAGE:
                from Backend.Automation.task_manager import manage_tasks
                return manage_tasks(query)
            elif intent == dec.IntentType.PC_OPTIMIZE:
                from Backend.Automation.pc_optimation import optimize_pc
                return optimize_pc()
            elif intent == dec.IntentType.FILE_OPERATION:
                from Backend.Automation.advanced_automation import file_operation
                return file_operation(query)
            elif intent == dec.IntentType.AUTOMATION:
                from Backend.Automation.advanced_automation import advanced_automation
                return advanced_automation(query)
            elif intent == dec.IntentType.SCHEDULE:
                from Backend.Automation.task_manager import schedule_task
                return schedule_task(query)
            return f"Automation module for {intent.value} is not yet implemented."
        except ImportError as e:
            return f"The automation module for {intent.value} is not ready yet: {e}"
        except Exception as e:
            return f"Error executing {intent.value}: {e}"

    def _handle_image_generation(self, query: str) -> str:
        try:
            import os
            os.makedirs("Frontend/Files", exist_ok=True)
            with open(r'Frontend\Files\ImageGeneration.data', "w") as f:
                f.write(f"{query},True")

            import subprocess
            subprocess.Popen(
                ['python', r"Backend\ImageGeneration.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                shell=False,
            )
            return f"Generating images of {query}. Please wait."
        except Exception as e:
            return f"Error starting image generation: {e}"

    def get_greeting(self) -> str:
        return personality.get_greeting()

    def get_proactive_prompt(self) -> str:
        return personality.get_proactive_prompt()

    def format_for_speech(self, text: str) -> str:
        return personality.format_response(text)
