import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from googleapiclient.discovery import build
import random # Used to pick a random prompt if one fails

# --- Configuration & Setup (Same as before) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '..', '.env')
load_dotenv(env_path)
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ ERROR: API Key not found.")
else:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"❌ GenAI Config Error: {e}")

class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        model = "models/text-embedding-004"
        return genai.embed_content(model=model, content=input, task_type="retrieval_document", title="Custom query")["embedding"]

class GenAIEngine:
    def __init__(self):
        try:
            self.model = genai.GenerativeModel('models/gemini-2.5-flash')
        except: self.model = None
        
        try:
            self.chroma_client = chromadb.Client()
            self.collection = self.chroma_client.get_or_create_collection(name="study_materials", embedding_function=GeminiEmbeddingFunction())
        except: pass
        
        self.chat_history = []
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.youtube = build('youtube', 'v3', developerKey=api_key)
        except: 
            self.nlp = None
            self.youtube = None

    def build_memory_index(self, text):
        # ... (RAG Indexing logic is the same) ...
        try:
            self.chroma_client.delete_collection("study_materials")
            self.collection = self.chroma_client.get_or_create_collection(name="study_materials", embedding_function=GeminiEmbeddingFunction())
        except: pass

        # Using 500-char chunks for better large document indexing
        chunks = [text[i:i + 500].strip() for i in range(0, len(text), 500) if len(text[i:i + 500].strip()) > 100]
        
        if not chunks: return "Error: Text too short."
        
        ids = [f"id_{i}" for i in range(len(chunks))]
        self.collection.add(documents=chunks, ids=ids)
        self.chat_history = []
        return f"✅ Indexed {len(chunks)} chunks. Ready to generate content."

    def generate_summary(self, text):
        """
        UPGRADE 1: Comprehensive Summary (No length limit, structured)
        Relies on Gemini's huge context window to handle large inputs and structured output.
        """
        # Truncate to a still-large but safe amount for the API
        safe_text = text[:80000] 
        
        prompt = f"""
        You are an expert Professor. Create a DETAILED, COMPREHENSIVE Study Guide for this document.
        
        It must be understandable to anyone, regardless of prior knowledge.
        
        Structure your entire response using the following headings and rich Markdown:
        1. 🎯 **Executive Summary** (A high-level overview in 3-4 sentences)
        2. 🔑 **Key Concepts** (A bulleted list of the most important terms and their definitions)
        3. 📖 **Comprehensive Breakdown** (A detailed, section-by-section summary of the content)
        4. 🧠 **Real-World Application** (How is this used in real life?)

        Text:
        {safe_text}
        """
        try:
            return self.model.generate_content(prompt).text
        except Exception as e:
            return f"Summary Error: {e}"

    def generate_quiz(self, text, difficulty="Medium", count=10):
        """
        UPGRADE 2: Flexible MCQ Count (Maximum of 50 total questions enforced by the frontend)
        """
        difficulty_prompts = {
            "Easy": "Focus on basic definitions, terminology, and simple facts. Use simple language.",
            "Medium": "Focus on understanding concepts, comparisons, and standard applications.",
            "Hard": "Focus on complex scenarios, cause-and-effect, and deep reasoning questions. Requires synthesis of knowledge."
        }
        
        style_instruction = difficulty_prompts.get(difficulty, difficulty_prompts["Medium"])
        
        prompt = f"""
        Create a {difficulty} level JSON quiz. Generate exactly {count} multiple-choice questions.
        
        Instructions: {style_instruction}
        
        Format: [{{ "question": "...", "options": ["A", "B", "C", "D"], "answer": "The correct option text", "explanation": "Why?" }}]
        Return ONLY raw JSON.
        
        Text:
        {text[:15000]} 
        """
        try:
            response = self.model.generate_content(prompt)
            clean = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(clean)
        except: return []

    def get_youtube_recommendations(self, text):
        """
        UPGRADE 3: Granular YouTube (7 total videos covering 4 sub-topics)
        """
        if not self.nlp or not self.youtube: return []
        
        # 1. Ask AI to identify 4 distinct sub-topics (Better than simple NLP keywords)
        prompt = f"""
        Identify the 4 most critical and distinct sub-topics in this text for educational video searches.
        Return ONLY the 4 topics separated by commas.
        Text: {text[:5000]}
        """
        try:
            response = self.model.generate_content(prompt)
            topics = [t.strip() for t in response.text.split(',')]
        except:
            topics = ["Educational Study Guide"] # Fallback

        videos = []
        
        # 2. Search for 4 topics, getting 2 videos per topic until 7 videos are collected
        for topic in topics[:4]:
            try:
                if len(videos) >= 7:
                    break
                    
                request = self.youtube.search().list(
                    part="snippet", maxResults=2, q=f"{topic} tutorial educational", type="video", safeSearch="moderate"
                )
                response = request.execute()
                
                for item in response['items']:
                    if len(videos) >= 7: # Check again after fetching
                        break
                    
                    videos.append({
                        "title": item['snippet']['title'],
                        "thumbnail": item['snippet']['thumbnails']['high']['url'],
                        "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                        "topic": topic
                    })
            except: continue
            
        return videos

    def chat_with_memory(self, user_query):
        # ... (Existing Logic - No change) ...
        results = self.collection.query(query_texts=[user_query], n_results=3)
        context = "\n\n".join(results['documents'][0])
        
        history = ""
        for turn in self.chat_history[-5:]:
            history += f"User: {turn['user']}\nBot: {turn['bot']}\n"
            
        prompt = f"""
        You are VAULT. Answer using the Context.
        Context: {context}
        History: {history}
        Question: {user_query}
        """
        try:
            res = self.model.generate_content(prompt)
            self.chat_history.append({"user": user_query, "bot": res.text})
            return res.text
        except: return "Error."