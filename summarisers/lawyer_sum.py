import sys, json
from together_client import call_llm

system = "You are an Indian lawyer. Return only JSON."
prompt = open("/workspace/prompts/lawyer.txt", encoding="utf-8").read().replace("{{TEXT}}", sys.stdin.read())
print(call_llm(system, prompt))
