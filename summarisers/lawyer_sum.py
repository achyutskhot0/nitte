import sys, json, os
from together_client import call_llm

system = "You are an Indian lawyer. Return only JSON."
PROMPT_PATH = os.path.join(os.path.dirname(__file__), os.pardir, "prompts", "lawyer.txt")
prompt = open(os.path.normpath(PROMPT_PATH), encoding="utf-8").read().replace("{{TEXT}}", sys.stdin.read())
print(call_llm(system, prompt))
