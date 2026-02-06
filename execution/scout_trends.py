"""
Scout Trends
Directive: directives/01_scout_trends.md
Structure matches user-provided reference.
"""
import os
import sys
import datetime
import re
import feedparser
from dateutil import parser as date_parser
from dateutil.tz import tzutc
from google import genai
from dotenv import load_dotenv
import time
import json

# Load environment variables
load_dotenv()

# Configuration
RSS_FEEDS = [
    "https://www.reddit.com/r/n8n/new/.rss?limit=100",
    "https://www.reddit.com/r/Automate/new/.rss?limit=100",
    "https://www.reddit.com/r/openai/new/.rss?limit=100",
    "https://www.reddit.com/r/LocalLLaMA/new/.rss?limit=100",
]
TIME_WINDOW_HOURS = 72
OUTPUT_DIR = ".tmp"

# Setup Gemini
def setup_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env")
        return None
    return genai.Client(api_key=api_key)

def retry_with_backoff(func, *args, **kwargs):
    max_retries = 3
    base_delay = 5
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                time.sleep(base_delay * (2 ** attempt))
            else:
                raise e
    return None

def fetch_posts():
    all_posts = []
    seen_links = set() # Use a set to track seen links for deduplication
    cutoff = datetime.datetime.now(tzutc()) - datetime.timedelta(hours=TIME_WINDOW_HOURS)
    
    for url in RSS_FEEDS:
        try:
            print(f"Fetching {url}...")
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if entry.link in seen_links:
                    continue
                seen_links.add(entry.link)

                # Date parsing
                pub = entry.get('updated') or entry.get('published')
                if not pub: continue
                try:
                    dt = date_parser.parse(pub)
                    if dt.tzinfo is None: dt = dt.replace(tzinfo=tzutc())
                    if dt < cutoff: continue
                    
                    # Content cleaning (Regex from screenshot)
                    content_raw = entry.get('content', [{'value': entry.get('summary', '')}])[0]['value']
                    text_content = re.sub('<[^<]+?>', '', content_raw)[:1500] # Truncate for token limits
                    
                    post = {
                        "title": entry.title,
                        "link": entry.link,
                        "date": dt.isoformat(),
                        "text": text_content.replace('\n', ' '),
                        "sub": feed.feed.get('title', 'Unknown') # This is the feed title, not the subreddit name
                    }
                    all_posts.append(post)
                except Exception as e:
                    # print(f"Error parsing entry: {e}")
                    continue
        except Exception as e:
             print(f"Failed to fetch {url}: {e}")
             
    # Deduplicate by link (from screenshot structure) - already done with seen_links set
    # unique_posts = {p['link']: p for p in all_posts}.values() # This line is redundant if seen_links is used
    print(f"Total relevant posts (last {TIME_WINDOW_HOURS}h, unique): {len(all_posts)}")
    return all_posts

def evaluate_posts(client, posts):
    print("Evaluating posts for signal...")
    selected_posts = []
    
    # 1. AI Selection
    if client and posts:
        try:
            print("  Ranking posts with AI...")
            # Limit to 50 posts for token efficiency, as per original logic
            titles_list = "\n".join([f"{i}: {p['title']}" for i, p in enumerate(posts[:50])])
            prompt = f"""
            Select the 5 most important/high-signal titles for an AI Automation Daily Report.
            Prioritize: New Tools, Major Releases, Tutorials.
            Return ONLY ID numbers separated by commas (e.g., 0, 4, 12).
            List:
            {titles_list}
            """
            resp = retry_with_backoff(client.models.generate_content, model='gemini-1.5-flash', contents=prompt)
            if resp and resp.text:
                ids = [int(x.strip()) for x in resp.text.split(',') if x.strip().isdigit()]
                for i in ids:
                    if 0 <= i < len(posts): # Ensure index is within bounds of the *original* posts list
                        selected_posts.append(posts[i])
                print(f"  AI selected {len(selected_posts)} posts.")
        except Exception as e:
            print(f"  AI Ranking failed: {e}")

    # 2. Heuristic Fallback
    if not selected_posts:
        print("  Using Keyword Heuristics...")
        scored = []
        keywords = ["agent", "n8n", "workflow", "tutorial", "guide", "release", "launch", "automate", "ai", "llm"]
        for p in posts:
            score = 0
            text = (p['title'] + " " + p['text']).lower()
            for k in keywords:
                if k in text: score += 1
            if "guide" in text or "tutorial" in text: score += 1
            if "release" in text or "launch" in text: score += 2
            scored.append((score, p))
        scored.sort(key=lambda x: x[0], reverse=True)
        selected_posts = [x[1] for x in scored[:5]]
    
    return selected_posts

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    client = setup_gemini()
    posts = fetch_posts()
    
    if not posts:
        print("No posts found.")
        return

    signal_posts = evaluate_posts(client, posts)
    
    # Generate Output
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    output_path = f"{OUTPUT_DIR}/trends_summary_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"REDDIT DAILY DIGEST - {date_str}\n")
        f.write("==================\n\n")
        f.write("## 🤖 Daily Trends (Top 5)\n\n") # Added this line to match original output format
        
        # Format: Insight/Source/Score (Preserved for compatibility)
        for p in signal_posts:
            title = p['title'].replace("[", "(").replace("]", ")")
            link = p.get('link', 'https://reddit.com')
            text_preview = p['text'][:300].strip()
            
            # Subreddit extraction (reverted to original logic from link)
            sub = "reddit"
            if "/r/" in link:
                try: sub = link.split("/r/")[1].split("/")[0]
                except: pass
                
            # Score calc (reverted to original logic)
            display_score = 7
            combined = (title + text_preview).lower()
            if "launch" in combined or "release" in combined: display_score += 2
            if "agent" in combined: display_score += 1
            if display_score > 10: display_score = 10
            
            f.write(f"**Insight**: {title} - {text_preview}...\n\n")
            f.write(f"**Source**: [top scoring links : {sub}]({link})\n") # Reverted to original source format
            f.write(f"**Score**: {display_score}/10\n\n")

    print(f"Success! Report saved to {output_path}")

if __name__ == "__main__":
    main()
