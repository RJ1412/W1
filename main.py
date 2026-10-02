from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import asyncio
import httpx
import os
import html
import socket

# Prioritize IPv4 on Windows to prevent network timeouts to Google API endpoints
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_first_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    try:
        res = _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
        if res:
            return res
    except Exception:
        pass
    return _orig_getaddrinfo(host, port, family, type, proto, flags)
socket.getaddrinfo = _ipv4_first_getaddrinfo

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Universal Exam Study Buddy")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6JvWkjDez0LJyMON7cB1osRLbGOnLizlTOodVuttsA2Qw")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "")  # leave empty to use auto-fallback
GEMINI_MODEL_FALLBACKS = [
    "gemini-2.5-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
]

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/ask", response_class=HTMLResponse)
async def ask_question(
    request: Request,
    question: str = Form(...),
    answer: str = Form(...),
    exam: str = Form("SSC CGL"),
    student_name: str = Form("Aman"),
    language: str = Form("Hinglish")
):
    student_name = student_name.strip() or "Aspirant"
    exam = exam.strip() or "Competitive Exam"
    
    if language == "English":
        lang_instruction = "Clear, encouraging English. Use professional yet accessible phrasing, highlighting exam terminology."
    elif language == "Hindi":
        lang_instruction = "Clear and encouraging Hindi (Devanagari script), keeping standard technical/exam terms in English."
    else:
        lang_instruction = "Friendly, informal Hinglish (Roman script). Keep exam and subject terms in English (e.g., quant, reasoning, percentile, speed-time, elimination)."

    prompt = f"""You are an elite competitive exam mentor and friendly study buddy specializing in {exam}.
The student ({student_name}) got a mock test or practice question wrong.
Explain their mistake with high energy, supportive empathy, and razor-sharp exam clarity.

Target Exam: {exam}
Student Name: {student_name}
Language / Tone: {lang_instruction}

Question:
{question}

Student's Marked Option / Mistake:
{answer}

Please structure your explanation using clean GitHub-flavored Markdown with these exact sections:

### 💡 1. Quick Diagnosis: Where the Logic Tripped
(Explain in 2-3 friendly sentences where the student's thought process went off track—e.g., calculation rush, misinterpreting the phrasing, or falling for a common distractor.)

### 🎯 2. Step-by-Step Correct Solution
(Provide a clear, methodical walkthrough. Highlight key numbers, formulas, and intermediate deductions in **bold** so it's super easy to scan.)

### ⚠️ 3. The Exam Trap (Distractor Breakdown)
(Explain why the question setter designed this specific trap and why students commonly mark this wrong option in {exam}.)

### 🧠 4. Buddy's Pro-Tip & Speed Trick
(Provide a 30-second shortcut, elimination technique, or memory trick to guarantee they never get this type of question wrong again.)

Conclude with a brief 1-line motivational cheer for {student_name}!
"""

    # Use env-override model, or auto-select first working from fallback list
    models_to_try = [GEMINI_MODEL] if GEMINI_MODEL else GEMINI_MODEL_FALLBACKS

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048}
    }

    llm_reply = ""
    error_msg = None

    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"

        for attempt in range(2):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=payload, timeout=60.0)

                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        llm_reply = "".join(p.get("text", "") for p in parts)
                    else:
                        llm_reply = "No answer generated. Please try again."
                    error_msg = None
                    break  # success — stop retrying this model

                elif response.status_code == 404:
                    error_msg = f"model_not_found:{model}"
                    break  # try next model in fallback list

                elif response.status_code == 429 and attempt == 0:
                    try:
                        details = response.json().get("error", {}).get("details", [])
                        retry_delay = 30
                        for d in details:
                            if d.get("@type", "").endswith("RetryInfo"):
                                raw = d.get("retryDelay", "30s")
                                retry_delay = int("".join(filter(str.isdigit, raw))) + 2
                        retry_delay = min(retry_delay, 35)
                    except Exception:
                        retry_delay = 30
                    await asyncio.sleep(retry_delay)
                    continue  # retry same model after waiting

                elif response.status_code == 429:
                    error_msg = (
                        "Daily free quota exhausted (20 req/day per key). "
                        "Get a new API key at aistudio.google.com/app/apikey "
                        "or wait until 5:30 AM IST for reset."
                    )
                    break

                elif response.status_code == 503 and attempt == 0:
                    await asyncio.sleep(3)
                    continue

                else:
                    error_msg = f"API error {response.status_code} on model {model}."
                    break

            except Exception as e:
                if attempt == 0:
                    await asyncio.sleep(1)
                    continue
                error_msg = f"Connection error: {str(e)}"

        if llm_reply:
            break  # got a response — stop trying other models
        if error_msg and not error_msg.startswith("model_not_found"):
            break  # real error (quota/connection) — don't try more models

    # If all models returned 404
    if not llm_reply and (not error_msg or error_msg.startswith("model_not_found")):
        error_msg = (
            "No compatible model found for your API key. "
            "Please get a new key at aistudio.google.com/app/apikey"
        )

    if error_msg:
        return f"""
        <div class="rounded-xl border border-[#e3d7c8] bg-[#fdfbf9] p-5 text-[#5c4033]">
            <p class="font-semibold text-sm text-[#3a271e]">Quota Limit Reached</p>
            <p class="mt-1 text-xs text-[#8c684e]">{html.escape(error_msg)}</p>
        </div>
        """


    escaped_markdown = html.escape(llm_reply)
    escaped_exam = html.escape(exam)
    escaped_student = html.escape(student_name)

    return f"""
    <div id="solution-card" class="rounded-2xl border border-[#e3d7c8] bg-white overflow-hidden">
        <!-- Warm header -->
        <div class="bg-[#f8f5f0] border-b border-[#e3d7c8] px-5 py-4 flex items-center justify-between">
            <div>
                <span class="text-xs font-semibold text-[#8c684e] uppercase tracking-wide">Buddy's Explanation</span>
                <div class="flex items-center gap-2 mt-0.5">
                    <span class="text-sm font-semibold text-[#3a271e]">{escaped_exam}</span>
                    <span class="text-xs text-[#ba9e89]">for {escaped_student}</span>
                </div>
            </div>
            <button type="button" onclick="copySolution()" id="copy-btn"
                class="text-xs font-medium text-[#8c684e] hover:text-[#5c4033] border border-[#d7c7b8] hover:border-[#ba9e89] rounded-lg px-3 py-1.5 transition-colors bg-white">
                Copy
            </button>
        </div>

        <!-- Formatted Content -->
        <div class="p-5 sm:p-7">
            <textarea id="raw-markdown-content" class="hidden">{escaped_markdown}</textarea>
            <div id="formatted-solution" class="text-sm text-[#4a382e] leading-relaxed">
                <div class="whitespace-pre-wrap">{escaped_markdown}</div>
            </div>
        </div>

        <!-- Footer -->
        <div class="border-t border-[#efe8de] px-5 py-3 flex items-center justify-between">
            <span class="text-xs text-[#ba9e89]">Powered by Gemini</span>
            <button type="button"
                onclick="document.getElementById('question-input').scrollIntoView({{behavior:'smooth'}}); document.getElementById('question-input').focus();"
                class="text-xs font-medium text-[#8c684e] hover:text-[#5c4033] transition-colors">
                Try another &uarr;
            </button>
        </div>
    </div>
    """
