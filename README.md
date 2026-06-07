# Outreach Pipeline

A Python CLI tool that automates cold outreach — from a single seed domain to personalized emails sent, with zero manual steps.

## What it does

1. **Ocean.io** — Finds lookalike companies for a seed domain
2. **Prospeo (Search)** — Finds C-suite and VP decision makers with LinkedIn URLs
3. **Prospeo (Enrich)** — Resolves each person to a verified work email
4. **Brevo** — Sends personalized outreach emails after confirmation

> Note: Eazyreach was evaluated for Stage 3 but does not expose a public API.
> Prospeo's Enrich endpoint was used instead — it performs the same function
> (LinkedIn profile → verified work email) and integrates cleanly into the pipeline.

## Project structure

- `.env` - local API keys (not committed)
- `requirements.txt` - required Python packages
- `main.py` - pipeline entry point
- `stages/` - one file per pipeline stage
- `utils/helpers.py` - caching, retry logic, and helpers
- `data/` - intermediate JSON output files
- `cache/` - shared response cache across runs (lookalikes, prospects, emails)
- `templates/` - email template file

## Setup

1. Create a Python environment:
```bash
python -m venv .venv
.venv/bin/activate       # macOS / Linux
.venv\Scripts\activate   # Windows PowerShell
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

Set these in `.env`:

| Variable | Description |
|----------|-------------|
| `OCEAN_API_KEY` | Ocean.io API token |
| `PROSPEO_API_KEY` | Prospeo API key (used for both search and enrich) |
| `BREVO_API_KEY` | Brevo API key for sending emails |
| `SENDER_NAME` | Your name shown in outreach emails |
| `SENDER_EMAIL` | Verified sender email address in Brevo |

## Usage

Run the full pipeline:
```bash
python main.py stripe.com
```

Dry run — executes all stages but skips sending emails:
```bash
python main.py stripe.com --dry-run
```

Skip Stage 2 and use existing `data/prospects.json`:
```bash
python main.py stripe.com --skip-stage2
```

## Output files

| File | Contents |
|------|----------|
| `data/domains.json` | Stage 1 — lookalike company domains |
| `data/prospects.json` | Stage 2 — decision makers with LinkedIn URLs |
| `data/emails.json` | Stage 3 — enriched records with verified emails |

## Features

- **Caching** — results saved locally and reused across runs, even across different seed domains
- **Retry logic** — every API call retries up to 3 times with exponential backoff
- **Graceful failure** — individual failures are logged and skipped without crashing the pipeline
- **Safety checkpoint** — shows full enriched list before sending any emails
- **Dry run mode** — test the full pipeline without sending emails