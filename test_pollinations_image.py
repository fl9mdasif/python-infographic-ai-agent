import os
import urllib.request
import urllib.parse
import time
import random
from dotenv import load_dotenv

load_dotenv()

def try_request(url, api_key=None, description=""):
    print(f"\n--- Testing: {description} ---")
    print(f"URL: {url}")
    
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    if api_key:
        print("Using API Key: Yes")
        req.add_header('Authorization', f'Bearer {api_key}')
    else:
        print("Using API Key: No")

    try:
        start_time = time.time()
        with urllib.request.urlopen(req, timeout=30) as response:
            print(f"Response Code: {response.getcode()}")
            content = response.read()
            if len(content) > 0:
                filename = f"test_pollinations_{int(start_time)}.jpg"
                with open(filename, "wb") as f:
                    f.write(content)
                print(f"SUCCESS: Image saved to {filename}")
                return True
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        try:
            print(f"Error Body: {e.read().decode()}")
        except:
            pass
    except Exception as e:
        print(f"General Error: {e}")
    
    return False

def generate_image():
    api_key = os.getenv("POLLINATIONS_API_KEY")
    prompt = "A futuristic city with flying cars neon lights"
    encoded_prompt = urllib.parse.quote(prompt)
    seed = random.randint(0, 10000)

    # Strategy 1: Simple, No Key, Default Model
    url1 = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=512&height=512&nologo=true"
    if try_request(url1, None, "Strategy 1 (No Key, Default Model, 512x512)"): return

    # Strategy 2: Simple, With Key, Default Model
    url2 = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=512&height=512&nologo=true"
    if try_request(url2, api_key, "Strategy 2 (With Key, Default Model, 512x512)"): return

    # Strategy 3: Flux Model, No Key
    url3 = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=512&height=512&nologo=true&model=flux"
    if try_request(url3, None, "Strategy 3 (No Key, Flux Model)"): return

    # Strategy 4: Flux Model, With Key
    url4 = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=512&height=512&nologo=true&model=flux"
    if try_request(url4, api_key, "Strategy 4 (With Key, Flux Model)"): return

    print("\nAll strategies failed.")

if __name__ == "__main__":
    generate_image()
