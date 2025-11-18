import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

# --- 1. Smartly Load the .env file ---
# Get the folder where THIS script (genai_engine.py) is located
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to the 'backend' folder where .env should be
env_path = os.path.join(current_dir, '..', '.env')

# Load the file specifically from that path
load_dotenv(env_path)

# Get the key
api_key = os.getenv("GEMINI_API_KEY")

# --- 2. Configure the AI ---
if not api_key:
    print("❌ ERROR: API Key not found.")
    print(f"   I looked for the file here: {os.path.abspath(env_path)}")
    print("   Make sure the file is named exactly '.env' and not '.env.txt'")
else:
    try:
        genai.configure(api_key=api_key)
        print("✅ GenAI Engine Connected.")
    except Exception as e:
        print(f"❌ Error configuring GenAI: {e}")

class GenAIEngine:
    def __init__(self):
        # We use the 'flash' model because it's fast, smart, and free
        try:
            self.model = genai.GenerativeModel('models/gemini-2.5-flash')
        except Exception as e:
            print(f"Error initializing model: {e}")
            self.model = None

    def generate_summary(self, text):
        """
        Generates a concise summary of the provided text.
        """
        if not self.model: return "Error: AI model not loaded."

        prompt = f"""
        You are an expert tutor. Summarize the following educational content for a student.
        Make it concise (under 150 words), clear, and bulleted if necessary.
        
        Content:
        {text}
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating summary: {e}"

    def generate_quiz(self, text, difficulty="Medium"):
        """
        Generates a JSON-formatted quiz based on the text.
        """
        if not self.model: return []

        prompt = f"""
        Create a {difficulty} level quiz based on this text.
        Generate 5 multiple-choice questions.
        
        CRITICAL: Return ONLY a raw JSON list. Do not use markdown blocks (```json).
        Format:
        [
            {{
                "question": "Question text here?",
                "options": ["A", "B", "C", "D"],
                "answer": "The correct option text",
                "explanation": "Short explanation"
            }}
        ]
        
        Text:
        {text}
        """
        try:
            response = self.model.generate_content(prompt)
            
            clean_json = response.text.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
            
            return json.loads(clean_json)
        except Exception as e:
            print(f"Quiz Error: {e}")
            return []

# --- Test Block ---
if __name__ == "__main__":
    print("--- Testing GenAI Engine ---")
    bot = GenAIEngine()
    
    test_text = """
    Artificial Intelligence (AI) is the simulation of human intelligence processes 
    by machines, especially computer systems. These processes include learning, 
    reasoning, and self-correction. Particular applications of AI include expert 
    systems, speech recognition, and machine vision.
    """
    
    print("\n--- 📝 Summary ---")
    print(bot.generate_summary(test_text))
    
    print("\n--- 🧠 Quiz ---")
    quiz = bot.generate_quiz(test_text)
    print(json.dumps(quiz, indent=2))