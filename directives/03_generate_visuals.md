# Directive: Generate Visuals

## Goal
Create compelling visual infographics using Google Gemini.

## Inputs
- Source: Trends report (`.tmp/trends_summary_*.txt`)

## Tooling
- Script: `execution/generate_visuals.py`
- Service: **Google Gemini / Imagen** (via API Key).

## Style Requirements
- **Background**: Dark / Black (#0f0f0f).
- **Colors**: Neon Purple, Neon Blue.
- **Layout**: Central Network/Graph Diagram.
- **Details**: Tech icons, connection lines, data points.

## Process
1.  Parse `Title` and `Core Idea`.
2.  Call Gemini API (`models/imagen-3.0-generate-001` or compatible).
3.  Save image to `.tmp/visuals/`.
