# Directive: Generate Content

## Goal
Create structured JSON articles based on identified trends.

## Inputs
- Source: One or more `trends_summary_*.txt` files in `.tmp/`.

## Tooling
- Script: `execution/generate_content.py`
- Model: `models/gemini-2.0-flash`

## Output
- File: `.tmp/articles/article_[TOPIC].json`
- Format: JSON with `title`, `summary`, `key_points`.

## Error Handling
- **Rate Limit**: Retry backoff.
- **Failover**: If text generation fails, create a "Fallback Article" JSON with placeholder text so the Dashboard doesn't look empty.
