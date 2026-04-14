from fastapi import APIRouter
from pydantic import BaseModel
import json
import os
from dotenv import load_dotenv

load_dotenv()

# ====== Router ======
router = APIRouter()

# ====== Request Schema ======
class TextRequest(BaseModel):
    text: str


# ====== CONFIG ======
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# ====== PROMPT ======
def build_prompt(user_text: str) -> str:
    return f"""
You are a system that converts natural language into JSON.

User input:
{user_text}

Return ONLY JSON. No explanation.

Example format (placeholder, can change later):
{{
  "object": "placeholder",
  "params": {{
    "size": "unknown",
    "features": []
  }}
}}
"""


# ====== AI CALL ======
def call_ai(prompt: str) -> str:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You output JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )

        return response.choices[0].message.content

    except Exception as e:
        print("AI call failed, fallback to mock:", e)

        # ===== fallback JSON =====
        return json.dumps({
            "object": "mock_object",
            "params": {
                "size": "40x40x20",
                "features": ["slot1", "slot2"]
            }
        })


# ====== PARSE JSON ======
def safe_parse_json(text: str):
    try:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]

        return json.loads(text)

    except Exception as e:
        print("JSON parse error:", e)
        return {
            "error": "invalid_json",
            "raw_output": text
        }


# ====== ROUTE ======
@router.post("/parse")
def parse_text(req: TextRequest):
    prompt = build_prompt(req.text)

    ai_output = call_ai(prompt)

    parsed_json = safe_parse_json(ai_output)

    return {
        "input": req.text,
        "ai_raw": ai_output,
        "parsed": parsed_json
    }