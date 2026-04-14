# DeskOrganizer

DeskOrganizer is a FastAPI service that uses an AI API to convert user natural-language input into structured JSON, then uses that structure to generate desk-organizer object definitions.

## What this project does

- Accepts user text input (for example: preferred desk organizer size/features).
- Sends a prompt to the AI model.
- Returns:
	- raw AI output
	- parsed JSON output
- Provides a foundation for generating desk-organizer objects from the parsed result.

Current API route:

- `POST /parse`

## Quick start

### 1) Create and activate a virtual environment

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```bash
./venv/bin/pip install -r requirements.txt 
```

### 3) Set environment variable

Set your OpenAI API key before running the server.

### 4) Start the project

From the project root:

```bash
uvicorn app.main:app --reload
```

Server default URL:

- `http://127.0.0.1:8000`

## Notes

- If AI API call fails, the app currently falls back to a mock JSON response.
- Parsed JSON appears in the `parsed` field of the API response.
