# backend/routers/backup.py

from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.backup import make_backup, restore_backup
from tempfile import NamedTemporaryFile
from pathlib import Path
import shutil
import os

router = APIRouter()

# === POST /api/backup/download ===
@router.post("/download", response_class=StreamingResponse)
def download_encrypted_backup(password: str = Form(...), db: Session = Depends(get_db)):
    try:
        with NamedTemporaryFile(delete=False, suffix=".btx") as temp_file:
            temp_path = Path(temp_file.name)
            make_backup(password, temp_path)

        return StreamingResponse(
            open(temp_path, "rb"),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename=bitcoin_backup.btx"
            },
        )
    finally:
        # Cleanup file after response is sent
        if 'temp_path' in locals() and temp_path.exists():
            os.remove(temp_path)

# === POST /api/backup/restore ===
@router.post("/restore")
def restore_encrypted_backup(
    password: str = Form(...),
    file: UploadFile = Form(...),
    db: Session = Depends(get_db),
):
    try:
        with NamedTemporaryFile(delete=False, suffix=".btx") as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = Path(temp_file.name)

        restore_backup(password, temp_path)
        return {"message": "✅ Database successfully restored."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Restore failed: {str(e)}")
    finally:
        if 'temp_path' in locals() and temp_path.exists():
            os.remove(temp_path)
