from fastapi import FastAPI, UploadFile, File
from PyPDF2 import PdfReader
import io, os, uuid
import docx2txt

app = FastAPI()
UPLOAD_DIR = "file_queue"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def extract_text(file: UploadFile) -> str:
    if file.content_type == "application/pdf":
        reader = PdfReader(io.BytesIO(file.file.read()))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return docx2txt.process(io.BytesIO(file.file.read()))
    else:
        return file.file.read().decode(errors="ignore")

@app.post("/upload")
async def upload(files: list[UploadFile] = File(...)):
    ids: list[str] = []
    for f in files:
        txt = extract_text(f)
        fid = str(uuid.uuid4())
        with open(f"{UPLOAD_DIR}/{fid}.txt", "w", encoding="utf-8") as out:
            out.write(txt)
        ids.append(fid)
    return {"file_ids": ids}
