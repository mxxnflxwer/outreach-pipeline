# Outreach Pipeline

A simple Python CLI pipeline that automates cold outreach preparation.

## What it does

1. Finds lookalike companies for a seed domain using Ocean.io
2. Finds decision makers with LinkedIn URLs using Prospeo
3. Resolves LinkedIn URLs to verified work emails using Eazyreach
4. Reviews the final enriched list and optionally sends emails through Brevo

## Project structure

- `.env` - local API keys (not committed)
- `requirements.txt` - required Python packages
- `main.py` - pipeline entry point
- `stages/` - one file per pipeline stage
- `utils/helpers.py` - caching, retry logic, and helpers
- `data/` - intermediate JSON output files
- `cache/` - shared response cache for lookalikes, prospects, and emails
- `templates/` - email template file

## Setup

1. Create a Python environment:

```bash
python -m venv .venv
.venv/bin/activate   # macOS / Linux
.venv\\Scripts\\activate  # Windows PowerShell
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and add your API keys:

```bash
copy .env.example .env
```

## Environment variables

Set these values in `.env`:

- `OCEAN_API_KEY`
- `PROSPEO_API_KEY`
- `EAZYREACH_API_KEY`
- `BREVO_API_KEY`

## Usage

Run the pipeline for a seed domain:

```bash
python main.py stripe.com
```

Run in dry-run mode to execute all stages without sending emails:

```bash
python main.py stripe.com --dry-run
```

## Output files

- `data/domains.json` - Stage 1 lookalikes
- `data/prospects.json` - Stage 2 prospects
- `data/emails.json` - Stage 3 enriched email records

## Notes

- Caching is shared across runs in the `cache/` directory
- API calls retry up to 3 times with exponential backoff
- The pipeline skips individual failures without crashing the entire process
