"""
Generate Visuals
Directive: directives/03_generate_visuals.md
"""
import os
import glob
import re
import urllib.parse
import urllib.request
import time
import random
from dotenv import load_dotenv

load_dotenv()

def main():
    files = glob.glob(".tmp/trends_summary_*.txt")
    topics = []
    if files:
        with open(max(files, key=os.path.getctime), "r", encoding="utf-8") as f: content = f.read()
        
    if files:
        with open(max(files, key=os.path.getctime), "r", encoding="utf-8") as f: content = f.read()
        
        # Format:
        # **Insight**: Title - Summary...
        # **Source**: ...
        matches = re.findall(r'\*\*Insight\*\*: (.*)', content)
        
        topics = []
        if matches:
            for m in matches:
                # Split title and idea
                if " - " in m:
                    parts = m.split(" - ", 1)
                    title = parts[0]
                    idea = parts[1]
                else:
                    title = m[:40]
                    idea = m
                topics.append((title, idea))
        else:
            # Fallback
            topics = [("AI Automation", "Future of work")]

    if not topics: topics = [("AI Automation", "Future of work and agents"), ("Future Tech", "New developments in robotics")]
    
    # Cleaning is less relevant now as we captured group 1 inside the []
    
    os.makedirs(".tmp/visuals", exist_ok=True)
    
    # Gemini Setup
    api_key = os.getenv("GEMINI_API_KEY")
    client = None
    if api_key:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
        except ImportError:
            print("Warning: google-genai library not found. Gemini generation will be skipped.")
    
    def generate_with_retry(client, model_id, prompt_text, path):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"  Requesting Gemini ({model_id}) [IMAGE Mode] - Attempt {attempt+1}...")
                response = client.models.generate_content(
                    model=model_id,
                    contents=prompt_text,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(
                            aspect_ratio="16:9"
                        )
                    )
                )
                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data:
                            with open(path, "wb") as f:
                                f.write(part.inline_data.data)
                            return True
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    print(f"    Quota hit. Waiting {35 * (attempt + 1)}s...")
                    time.sleep(35 * (attempt + 1))
                else:
                    print(f"    Error: {e}")
                    break
        return False

    for title, idea in topics:
        print(f"Generating visual for: {title}")
        prompt_text = (
            f"High-tech infographic for: {title}. "
            f"Theme: {idea}. "
            f"Style: Neon blue and purple, dark background, detailed tech nodes, clean vector aesthetic."
        )
        
        safe = "".join(c for c in title if c.isalnum()).rstrip()
        path = f".tmp/visuals/{safe}.png"
        
        # Strictly use Gemini 2.5 Flash Image per documentation
        model_id = "models/gemini-2.5-flash"
        success = False
        if client: # Only attempt Gemini if client is initialized
            success = generate_with_retry(client, model_id, prompt_text, path)
        
        if success:
            print(f"  ✅ Saved: {path}")
        else:
            print(f"  ❌ Gemini failed (or skipped). Falling back to Pollinations for: {title}")
            
            pollinations_key = os.getenv("POLLINATIONS_API_KEY")
            # Encode the prompt
            encoded_prompt = urllib.parse.quote(prompt_text)
            # Use random seed to vary results
            seed = random.randint(0, 100000)
            
            # Construct URL - trying Flux model as it is often higher quality/stable
            url = f"https://gen.pollinations.ai/image/{encoded_prompt}?width=1024&height=1024&seed={seed}&nologo=true&model=flux"
            
            # Retry logic for Pollinations
            pollinations_success = False
            for attempt in range(1, 4):
                try:
                    print(f"    Requesting Pollinations (Attempt {attempt})...")
                    req = urllib.request.Request(url)
                    req.add_header('User-Agent', 'Mozilla/5.0')
                    if pollinations_key:
                        req.add_header('Authorization', f'Bearer {pollinations_key}')
                        
                    with urllib.request.urlopen(req, timeout=60) as response:
                        if response.getcode() == 200:
                            content = response.read()
                            with open(path, 'wb') as out_file:
                                out_file.write(content)
                            print(f"  ✅ Saved (Pollinations): {path}")
                            pollinations_success = True
                            success = True
                            break
                        else:
                            print(f"    Pollinations returned status: {response.getcode()}")
                except Exception as e:
                    print(f"    Pollinations Error (Attempt {attempt}): {e}")
                    # If 502 or network error, wait a bit
                    time.sleep(2 * attempt)
            
            if not pollinations_success:
                print(f"  ❌ Pollinations failed after retries for: {title}")

if __name__ == "__main__":
    main()
