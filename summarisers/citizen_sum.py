import sys, json
from together_client import call_llm

system = "You are a helpful Indian legal advisor for the public. Return only JSON."
prompt = open("/workspace/prompts/citizen.txt", encoding="utf-8").read().replace("{{TEXT}}", sys.stdin.read())
print(call_llm(system, prompt))
