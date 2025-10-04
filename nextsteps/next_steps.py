import spacy, re, json, sys

nlp = spacy.load("en_core_web_sm")
date_pat = re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b")

def parse(text: str):
    dates = sorted(set(date_pat.findall(text)))
    entities = [(ent.text, ent.label_) for ent in nlp(text).ents]
    return {"deadlines": dates, "entities": entities}

if __name__ == "__main__":
    print(json.dumps(parse(sys.stdin.read()), ensure_ascii=False))
