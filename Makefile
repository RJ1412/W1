.PHONY: run setup install-model

setup:
	pip install -r requirements.txt

run:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

install-model:
	ollama pull qwen2.5:1.5b
