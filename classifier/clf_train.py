from datasets import load_dataset
from setfit import SetFitModel
import joblib, os

# 1500 legal + 1500 random = 3 k samples → ~3 min on CPU
legal = load_dataset("sileod/legalbench", split="train[:1500]")
random = load_dataset("wikitext", "wikitext-2-raw-v1", split="train[:1500]")
texts = [d["text"] for d in legal] + [r["text"] for r in random]
labels = [1] * 1500 + [0] * 1500

model = SetFitModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model.train(texts, labels, batch_size=16, num_epochs=1)

os.makedirs("weights", exist_ok=True)
model.save_pretrained("weights/legal_clf")
joblib.dump(model, "weights/legal_clf.joblib")
