"""
Build Dashboard
Directive: directives/04_build_dashboard.md
"""
import os
import glob
import json

def main():
    print("Building Dashboard...")
    
    # Trends
    trend_report = ""
    t_files = glob.glob(".tmp/trends_summary_*.txt")
    if t_files:
        with open(max(t_files, key=os.path.getctime), "r", encoding="utf-8") as f: 
            trend_report = f.read()
            # Wrap links in anchor tags if not already (simple heuristic)
            # The report has 🔗 https://...
            # We can run a simple replace to make them clickable in HTML
            trend_report = re.sub(r'(https?://[^\s]+)', r'<a href="\1">\1</a>', trend_report)

    # Articles
    articles_html = ""
    for af in glob.glob(".tmp/articles/*.json"):
        with open(af, "r") as f:
            d = json.load(f)
            articles_html += f"<div class='card'><h3>{d.get('title', 'Untitled')}</h3><p>{d.get('summary', '')}</p></div>"

    # Visuals
    visuals_html = ""
    for vf in glob.glob(".tmp/visuals/*.png"):
        fn = os.path.basename(vf)
        visuals_html += f"<img src='visuals/{fn}' class='viz'>"

    html = f"""<html><head><style>
    body{{font-family:sans-serif;background:#f4f4f4;padding:20px}} 
    .card{{background:white;padding:20px;margin:10px;border-radius:8px}}
    .viz{{width:100%;height:300px;object-fit:contain;background:#222;border:none;margin:10px}}
    </style></head><body>
    <h1>Daily Report</h1>
    <div class='card'><h2>Trends</h2><pre>{trend_report}</pre></div>
    <div class='card'><h2>Visuals</h2>{visuals_html}</div>
    <div class='card'><h2>Articles</h2>{articles_html}</div>
    </body></html>"""
    
    with open(".tmp/index.html", "w") as f:
        f.write(html)
    print("Dashboard saved: .tmp/index.html")

if __name__ == "__main__":
    main()
