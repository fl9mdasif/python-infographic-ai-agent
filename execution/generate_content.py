"""
Generate Content
Directive: directives/02_generate_content.md
"""
import os
import sys
import glob
import re
import json
import time
from google import genai
from dotenv import load_dotenv

load_dotenv()

def setup_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: return None
    return genai.Client(api_key=api_key)

def retry_with_backoff(func, *args, **kwargs):
    max_retries = 3
    base_delay = 5
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "429" in str(e):
                time.sleep(base_delay * (2 ** attempt))
            else:
                return None
    return None

def main():
    client = setup_client()
    files = glob.glob(".tmp/trends_summary_*.txt")
    if not files: return
    
    with open(max(files, key=os.path.getctime), "r", encoding="utf-8") as f: content = f.read()
    
    # Regex for new Digest format: ### [newest submissions : sub] Title
    topics = re.findall(r'### \[.*?\] (.*)', content)[:5]
    if not topics: topics = ["AI Automation Trends"]

    os.makedirs(".tmp/articles", exist_ok=True)

    for topic in topics:
        print(f"Generating content for: {topic}")
        data = None
        
        if client:
            prompt = f"Create JSON article for {topic}. Keys: title, summary, key_points."
            try:
                resp = retry_with_backoff(client.models.generate_content, model='models/gemini-2.0-flash', contents=prompt)
                if resp:
                    text = resp.text.replace("```json", "").replace("```", "").strip()
                    data = json.loads(text)
            except Exception as e:
                print(f"API/JSON Error for {topic}: {e}")

        if not data:
            print("Using Fallback Article.")
            data = {
                "title": topic,
                "summary": "Fallback summary due to API limits.",
                "key_points": [{"headline": "System Limit", "description": "Offline mode active."}]
            }
            
        safe = "".join(c for c in topic if c.isalnum()).rstrip()
        with open(f".tmp/articles/article_{safe}.json", "w") as f:
            json.dump(data, f, indent=4)

if __name__ == "__main__":
    main()
