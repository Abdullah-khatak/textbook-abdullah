import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")  # Using same variable name
        if not api_key:
            raise ValueError("⚠️ GEMINI_API_KEY not set in .env file")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        
    def generate_response(self, prompt: str, context: str = ""):
        """Generate response using OpenRouter"""
        full_prompt = f"""You are a helpful assistant for a Physical AI & Humanoid Robotics textbook.

Context: {context}

User Question: {prompt}

Provide a clear, accurate answer based on the context."""

        response = self.client.chat.completions.create(
            model="meta-llama/llama-3.2-3b-instruct:free",  # Free model!
            messages=[
                {"role": "system", "content": "You are a helpful robotics and AI assistant."},
                {"role": "user", "content": full_prompt}
            ]
        )
        
        return response.choices[0].message.content