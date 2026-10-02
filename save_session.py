import json
import os
import subprocess

TRANSCRIPT_PATH = r"C:\Users\rahul\.gemini\antigravity-ide\brain\353ca77a-ad22-4938-b9cd-fcdfc26417b6\.system_generated\logs\transcript.jsonl"
OUT_PATH = "session_data.json"

messages = []
try:
    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            event = json.loads(line)
            
            # Simple conversion from transcript to DevRelay format
            if event.get("type") == "USER_INPUT":
                messages.append({
                    "role": "user",
                    "content": [{"type": "text", "text": event.get("content", "")}]
                })
            elif event.get("type") == "PLANNER_RESPONSE":
                content = []
                if event.get("content"):
                    content.append({"type": "text", "text": event.get("content", "")})
                
                tool_calls = event.get("tool_calls", [])
                for tc in tool_calls:
                    content.append({
                        "type": "tool_call",
                        "name": tc.get("function", {}).get("name", "unknown"),
                        "input": json.dumps(tc.get("function", {}).get("arguments", {})),
                        "output": "..."
                    })
                
                if content:
                    messages.append({
                        "role": "assistant",
                        "model": "gemini-3.1-pro", # assuming current
                        "content": content
                    })

    curated_data = {
        "messages": messages,
        "metadata": {
            "tool_name": "gemini_cli",
            "session_id": "353ca77a-ad22-4938-b9cd-fcdfc26417b6",
            "total_messages": len(messages)
        }
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(curated_data, f)
        
    print(f"Created {OUT_PATH} with {len(messages)} messages.")
    
    # Run devrelay submit
    result = subprocess.run([
        "devrelay", "sessions", "submit", 
        "--title", "Building Universal Exam Study Buddy", 
        "--file", OUT_PATH
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("ERR:", result.stderr)

except Exception as e:
    print(f"Error: {e}")
