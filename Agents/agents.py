import google.generativeai as genai
import os

os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

class Agent:
    def __init__(self,name,model_name = "gemini-1.5-flash",instruction=""):
        self.name = name
        self.model = genai.GenerativeModel(
            model_name,
            system_instruction=instruction
        )
        self.chat = self.model.start_chat(history=[])
    def send_message(self,message):
        """send message to agent and get response"""
        try:
            response = self.chat.send_message(message)
            return response.text
        except Exception as e:
            return f"Error in {self.name}: {e}"