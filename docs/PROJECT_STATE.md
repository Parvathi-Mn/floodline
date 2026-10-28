# Floodline: project state (handoff file)

Last updated: 2026-10-28. Paste this file into a new chat to resume.

## What this is
A multilingual (Malayalam, English, Manglish) flood helpline agent for Kerala, built as a mock
client deployment for the Kerala SDMA. Demo project, not an official service.
Goal: portfolio piece for a Forward Deployed Engineer role (CallKaro AI).

## Stack
FastAPI backend, Gemini (google-genai) with function calling, Open-Meteo rainfall data,
single-file chat page served by the API. Model name and key live in .env (never committed).

## Run it
    .\backend\.venv\Scripts\Activate.ps1
    cd backend
    pytest
    ruff check .
    uvicorn app.main:app --reload     # chat page at http://127.0.0.1:8000/

## Layout
- backend/app: main.py, chat.py, config.py, risk.py, weather.py, settings.py
- backend/app/agent: loop.py, models.py, tools.py, prompt_loader.py, prompts/v1.md, providers/gemini.py
- clients/kerala.yaml: districts, languages, emergency numbers (client config)
- frontend/index.html: chat page
- docs: client-brief.md, risk-model.md, PROJECT_STATE.md

## Design rules
- Facts (risk, numbers) come from tools and config, never from the model's memory.
- Every conversation ends with a next step. Danger means 112 first.
- Provider failure returns a safe fallback message built from the client config.
- Never commit .env. Never log the API key. Log error types only.
- History messages can hold raw SDK objects ("raw"): never serialize them (logging stores name, args, content only).

## Status
Done: client brief, risk engine and API, agent loop, tools, settings, Gemini provider, /api/chat, chat page.
Next: verify emergency numbers, then Phase 3 (SQLite call logs, 20-30 eval scenarios,
prompt v2 and v3 with pass rates in docs/prompt-changelog.md), then Manglish/Malayalam tuning,
voice, dashboard, CI, README, demo video, v0.1.0 tag.

## Known issues
- Model answers use markdown (**bold**): prompt v2 must say plain text only.
- No relief-camp, road or dam data: agent must say so, never invent.
- One coordinate point per district; same rainfall thresholds for all hazards.
- Sessions are in memory and lost on restart.
- "Naidu et al. 2017" comment in risk.py is unverified: check the paper or reword.