import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException, status

STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / "storage_uploads"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

MAGIC_BYTES_SIGNATURES = {
    ".pdf": [b"%PDF"],
    ".png": [b"\x89PNG\r\n\x1a\n", b"\x89PNG"],
    ".jpg": [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
}

def validar_assinatura_binaria(content: bytes, ext: str) -> bool:
    """Verifica se o cabeçalho binário (magic bytes) corresponde à extensão declarada."""
    ext_lower = ext.lower()
    signatures = MAGIC_BYTES_SIGNATURES.get(ext_lower)
    if not signatures:
        return False
    return any(content.startswith(sig) for sig in signatures)

async def save_uploaded_file(file: UploadFile, prefix: str = "doc") -> str:
    """
    Saves an uploaded file to object storage directory using a secure UUID-based name.
    Never uses the original filename. Never saves inside database.
    Validates file extension, length and true binary magic bytes (MIME sniffing defense).
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

    if not validar_assinatura_binaria(content, ext):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assinatura binária do arquivo (magic bytes) incompatível com a extensão declarada. Envio bloqueado por segurança."
        )

    secure_filename = f"{prefix}_{uuid.uuid4().hex}{ext}"
    dest_path = STORAGE_DIR / secure_filename
    with open(dest_path, "wb") as f:
        f.write(content)

    # Return virtual storage URL
    return f"/storage/{secure_filename}"
