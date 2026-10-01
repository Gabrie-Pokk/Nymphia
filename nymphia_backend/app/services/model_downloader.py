"""
Nymphia -- Download automático e entrega dos pesos do BERTimbau na nuvem.
Permite que o Render ou qualquer servidor faça download dos pesos treinados
via Google Drive, Dropbox ou URL direta (S3, GitHub Releases) no startup do contêiner.
"""
import os
import re
import ssl
import shutil
import logging
import urllib.request
from pathlib import Path

logger = logging.getLogger("nymphia.model_downloader")

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
MODELOS_DIR = Path(os.environ.get("NYMPHIA_MODELOS_DIR", str(_BACKEND_DIR / "modelos")))
BERTIMBAU_DIR = MODELOS_DIR / "bertimbau_nymphia" / "modelo_final"

# Arquivos do modelo BERTimbau ajustado na taxonomia de 6 categorias clínicas (Nymphia)
DEFAULT_BERTIMBAU_FILES = {
    "config.json": "1PnS0dHMrzJqwrYypuNgpOCbCQb8Mom4c",
    "tokenizer_config.json": "1xC8hHBH0fss7EvEXcQ4C_-4b3S1DG4X7",
    "tokenizer.json": "1qn7SSYIYIWzUktvSqWmVrDJJLqDuWUVf",
    "model.safetensors": "1KE4XynMZTGGWIgJyT00MJjF6RegiEnFf",
}


def _get_ssl_context():
    """Gera contexto SSL tolerante a certificados intermediários."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def baixar_arquivo_google_drive(file_id: str, destino: Path):
    """
    Baixa arquivos do Google Drive suportando arquivos grandes com
    página de confirmação de vírus (download_warning / download anyway).
    """
    ctx = _get_ssl_context()
    url_base = f"https://drive.google.com/uc?export=download&id={file_id}"
    req = urllib.request.Request(
        url_base,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )

    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        content_type = resp.headers.get("Content-Type", "")
        # Se veio como octet-stream ou json direto
        if "text/html" not in content_type:
            with open(destino, "wb") as f:
                shutil.copyfileobj(resp, f)
            return

        # Veio página HTML de confirmação de tamanho grande
        html = resp.read().decode("utf-8", errors="ignore")

    # Extrai o token de confirmação ou uuid do formulário
    uuid_match = re.search(r'name="uuid"\s+value="([^"]+)"', html)
    uuid_val = uuid_match.group(1) if uuid_match else ""

    confirm_match = re.search(r'name="confirm"\s+value="([^"]+)"', html)
    confirm_val = confirm_match.group(1) if confirm_match else "t"

    url_download = (
        f"https://drive.usercontent.google.com/download?id={file_id}"
        f"&export=download&confirm={confirm_val}&uuid={uuid_val}"
    )

    req2 = urllib.request.Request(
        url_download,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )

    with urllib.request.urlopen(req2, context=ctx, timeout=300) as resp2:
        total_esperado = int(resp2.headers.get("Content-Length", 0))
        with open(destino, "wb") as f:
            while True:
                chunk = resp2.read(4 * 1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)

    if total_esperado > 0 and destino.stat().st_size != total_esperado:
        raise IOError(
            f"Tamanho inconsistente para {destino.name}: baixou {destino.stat().st_size} de {total_esperado} bytes esperados."
        )


def bertimbau_instalado() -> bool:
    """Verifica se os arquivos essenciais do BERTimbau estão presentes no disco."""
    if not BERTIMBAU_DIR.exists():
        return False

    tem_config = (BERTIMBAU_DIR / "config.json").exists()
    tem_pesos = (BERTIMBAU_DIR / "model.safetensors").exists() or (BERTIMBAU_DIR / "pytorch_model.bin").exists()
    return tem_config and tem_pesos


def garantir_bertimbau_presente() -> bool:
    """
    Garante a presença dos pesos do BERTimbau no diretório do modelo.
    Se não existirem, faz o download automático dos arquivos individuais
    a partir do repositório Google Drive configurado.
    """
    if bertimbau_instalado():
        logger.info(f"BERTimbau já presente em {BERTIMBAU_DIR}.")
        return True

    BERTIMBAU_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Pesos do BERTimbau não localizados localmente. Iniciando download do Drive...")

    sucesso_total = True
    for nome_arquivo, file_id in DEFAULT_BERTIMBAU_FILES.items():
        destino = BERTIMBAU_DIR / nome_arquivo
        if destino.exists() and destino.stat().st_size > 0:
            continue

        logger.info(f"Baixando {nome_arquivo} (ID: {file_id})...")
        try:
            baixar_arquivo_google_drive(file_id, destino)
            tamanho_mb = destino.stat().st_size / (1024 * 1024)
            logger.info(f"{nome_arquivo} baixado com sucesso ({tamanho_mb:.1f} MB).")
        except Exception as e:
            logger.error(f"Falha ao baixar {nome_arquivo}: {e}")
            if destino.exists():
                destino.unlink()
            sucesso_total = False

    return bertimbau_instalado()
