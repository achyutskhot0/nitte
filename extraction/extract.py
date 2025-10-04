import spacy, yaml, re, json, sys

nlp = spacy.load("en_core_web_sm")
fields = yaml.safe_load(open("/workspace/extraction/fields.yaml", encoding="utf-8"))["fields"]

def extract(text: str):
    data = {}
    for field in fields:
        if "pattern" in field:
            try:
                data[field["name"]] = re.findall(field["pattern"], text)
            except re.error:
                data[field["name"]] = []
        if "keywords" in field:
            sentences = [sent.text for sent in nlp(text).sents]
            data[field["name"]] = [s for s in sentences if any(k in s.lower() for k in field["keywords"]) ]
    return data

if __name__ == "__main__":
    print(json.dumps(extract(sys.stdin.read()), ensure_ascii=False))
