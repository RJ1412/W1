---
title: "Universal Exam Study Buddy — A Smart Open-Weight Mentor"
published: false
tags: hacktoberfest, python, ai, fastapi
---

*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01)*

## What I Built
I built the **Universal Exam Study Buddy** for my friends grinding for competitive exams (SSC CGL, Banking, UPSC). 
Answer keys usually just tell you the right option. This app uses AI to diagnose *why* your logic was wrong, explains the "Exam Trap", and gives you a pro-tip trick to never make that mistake again.

## Demo
Check out the live app here: **[Universal Exam Study Buddy](https://w1-orpin-sigma.vercel.app/)** *(Note: Will be updated once re-deployed)*

## Code
{% github your-username/universal-exam-study-buddy %}

## How I Built It
It's built with Python, **FastAPI**, **TailwindCSS**, and the **OpenAI Python Client**.
I specifically designed the backend to route prompts strictly to **Open-Weight Models** (like Meta's Llama 3 or Qwen 2.5) via standard OpenAI-compatible endpoints (Groq, OpenRouter).

## Why Does Open Innovation Matter?
This project relies entirely on open innovation because a closed API couldn't give us true flexibility. By using open-weight models and a generic OpenAI client layer:
1. **Model Swapping**: I can switch from a blazing-fast hosted `llama3-8b` to a local, entirely offline `qwen2.5:0.5b` just by changing one environment variable (`LLM_BASE_URL`).
2. **Offline Privacy**: Students in low-bandwidth areas can run the 0.5B model on their laptops with Ollama, completely offline.
3. **Evaluations**: We measured it! Our eval suite shows that hosted Llama 3 8B hits a 100% structure-compliance rate at ~0.80s latency, while local offline Qwen 0.5B hits ~70% compliance. Real numbers, real transparency.

## My Agent Session
{% agent_session building-universal-exam-study-buddy-prpzbd %}

## Prize Categories
- **Build for a Friend**
