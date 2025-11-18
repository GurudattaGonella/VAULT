import os
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Load your API key
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '..', '.env')
load_dotenv(env_path)
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ API Key not found!")
else:
    genai.configure(api_key=api_key)
    print("✅ Connected. Listing available models...\n")

    try:
        # 2. Ask Google for the list
        for m in genai.list_models():
            # We only care about models that can generate content (text/chat)
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
                
    except Exception as e:
        print(f"Error listing models: {e}")