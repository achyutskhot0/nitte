from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os, subprocess, json, io, uuid
from PyPDF2 import PdfReader
import docx2txt

app = FastAPI()

# Static frontend at /static and root index
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def root():
    return FileResponse("frontend/index.html")

# Basic CORS (handy for dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.post("/summaries/{fid}")
def summarize(fid: str):
    txt_path = f"file_queue/{fid}.txt"
    if not os.path.exists(txt_path):
        return {"error": "file not found"}
    txt = open(txt_path, encoding="utf-8").read()

    # 1. classify
    try:
        legal = int(
            subprocess.check_output(
                ["python", "classifier/clf_infer.py"], input=txt, text=True
            ).strip()
        )
    except Exception as e:
        return {"error": f"classifier failed: {e}"}
    if not legal:
        return {"error": "not legal"}

    # 2. extract
    try:
        facts = json.loads(
            subprocess.check_output(["python", "extraction/extract.py"], input=txt, text=True)
        )
    except Exception as e:
        facts = {"error": f"extract failed: {e}"}

    # 3. summaries
    try:
        lawyer = json.loads(
            subprocess.check_output(["python", "summarisers/lawyer_sum.py"], input=txt, text=True)
        )
    except Exception as e:
        lawyer = {"error": f"lawyer summary failed: {e}"}

    try:
        citizen = json.loads(
            subprocess.check_output(["python", "summarisers/citizen_sum.py"], input=txt, text=True)
        )
    except Exception as e:
        citizen = {"error": f"citizen summary failed: {e}"}

    # 4. next steps
    try:
        nxt = json.loads(
            subprocess.check_output(["python", "nextsteps/next_steps.py"], input=txt, text=True)
        )
    except Exception as e:
        nxt = {"error": f"next steps failed: {e}"}

    return {"lawyer": lawyer, "citizen": citizen, "next": nxt, "facts": facts}
