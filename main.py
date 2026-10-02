import os
import html
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from openai import AsyncOpenAI, APIConnectionError, RateLimitError
from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Universal Exam Study Buddy")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Open-weight model config
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "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")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
FALLBACK_STR = os.getenv("LLM_FALLBACK_MODELS", "openai/gpt-oss-20b,llama-3.1-8b-instant")
LLM_FALLBACK_MODELS = [m.strip() for m in FALLBACK_STR.split(",") if m.strip()]

# Determine if model is "small" (< 3B params) for UI warning
def is_small_model(model_name: str) -> bool:
    name = model_name.lower()
    return "0.5b" in name or "1b" in name or "1.5b" in name or "2b" in name

client = AsyncOpenAI(
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY
)

@app.get("/api/health")
async def health_check():
    return JSONResponse({
        "status": "ok",
        "model": LLM_MODEL,
        "is_small": is_small_model(LLM_MODEL)
    })

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

    prompt_path = BASE_DIR / "prompts" / "mentor_v1.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    prompt = prompt_template.format(
        exam=exam,
        student_name=student_name,
        lang_instruction=lang_instruction,
        question=question,
        answer=answer
    )

    models_to_try = [LLM_MODEL] + LLM_FALLBACK_MODELS
    llm_reply = ""
    error_msg = None
    used_model = LLM_MODEL

    for model in models_to_try:
        used_model = model
        for attempt in range(2):
            try:
                response = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2048,
                    timeout=60.0
                )
                if response.choices and response.choices[0].message.content:
                    llm_reply = response.choices[0].message.content
                    error_msg = None
                else:
                    error_msg = "No answer generated. Please try again."
                break  # success or empty response
                
            except RateLimitError as e:
                if attempt == 0:
                    await asyncio.sleep(4)
                    continue
                error_msg = f"Rate limit exhausted for {model}. Try later."
                break
            except APIConnectionError as e:
                if attempt == 0:
                    await asyncio.sleep(2)
                    continue
                error_msg = f"Connection error to API. Please check your internet or LLM_BASE_URL."
                break
            except Exception as e:
                err_str = str(e).lower()
                if "404" in err_str or "not found" in err_str:
                    error_msg = f"model_not_found"
                    break # try next model
                if attempt == 0:
                    await asyncio.sleep(2)
                    continue
                error_msg = f"API error: {str(e)}"
                break
                
        if llm_reply:
            break
        if error_msg and error_msg != "model_not_found":
            break

    if not llm_reply and error_msg == "model_not_found":
        error_msg = "No compatible models found. Please check your LLM_MODEL configuration."

    if error_msg:
        return f"""
        <div class="rounded-xl border border-[#e3d7c8] bg-[#fdfbf9] p-5 text-[#5c4033]">
            <p class="font-semibold text-sm text-[#3a271e]">Connection or Quota Issue</p>
            <p class="mt-1 text-xs text-[#8c684e]">{html.escape(error_msg)}</p>
        </div>
        """

    escaped_markdown = html.escape(llm_reply)
    escaped_exam = html.escape(exam)
    escaped_student = html.escape(student_name)
    
    warning_html = ""
    if is_small_model(used_model):
        warning_html = """
        <div class="bg-orange-50 border-b border-orange-100 px-5 py-2 text-[11px] text-orange-800 flex items-center gap-2">
            <span>⚠️</span> Small model active. Double-check math answers.
        </div>
        """

    return f"""
    <div id="solution-card" class="rounded-2xl border border-[#e3d7c8] bg-white overflow-hidden">
        {warning_html}
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

        <div class="p-5 sm:p-7">
            <textarea id="raw-markdown-content" class="hidden">{escaped_markdown}</textarea>
            <div id="formatted-solution" class="text-sm text-[#4a382e] leading-relaxed">
                <div class="whitespace-pre-wrap">{escaped_markdown}</div>
            </div>
        </div>

        <div class="border-t border-[#efe8de] px-5 py-3 flex items-center justify-between">
            <span class="text-[10px] text-[#ba9e89] uppercase tracking-wider font-semibold">Powered by {html.escape(used_model)} • open-weight</span>
            <button type="button"
                onclick="document.getElementById('question-input').scrollIntoView({{behavior:'smooth'}}); document.getElementById('question-input').focus();"
                class="text-xs font-medium text-[#8c684e] hover:text-[#5c4033] transition-colors">
                Try another &uarr;
            </button>
        </div>
    </div>
    """
