import sys, json, os
from together_client import call_llm

system = "You are a helpful Indian legal advisor for the public. Return only JSON."
PROMPT_PATH = os.path.join(os.path.dirname(__file__), os.pardir, "prompts", "citizen.txt")
prompt = open(os.path.normpath(PROMPT_PATH), encoding="utf-8").read().replace("{{TEXT}}", sys.stdin.read())
print(call_llm(system, prompt))
