# Directive: Scout Reddit Trends

## Goal
Identify high-signal opportunities from Reddit RSS feeds.

## Inputs
- Default Feeds: `r/n8n`, `r/Automate`
- Time Window: Last 72 hours

## Tooling
- Script: `execution/scout_trends.py`
- Model: `models/gemini-2.0-flash` (Text)

## Output
- File: `.tmp/trends_summary_[TIMESTAMP].txt`
- Format: Markdown list of opportunities.

## Error Handling (Self-Annealing)
- **Rate Limit (429)**: The script MUST retry with exponential backoff.
- **Total Failure**: If API fails completely, write a **FALLBACK REPORT** to `.tmp/` so downstream steps (Images/Dashboard) do not fail.
