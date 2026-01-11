# backend/routers/backup.py

from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException, BackgroundTasks
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
def download_encrypted_backup(
    background_tasks: BackgroundTasks,
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Download an encrypted backup of the database.
    Uses BackgroundTasks to clean up temp file after streaming completes.
    """
    with NamedTemporaryFile(delete=False, suffix=".btx") as temp_file:
        temp_path = Path(temp_file.name)
        make_backup(password, temp_path)

    def cleanup():
        if temp_path.exists():
            os.remove(temp_path)

    background_tasks.add_task(cleanup)

    return StreamingResponse(
        open(temp_path, "rb"),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": "attachment; filename=bitcoin_backup.btx"
        },
    )

# === POST /api/backup/restore ===
@router.post("/restore")
def restore_encrypted_backup(
    password: str = Form(...),
    file: UploadFile = Form(...),
    db: Session = Depends(get_db),
):
    """
    Restore the database from an encrypted backup file.
    """
    temp_path = None
    try:
        with NamedTemporaryFile(delete=False, suffix=".btx") as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = Path(temp_file.name)

        restore_backup(password, temp_path)
        return {"message": "✅ Database successfully restored."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Restore failed: {str(e)}")
    finally:
        if temp_path and temp_path.exists():
            os.remove(temp_path)
