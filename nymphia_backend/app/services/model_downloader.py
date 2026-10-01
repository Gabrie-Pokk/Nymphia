"""
Nymphia -- Download automático e entrega dos pesos do BERTimbau na nuvem.
Permite que o Render ou qualquer servidor faça download dos pesos treinados
via Google Drive, Dropbox ou URL direta (S3, GitHub Releases) no startup do contêiner.
"""
import os
import re
import shutil
import tarfile
import zipfile
import logging
import urllib.request
from pathlib import Path

logger = logging.getLogger("nymphia.model_downloader")

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
MODELOS_DIR = Path(os.environ.get("NYMPHIA_MODELOS_DIR", str(_BACKEND_DIR / "modelos")))
BERTIMBAU_DIR = MODELOS_DIR / "bertimbau_nymphia" / "modelo_final"


def extrair_google_drive_id(url: str) -> str:
    """Extrai o ID do arquivo de diversos formatos de links de compartilhamento do Google Drive."""
    padroes = [
        r'/file/d/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)',
        r'/d/([a-zA-Z0-9_-]+)'
    ]
    for p in padroes:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return ""


def baixar_google_drive(file_id: str, destino: Path):
    """Baixa arquivos grandes do Google Drive contornando o token de confirmação de vírus."""
    url_base = f"https://drive.google.com/uc?export=download&id={file_id}"
    req = urllib.request.Request(
        url_base,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    
    with urllib.request.urlopen(req, timeout=120) as resp:
        # Verifica se há cookie de confirmação para arquivos grandes (>100MB)
        cookies = resp.headers.get("Set-Cookie", "")
        confirm_token = None
        for c in cookies.split(";"):
            if "download_warning" in c:
                parts = c.split("=")
                if len(parts) > 1:
                    confirm_token = parts[1].strip()
                    break

        if confirm_token:
            url_confirmada = f"{url_base}&confirm={confirm_token}"
            req_confirm = urllib.request.Request(
                url_confirmada,
                headers={"User-Agent": "Mozilla/5.0", "Cookie": cookies}
            )
            with urllib.request.urlopen(req_confirm, timeout=300) as resp_final:
                with open(destino, "wb") as f:
                    shutil.copyfileobj(resp_final, f)
        else:
            with open(destino, "wb") as f:
                shutil.copyfileobj(resp, f)


def descompactar_arquivo(arquivo_zip_ou_tar: Path, destino_dir: Path):
    """Descompacta .zip ou .tar.gz no diretório de destino preservando a estrutura."""
    destino_dir.mkdir(parents=True, exist_ok=True)
    nome = arquivo_zip_ou_tar.name.lower()
    
    if nome.endswith(".zip"):
        with zipfile.ZipFile(arquivo_zip_ou_tar, 'r') as z:
            z.extractall(destino_dir)
    elif nome.endswith((".tar.gz", ".tgz", ".tar")):
        with tarfile.open(arquivo_zip_ou_tar, 'r:*') as t:
            t.extractall(destino_dir)
    else:
        # Se for um único arquivo de pesos (ex: safetensors ou bin direto)
        shutil.copy(arquivo_zip_ou_tar, destino_dir / arquivo_zip_ou_tar.name)

    # Se a descompactação gerou uma subpasta aninhada, ajusta os arquivos para a raiz de modelo_final
    subpastas = [p for p in destino_dir.iterdir() if p.is_dir()]
    if len(subpastas) == 1 and not (destino_dir / "config.json").exists():
        sub = subpastas[0]
        for item in sub.iterdir():
            shutil.move(str(item), str(destino_dir / item.name))
        try:
            sub.rmdir()
        except Exception:
            pass


def bertimbau_instalado() -> bool:
    """Verifica se os arquivos essenciais do BERTimbau estão presentes no disco."""
    if not BERTIMBAU_DIR.exists():
        return False
    
    arquivos = [f.name for f in BERTIMBAU_DIR.glob("*")]
    tem_config = "config.json" in arquivos
    tem_pesos = any(
        f.endswith((".safetensors", ".bin", ".pt", ".onnx"))
        for f in arquivos
    )
    return tem_config and tem_pesos


def garantir_bertimbau_presente():
    """
    Executado no startup: se o modelo não existir localmente, tenta baixar
    a partir da variável de ambiente NYMPHIA_BERTIMBAU_URL.
    """
    if bertimbau_instalado():
        logger.info(f"BERTimbau já presente em {BERTIMBAU_DIR}.")
        return True

    download_url = os.environ.get("NYMPHIA_BERTIMBAU_URL", "").strip()
    if not download_url:
        logger.info(
            "NYMPHIA_BERTIMBAU_URL não configurada. Operando em modo gracioso com regras determinísticas."
        )
        return False

    logger.info(f"Baixando pesos do BERTimbau a partir da URL configurada...")
    temp_download = MODELOS_DIR / "temp_bertimbau_download.bin"
    MODELOS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        drive_id = extrair_google_drive_id(download_url)
        if drive_id:
            logger.info(f"Detectado link Google Drive (ID: {drive_id}). Iniciando download...")
            baixar_google_drive(drive_id, temp_download)
        else:
            logger.info(f"Iniciando download HTTP direto...")
            req = urllib.request.Request(
                download_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=300) as resp, open(temp_download, "wb") as f:
                shutil.copyfileobj(resp, f)

        tamanho_mb = temp_download.stat().st_size / (1024 * 1024)
        logger.info(f"Download concluído: {tamanho_mb:.1f} MB. Descompactando...")
        descompactar_arquivo(temp_download, BERTIMBAU_DIR)

        if bertimbau_instalado():
            logger.info(f"BERTimbau instalado com sucesso em {BERTIMBAU_DIR}!")
            return True
        else:
            logger.warning(
                f"Arquivo descompactado em {BERTIMBAU_DIR}, mas 'config.json' ou pesos não foram localizados."
            )
            return False

    except Exception as e:
        logger.error(f"Erro ao baixar/instalar BERTimbau da nuvem: {e}")
        return False
    finally:
        if temp_download.exists():
            try:
                temp_download.unlink()
            except Exception:
                pass
