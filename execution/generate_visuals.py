"""
Generate Visuals
Directive: directives/03_generate_visuals.md
"""
import os
import glob
import re
import urllib.parse
import urllib.request
from dotenv import load_dotenv

load_dotenv()

def main():
    files = glob.glob(".tmp/trends_summary_*.txt")
    topics = []
    if files:
        with open(max(files, key=os.path.getctime), "r", encoding="utf-8") as f: content = f.read()
        
        # New Digest Regex:
        # ### [newest submissions : sub] Title
        # 🔗 Link
        #     Summary
        matches = re.findall(r'### \[.*?\] (.*?)\n🔗 .*?\n\s+(.*)', content)
        
        if matches:
            topics = matches # List of (Title, Summary) tuples
        else:
            # Fallback
            titles = re.findall(r'### \[.*?\] (.*)', content)[:3]
            topics = [(t, "Innovative AI automation trend") for t in titles]

    if not topics: topics = [("AI Automation", "Future of work and agents"), ("Future Tech", "New developments in robotics")]
    
    # Cleaning is less relevant now as we captured group 1 inside the []
    
    os.makedirs(".tmp/visuals", exist_ok=True)
    
    # Gemini Setup
    api_key = os.getenv("GEMINI_API_KEY")
    client = None
    if api_key:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
    
    for title, idea in topics:
        print(f"Generating visual for: {title}")
        print(f"  Context: {idea[:50]}...")
        
        # Enhanced Prompt (Neon/Tech)
        prompt = (
            f"Professional tech infographic about '{title}'. "
            f"Central theme: {idea}. "
            f"Style: Dark Mode background (Hex #0f0f0f), glowing neon purple and blue data visualization. "
            f"Layout: Central complex network diagram connecting nodes. "
            f"Bottom section: Key takeaways with tech icons. "
            f"Aesthetic: Cyberpunk, Futuristic, High-Tech, 8k resolution, highly detailed vector art."
        )
        
        safe = "".join(c for c in title if c.isalnum()).rstrip()
        path = f".tmp/visuals/{safe}.png"
        
        success = False
        
        # 1. Try Gemini (Imagen)
        if client:
            try:
                print("  Requesting Gemini (Imagen)...")
                # Using standard Imagen mode if available, or the one user had.
                # 'models/imagen-3.0-generate-001' is common for v2
                response = client.models.generate_images(
                    model='models/imagen-3.0-generate-001',
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                    )
                )
                if response.generated_images:
                    image_bytes = response.generated_images[0].image.image_bytes
                    with open(path, "wb") as f:
                        f.write(image_bytes)
                    print(f"  ✅ Saved (Gemini): {path}")
                    success = True
            except Exception as e:
                print(f"  ❌ Gemini Image Gen failed: {e}")
        
        # 2. Fallback to Pollinations (if Gemini fails or no key)
        if not success:
            print("  ⚠️ Fallback to Pollinations.ai...")
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true"
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response, open(path, 'wb') as out_file:
                    out_file.write(response.read())
                print(f"  ✅ Saved (Pollinations): {path}")
            except Exception as e:
                print(f"  ❌ Fallback failed: {e}")

if __name__ == "__main__":
    main()
