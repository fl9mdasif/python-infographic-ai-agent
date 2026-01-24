"""
Scout Trends
Directive: directives/01_scout_trends.md
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

load_dotenv()

args_feeds = [
    "https://www.reddit.com/r/n8n/new/.rss?limit=100",
    "https://www.reddit.com/r/Automate/new/.rss?limit=100",
]
MAX_AGE_HOURS = 72

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
            if "429" in str(e) or "quota" in str(e).lower():
                time.sleep(base_delay * (2 ** attempt))
            else:
                raise e
    return None

def main():
    client = setup_client()
    print("Scouting trends...")
    
    all_posts = []
    seen = set()
    cutoff = datetime.datetime.now(tzutc()) - datetime.timedelta(hours=MAX_AGE_HOURS)

    for url in args_feeds:
        try:
            print(f"Fetching {url}...")
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if entry.link in seen: continue
                seen.add(entry.link)
                # Date parsing logic
                pub = entry.get('updated') or entry.get('published')
                if not pub: continue
                try:
                    dt = date_parser.parse(pub)
                    if dt.tzinfo is None: dt = dt.replace(tzinfo=tzutc())
                    if dt < cutoff: continue
                    text_content = entry.get('content', [{'value': entry.get('summary', '')}])[0]['value']
                    clean_text = re.sub('<[^<]+?>', '', text_content)[:500].replace('\n', ' ')
                    all_posts.append({"title": entry.title, "link": entry.link, "text": clean_text})
                except: continue
        except Exception as e:
             print(f"Feed error: {e}")

    print(f"Found {len(all_posts)} recent posts.")

    print(f"Found {len(all_posts)} recent posts.")

    # Select Top 5 "Most Important"
    # Strategy: Try lightweight AI selection (Titles only), Fallback to Keyword Scoring
    selected_posts = []
    
    # 1. AI Selection (Lightweight)
    if client and all_posts:
        try:
            print("  Ranking posts with AI...")
            # Create a minimized list for Token Efficiency
            titles_list = "\n".join([f"{i}: {p['title']}" for i, p in enumerate(all_posts[:50])]) # Limit to 50 to fit context
            prompt = f"""
            Select the 5 most important/high-signal titles for an AI Automation Daily Report from this list.
            Prioritize: New Tools, Major Releases, Tutorials, and High-Value Discussions.
            Return ONLY the ID numbers separated by commas. Example: 0, 4, 12, 15, 20
            
            List:
            {titles_list}
            """
            resp = retry_with_backoff(client.models.generate_content, model='models/gemini-2.0-flash', contents=prompt)
            if resp:
                ids = [int(x.strip()) for x in resp.text.split(',') if x.strip().isdigit()]
                for i in ids:
                    if 0 <= i < len(all_posts):
                        selected_posts.append(all_posts[i])
                print(f"  AI selected {len(selected_posts)} posts.")
        except Exception as e:
            print(f"  AI Ranking failed: {e}")

    # 2. Heuristic Fallback (if AI failed or returned nothing)
    if not selected_posts:
        print("  Using Heuristic Ranking (Fallback)...")
        scored = []
        keywords = ["agent", "n8n", "workflow", "tutorial", "guide", "release", "launch", "automate", "ai", "llm"]
        for p in all_posts:
            score = 0
            text = (p['title'] + " " + p['text']).lower()
            # Newness boost (linear decay)
            # Simple keyword matching
            for k in keywords:
                if k in text: score += 1
            if "guide" in text or "tutorial" in text: score += 1
            if "release" in text or "launch" in text: score += 2
            scored.append((score, p))
        
        # Sort by score desc
        scored.sort(key=lambda x: x[0], reverse=True)
        selected_posts = [x[1] for x in scored[:5]]

    # Generate Report for Selected Posts
    ts_str = datetime.datetime.now().strftime('%Y-%m-%d')
    report_text = f"REDDIT DIGEST - {ts_str}\n==========================\n\n## 🤖 Daily Trends (Top 5)\n\n"
    
    for p in selected_posts:
        title = p['title'].replace("[", "(").replace("]", ")")
        link = p.get('link', 'https://reddit.com')
        # Infer sub
        sub = "reddit"
        if "/r/" in link:
            try: sub = link.split("/r/")[1].split("/")[0]
            except: pass
            
        summary = p['text'][:300].replace("\n", " ") + "..."
        
        report_text += f"### [r/{sub}] {title}\n"
        report_text += f"🔗 {link}\n"
        report_text += f"    {summary}\n\n"

    ts = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    os.makedirs(".tmp", exist_ok=True)
    with open(f".tmp/trends_summary_{ts}.txt", "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"Saved: .tmp/trends_summary_{ts}.txt")

if __name__ == "__main__":
    main()
