import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException, status

STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / "storage_uploads"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def save_uploaded_file(file: UploadFile, prefix: str = "doc") -> str:
    """
    Saves an uploaded file to object storage directory using a secure UUID-based name.
    Never uses the original filename. Never saves inside database.
    """
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de arquivo inválido. Permitidos: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo excede o tamanho máximo permitido de 10MB"
        )

    secure_filename = f"{prefix}_{uuid.uuid4().hex}{ext}"
    dest_path = STORAGE_DIR / secure_filename
    with open(dest_path, "wb") as f:
        f.write(content)

    # Return virtual storage URL
    return f"/storage/{secure_filename}"
