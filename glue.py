from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os, subprocess, json, io, uuid, time, sqlite3
from PyPDF2 import PdfReader
import docx2txt
from datetime import datetime
from typing import List, Dict, Optional
import asyncio
from pathlib import Path

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
RESULTS_DIR = "results"
DB_FILE = "legal_lens.db"

# Create directories
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_size INTEGER,
            content_type TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            status TEXT DEFAULT 'uploaded'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            file_id TEXT PRIMARY KEY,
            lawyer_summary TEXT,
            citizen_summary TEXT,
            next_steps TEXT,
            key_facts TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files (id)
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove disconnected connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

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
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    ids: list[str] = []
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        for f in files:
            # Validate file type
            if f.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {f.content_type}")
            
            # Extract text
            txt = extract_text(f)
            if not txt.strip():
                raise HTTPException(status_code=400, detail=f"Could not extract text from {f.filename}")
            
            # Generate unique ID
            fid = str(uuid.uuid4())
            
            # Save text file
            with open(f"{UPLOAD_DIR}/{fid}.txt", "w", encoding="utf-8") as out:
                out.write(txt)
            
            # Store file info in database
            cursor.execute('''
                INSERT INTO files (id, filename, original_name, file_size, content_type, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (fid, f"{fid}.txt", f.filename, f.size, f.content_type, 'uploaded'))
            
            ids.append(fid)
        
        conn.commit()
        return {"file_ids": ids, "message": f"Successfully uploaded {len(files)} file(s)"}
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/summaries/{fid}")
async def summarize(fid: str, background_tasks: BackgroundTasks):
    # Check if file exists
    txt_path = f"{UPLOAD_DIR}/{fid}.txt"
    if not os.path.exists(txt_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if already processed
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT status FROM files WHERE id = ?", (fid,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="File not found in database")
        
        if result[0] == 'processed':
            # Return cached results
            cursor.execute("SELECT * FROM results WHERE file_id = ?", (fid,))
            result = cursor.fetchone()
            if result:
                return {
                    "lawyer": json.loads(result[1]) if result[1] else {},
                    "citizen": json.loads(result[2]) if result[2] else {},
                    "next": json.loads(result[3]) if result[3] else {},
                    "facts": json.loads(result[4]) if result[4] else {}
                }
        
        # Update status to processing
        cursor.execute("UPDATE files SET status = 'processing' WHERE id = ?", (fid,))
        conn.commit()
        
        # Read text
        with open(txt_path, encoding="utf-8") as f:
            txt = f.read()
        
        # Process the document with progress updates
        results = await process_document_with_progress(txt, fid)
        
        # Store results in database
        cursor.execute('''
            INSERT OR REPLACE INTO results (file_id, lawyer_summary, citizen_summary, next_steps, key_facts)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            fid,
            json.dumps(results["lawyer"]),
            json.dumps(results["citizen"]),
            json.dumps(results["next"]),
            json.dumps(results["facts"])
        ))
        
        # Update file status
        cursor.execute("UPDATE files SET status = 'processed', processed_at = CURRENT_TIMESTAMP WHERE id = ?", (fid,))
        conn.commit()
        
        return results
        
    except Exception as e:
        cursor.execute("UPDATE files SET status = 'error' WHERE id = ?", (fid,))
        conn.commit()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

async def process_document_with_progress(txt: str, fid: str) -> Dict:
    """Process document with real-time progress updates"""
    results = {
        "lawyer": {},
        "citizen": {},
        "next": {},
        "facts": {}
    }
    
    # Send progress update
    await manager.broadcast(json.dumps({
        "type": "progress",
        "file_id": fid,
        "step": "classifying",
        "progress": 10,
        "message": "Classifying document..."
    }))
    
    # 1. Classify
    try:
        legal = int(
            subprocess.check_output(
                ["python", "classifier/clf_infer.py"], input=txt, text=True
            ).strip()
        )
        if not legal:
            results["lawyer"] = {"error": "Document is not legal in nature"}
            results["citizen"] = {"error": "Document is not legal in nature"}
            await manager.broadcast(json.dumps({
                "type": "progress",
                "file_id": fid,
                "step": "complete",
                "progress": 100,
                "message": "Document is not legal in nature"
            }))
            return results
    except Exception as e:
        results["lawyer"] = {"error": f"Classification failed: {e}"}
        results["citizen"] = {"error": f"Classification failed: {e}"}
        await manager.broadcast(json.dumps({
            "type": "progress",
            "file_id": fid,
            "step": "error",
            "progress": 0,
            "message": f"Classification failed: {e}"
        }))
        return results

    # Send progress update
    await manager.broadcast(json.dumps({
        "type": "progress",
        "file_id": fid,
        "step": "extracting_facts",
        "progress": 30,
        "message": "Extracting key facts..."
    }))

    # 2. Extract facts
    try:
        facts = json.loads(
            subprocess.check_output(["python", "extraction/extract.py"], input=txt, text=True)
        )
        results["facts"] = facts
    except Exception as e:
        results["facts"] = {"error": f"Fact extraction failed: {e}"}

    # Send progress update
    await manager.broadcast(json.dumps({
        "type": "progress",
        "file_id": fid,
        "step": "generating_lawyer_summary",
        "progress": 50,
        "message": "Generating legal analysis..."
    }))

    # 3. Generate lawyer summary
    try:
        lawyer = json.loads(
            subprocess.check_output(["python", "summarisers/lawyer_sum.py"], input=txt, text=True)
        )
        results["lawyer"] = lawyer
    except Exception as e:
        results["lawyer"] = {"error": f"Lawyer summary failed: {e}"}

    # Send progress update
    await manager.broadcast(json.dumps({
        "type": "progress",
        "file_id": fid,
        "step": "generating_citizen_summary",
        "progress": 70,
        "message": "Generating citizen summary..."
    }))

    # 4. Generate citizen summary
    try:
        citizen = json.loads(
            subprocess.check_output(["python", "summarisers/citizen_sum.py"], input=txt, text=True)
        )
        results["citizen"] = citizen
    except Exception as e:
        results["citizen"] = {"error": f"Citizen summary failed: {e}"}

    # Send progress update
    await manager.broadcast(json.dumps({
        "type": "progress",
        "file_id": fid,
        "step": "extracting_next_steps",
        "progress": 90,
        "message": "Extracting next steps..."
    }))

    # 5. Extract next steps
    try:
        nxt = json.loads(
            subprocess.check_output(["python", "nextsteps/next_steps.py"], input=txt, text=True)
        )
        results["next"] = nxt
    except Exception as e:
        results["next"] = {"error": f"Next steps extraction failed: {e}"}

    # Send completion update
    await manager.broadcast(json.dumps({
        "type": "progress",
        "file_id": fid,
        "step": "complete",
        "progress": 100,
        "message": "Processing complete!"
    }))

    return results

async def process_document(txt: str, fid: str) -> Dict:
    """Process document through all analysis steps"""
    results = {
        "lawyer": {},
        "citizen": {},
        "next": {},
        "facts": {}
    }
    
    # 1. Classify
    try:
        legal = int(
            subprocess.check_output(
                ["python", "classifier/clf_infer.py"], input=txt, text=True
            ).strip()
        )
        if not legal:
            results["lawyer"] = {"error": "Document is not legal in nature"}
            results["citizen"] = {"error": "Document is not legal in nature"}
            return results
    except Exception as e:
        results["lawyer"] = {"error": f"Classification failed: {e}"}
        results["citizen"] = {"error": f"Classification failed: {e}"}
        return results

    # 2. Extract facts
    try:
        facts = json.loads(
            subprocess.check_output(["python", "extraction/extract.py"], input=txt, text=True)
        )
        results["facts"] = facts
    except Exception as e:
        results["facts"] = {"error": f"Fact extraction failed: {e}"}

    # 3. Generate summaries
    try:
        lawyer = json.loads(
            subprocess.check_output(["python", "summarisers/lawyer_sum.py"], input=txt, text=True)
        )
        results["lawyer"] = lawyer
    except Exception as e:
        results["lawyer"] = {"error": f"Lawyer summary failed: {e}"}

    try:
        citizen = json.loads(
            subprocess.check_output(["python", "summarisers/citizen_sum.py"], input=txt, text=True)
        )
        results["citizen"] = citizen
    except Exception as e:
        results["citizen"] = {"error": f"Citizen summary failed: {e}"}

    # 4. Extract next steps
    try:
        nxt = json.loads(
            subprocess.check_output(["python", "nextsteps/next_steps.py"], input=txt, text=True)
        )
        results["next"] = nxt
    except Exception as e:
        results["next"] = {"error": f"Next steps extraction failed: {e}"}

    return results

# File management endpoints
@app.get("/files")
async def list_files():
    """List all uploaded files"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, original_name, file_size, uploaded_at, processed_at, status
            FROM files
            ORDER BY uploaded_at DESC
        ''')
        files = cursor.fetchall()
        
        return [
            {
                "id": f[0],
                "name": f[1],
                "size": f[2],
                "uploaded_at": f[3],
                "processed_at": f[4],
                "status": f[5]
            }
            for f in files
        ]
    finally:
        conn.close()

@app.get("/files/{file_id}")
async def get_file_info(file_id: str):
    """Get information about a specific file"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, original_name, file_size, uploaded_at, processed_at, status
            FROM files
            WHERE id = ?
        ''', (file_id,))
        file_info = cursor.fetchone()
        
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
        
        return {
            "id": file_info[0],
            "name": file_info[1],
            "size": file_info[2],
            "uploaded_at": file_info[3],
            "processed_at": file_info[4],
            "status": file_info[5]
        }
    finally:
        conn.close()

@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Delete a file and its results"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Check if file exists
        cursor.execute("SELECT filename FROM files WHERE id = ?", (file_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="File not found")
        
        filename = result[0]
        
        # Delete from database
        cursor.execute("DELETE FROM results WHERE file_id = ?", (file_id,))
        cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
        conn.commit()
        
        # Delete physical files
        txt_path = f"{UPLOAD_DIR}/{filename}"
        if os.path.exists(txt_path):
            os.remove(txt_path)
        
        return {"message": "File deleted successfully"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/files/{file_id}/results")
async def get_file_results(file_id: str):
    """Get analysis results for a specific file"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT lawyer_summary, citizen_summary, next_steps, key_facts
            FROM results
            WHERE file_id = ?
        ''', (file_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Results not found")
        
        return {
            "lawyer": json.loads(result[0]) if result[0] else {},
            "citizen": json.loads(result[1]) if result[1] else {},
            "next": json.loads(result[2]) if result[2] else {},
            "facts": json.loads(result[3]) if result[3] else {}
        }
    finally:
        conn.close()

@app.post("/files/{file_id}/reprocess")
async def reprocess_file(file_id: str):
    """Reprocess a file"""
    # Check if file exists
    txt_path = f"{UPLOAD_DIR}/{file_id}.txt"
    if not os.path.exists(txt_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Reset status and reprocess
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE files SET status = 'uploaded' WHERE id = ?", (file_id,))
        cursor.execute("DELETE FROM results WHERE file_id = ?", (file_id,))
        conn.commit()
        
        # Trigger reprocessing
        return await summarize(file_id, BackgroundTasks())
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Statistics endpoint
@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Total files
        cursor.execute("SELECT COUNT(*) FROM files")
        total_files = cursor.fetchone()[0]
        
        # Processed files
        cursor.execute("SELECT COUNT(*) FROM files WHERE status = 'processed'")
        processed_files = cursor.fetchone()[0]
        
        # Error files
        cursor.execute("SELECT COUNT(*) FROM files WHERE status = 'error'")
        error_files = cursor.fetchone()[0]
        
        # Total size
        cursor.execute("SELECT SUM(file_size) FROM files")
        total_size = cursor.fetchone()[0] or 0
        
        return {
            "total_files": total_files,
            "processed_files": processed_files,
            "error_files": error_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
    finally:
        conn.close()

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # Echo back for now, can be extended for specific commands
            await manager.send_personal_message(f"Echo: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
