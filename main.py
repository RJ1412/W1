from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5:1.5b")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask", response_class=HTMLResponse)
async def ask_question(request: Request, question: str = Form(...), answer: str = Form(...)):
    prompt = f"""You are Aman's study buddy. He is preparing for the SSC CGL exam.
He got a mock test question wrong. Explain his mistake in friendly, informal Hinglish (Roman script). Keep exam terms in English (like reasoning, quant, percentile).
Question: {question}
Aman's Answer: {answer}
Explain briefly why this is wrong and what the right approach is:"""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(OLLAMA_URL, json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            }, timeout=60.0)
            
        if response.status_code == 200:
            llm_reply = response.json().get("response", "No response from model.")
        else:
            llm_reply = f"Error from Ollama: {response.text}"
    except Exception as e:
        llm_reply = f"Error connecting to local AI (Ensure Ollama is running): {str(e)}"

    return f'<div class="mt-4 p-4 bg-blue-50 border border-blue-200 rounded"><strong>Buddy Says:</strong><p class="mt-2 whitespace-pre-wrap">{llm_reply}</p></div>'
