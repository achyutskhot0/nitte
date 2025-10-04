import joblib, sys

model = joblib.load("weights/legal_clf.joblib")
text = sys.stdin.read()
print(int(model([text])[0]))
