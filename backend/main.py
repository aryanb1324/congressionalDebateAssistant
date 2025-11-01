import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

from llm import get_llm_client
from prompts import (
    build_argument_prompt,
    build_po_prompt,
    build_speech_prompt,
    build_polish_prompt,
    build_chat_prompt,   # NEW
)

load_dotenv()

app = FastAPI(title="Debate Argument Generator API", version="0.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500", "http://localhost:5500",
        "https://*.netlify.app", "https://*.vercel.app"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateBody(BaseModel):
    bill: str
    speech_minutes: int = 2
    style: str = "nationals"
    novelty: str = "standard"   # "standard" | "high" | "wild"
    return_qx: bool = True
    return_full_speeches: bool = False
    polish: bool = True
    custom_instructions: Optional[str] = None  # NEW

class POBody(BaseModel):
    text: str

class ChatBody(BaseModel):
    message: str
    bill: Optional[str] = None
    style: str = "razor"
    novelty: str = "standard"

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/generate")
def generate(body: GenerateBody):
    if not body.bill or not body.bill.strip():
        raise HTTPException(400, "Bill text required")

    client = get_llm_client()

    # 1) Argument package
    pkg_prompt = build_argument_prompt(
        body.bill, body.speech_minutes, body.style, body.return_qx, body.novelty, body.custom_instructions
    )
    try:
        pkg_text = client.generate(pkg_prompt)
    except Exception as e:
        raise HTTPException(500, f"LLM error (package): {e}")

    # 1b) Polish package (optional)
    if body.polish:
        try:
            pol_prompt = build_polish_prompt(pkg_text, style=body.style, custom_instructions=body.custom_instructions)
            pkg_text = client.generate(pol_prompt)
        except Exception as e:
            raise HTTPException(500, f"LLM error (polish package): {e}")

    # 2) Full speeches (optional)
    speeches_text = None
    if body.return_full_speeches:
        sp_prompt = build_speech_prompt(
            body.bill, body.speech_minutes, body.style, body.novelty, body.custom_instructions
        )
        try:
            speeches_text = client.generate(sp_prompt)
            if body.polish:
                sp_pol_prompt = build_polish_prompt(speeches_text, style=body.style, custom_instructions=body.custom_instructions)
                speeches_text = client.generate(sp_pol_prompt)
        except Exception as e:
            raise HTTPException(500, f"LLM error (speeches): {e}")

    return {"ok": True, "result": pkg_text, "speeches": speeches_text}

@app.post("/api/chat")
def chat(body: ChatBody):
    client = get_llm_client()
    prompt = build_chat_prompt(body.message, body.bill, style=body.style, novelty=body.novelty)
    try:
        reply = client.generate(prompt)
        return {"ok": True, "result": reply}
    except Exception as e:
        raise HTTPException(500, f"LLM error (chat): {e}")

@app.post("/api/po-assist")
def po_assist(body: POBody):
    client = get_llm_client()
    prompt = build_po_prompt(body.text)
    try:
        result = client.generate(prompt)
        return {"ok": True, "result": result}
    except Exception as e:
        raise HTTPException(500, f"LLM error (po): {e}")
