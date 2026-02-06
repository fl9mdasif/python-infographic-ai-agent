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
    
    os.makedirs(".tmp/visuals", exist_ok=True)
    
    pollinations_key = os.getenv("POLLINATIONS_API_KEY")
    if not pollinations_key:
        print("Warning: POLLINATIONS_API_KEY not found in .env. Using free tier (rate limited).")

    for title, idea in topics:
        print(f"Generating visual for: {title}")
        prompt_text = (
            f"High-tech infographic for: {title}. "
            f"Theme: {idea}. "
            f"Style: Neon blue and purple, dark background, detailed tech nodes, clean vector aesthetic."
        )
        
        safe = "".join(c for c in title if c.isalnum()).rstrip()
        path = f".tmp/visuals/{safe}.png"
        
        # Pollinations AI Logic
        encoded_prompt = urllib.parse.quote(prompt_text)
        seed = random.randint(0, 100000)
        
        # Construct URL - using Flux model
        url = f"https://gen.pollinations.ai/image/{encoded_prompt}?width=1024&height=1024&seed={seed}&nologo=true&model=flux"
        
        pollinations_success = False
        for attempt in range(1, 4):
            try:
                print(f"  Requesting Pollinations (Attempt {attempt})...")
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'Mozilla/5.0')
                if pollinations_key:
                    req.add_header('Authorization', f'Bearer {pollinations_key}')
                    
                with urllib.request.urlopen(req, timeout=60) as response:
                    if response.getcode() == 200:
                        content = response.read()
                        with open(path, 'wb') as out_file:
                            out_file.write(content)
                        print(f"  ✅ Saved: {path}")
                        pollinations_success = True
                        break
                    else:
                        print(f"  Pollinations returned status: {response.getcode()}")
            except Exception as e:
                print(f"  Pollinations Error (Attempt {attempt}): {e}")
                # If 502 or network error, wait a bit
                time.sleep(2 * attempt)
        
        if not pollinations_success:
            print(f"  ❌ Pollinations failed after retries for: {title}")

if __name__ == "__main__":
    main()
