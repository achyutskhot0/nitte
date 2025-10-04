import joblib, sys, os

MODEL_PATHS = [
    os.path.join(os.path.dirname(__file__), "..", "weights", "legal_clf.joblib"),
    os.path.join(os.path.dirname(__file__), "weights", "legal_clf.joblib"),
    "weights/legal_clf.joblib",
]

model = None
for p in MODEL_PATHS:
    p = os.path.normpath(p)
    if os.path.exists(p):
        model = joblib.load(p)
        break

def simple_fallback(text: str) -> int:
    keywords = ["court", "petition", "respondent", "appellant", "tribunal", "hon'ble", "justice"]
    score = sum(k in text.lower() for k in keywords)
    return 1 if score >= 1 else 0

text = sys.stdin.read()
if model is None:
    print(simple_fallback(text))
else:
    try:
        print(int(model([text])[0]))
    except Exception:
        print(simple_fallback(text))
