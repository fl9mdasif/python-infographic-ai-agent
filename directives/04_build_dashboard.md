# Directive: Build Dashboard

## Goal
Aggregate all artifacts into a daily HTML report.

## Inputs
- `.tmp/trends_summary_*.txt`
- `.tmp/articles/*.json`
- `.tmp/visuals/*.png`

## Tooling
- Script: `execution/build_dashboard.py`

## Output
- File: `.tmp/index.html` (The Deliverable).
