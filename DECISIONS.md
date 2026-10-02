# Architectural Decisions

## Open-Weight Shift
Removed proprietary Gemini models in favor of open-weight models accessed via OpenAI-compatible endpoints (Groq, OpenRouter, or local Ollama).
*Why*: Open innovation. Prevents vendor lock-in, enables self-hosting for offline use, and aligns with the Hacktoberfest open-source ethos.

## Model Selection
**Default:** Llama 3 8B (via Groq/OpenRouter). 
*Why*: It offers an excellent balance of speed and reasoning for math and multilingual (Hinglish) capabilities, remaining small enough to fall within the open-weight paradigm without compromising logic breakdown.
**Local Fallback:** Qwen 2.5 0.5B (via Ollama).
*Why*: Can easily run on standard laptops offline, providing immediate fallback capability, though it warrants a "double-check math" warning due to its small size.

## Flexible API Layer
Replaced the Google Gemini client with standard `openai` python library.
*Why*: The OpenAI client is the defacto standard for almost all open-weight inference APIs. It allows switching between hosted Groq/OpenRouter and local Ollama merely by changing environment variables.

## Prompt Extraction
Moved prompt from hardcoded strings to `prompts/mentor_v1.txt`.
*Why*: Easier evaluation, iteration, and cleaner code separation.
