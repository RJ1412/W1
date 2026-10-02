import os
import json
import time
import asyncio
from pathlib import Path
from openai import AsyncOpenAI

# Configuration
EVAL_MODELS = [
    os.getenv("LLM_MODEL", "llama3-8b-8192"), # Default hosted small
    "qwen2.5:0.5b",                           # Local small (if Ollama running)
    "llama3-70b-8192"                         # Hosted large
]

BASE_DIR = Path(__file__).resolve().parent.parent
QUESTIONS_FILE = BASE_DIR / "evals" / "questions.json"
PROMPT_FILE = BASE_DIR / "prompts" / "mentor_v1.txt"

def check_structure(response_text: str) -> bool:
    required_sections = [
        "### 💡 1. Quick Diagnosis",
        "### 🎯 2. Step-by-Step",
        "### ⚠️ 3. The Exam Trap",
        "### 🧠 4. Buddy's Pro-Tip"
    ]
    # flexible matching for headers
    for section in required_sections:
        # Check if basic string components exist to be resilient to minor formatting diffs
        part1 = section.split()[1]
        part2 = section.split()[2]
        if part1 not in response_text or part2 not in response_text:
            return False
    return True

async def run_eval_for_model(model: str, questions: list, prompt_template: str):
    # Setup client - if local model, assume ollama running on localhost
    if "qwen" in model or "gemma" in model:
        client = AsyncOpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    else:
        client = AsyncOpenAI(
            base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
            api_key=os.getenv("LLM_API_KEY", "")
        )

    results = []
    start_time = time.time()
    valid_structure_count = 0
    
    print(f"\\n--- Running Eval for Model: {model} ---")
    for idx, q in enumerate(questions):
        prompt = prompt_template.format(
            exam=q["exam"],
            student_name="EvalUser",
            lang_instruction="Friendly Hinglish",
            question=q["question"],
            answer=q["answer"]
        )
        try:
            t0 = time.time()
            resp = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            t1 = time.time()
            reply = resp.choices[0].message.content
            
            is_valid = check_structure(reply)
            if is_valid:
                valid_structure_count += 1
                
            results.append({
                "time_s": t1 - t0,
                "valid": is_valid
            })
            print(f"Q{idx+1}: {t1-t0:.2f}s | Structured: {is_valid}")
        except Exception as e:
            print(f"Q{idx+1} Failed: {e}")
            results.append({"time_s": 0, "valid": False})

    total_time = time.time() - start_time
    avg_latency = sum(r["time_s"] for r in results if r["time_s"] > 0) / len([r for r in results if r["time_s"] > 0]) if results else 0
    structure_rate = (valid_structure_count / len(questions)) * 100
    
    return {
        "model": model,
        "structure_rate": structure_rate,
        "avg_latency": avg_latency
    }

async def main():
    with open(QUESTIONS_FILE, "r") as f:
        questions = json.load(f)
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    print(f"Evaluating {len(questions)} questions on {len(EVAL_MODELS)} models...")
    
    summary = []
    for model in EVAL_MODELS:
        res = await run_eval_for_model(model, questions, prompt_template)
        summary.append(res)
        
    print("\\n### Evaluation Summary Markdown Table ###")
    print("| Model | Structure Format Rate (%) | Avg Latency (s) |")
    print("|-------|---------------------------|-----------------|")
    for r in summary:
        print(f"| {r['model']} | {r['structure_rate']:.1f}% | {r['avg_latency']:.2f}s |")

if __name__ == "__main__":
    asyncio.run(main())
