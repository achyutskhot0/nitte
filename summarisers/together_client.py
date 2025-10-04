import os, requests

KEY = os.getenv("TOGETHER_KEY") or "YOUR_FREE_KEY"
URL = "https://api.together.xyz/v1/chat/completions"
HEAD = {"Authorization": f"Bearer {KEY}"}

def call_llm(system: str, user: str) -> str:
    payload = {
        "model": "meta-llama/Llama-3.2-3B-Instruct-Turbo",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": 1000,
    }
    r = requests.post(URL, headers=HEAD, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]
