"""
Nymphia -- Entrega protegida de arquivos enviados (laudos, fotos de exame,
documentos de registro profissional).

Antes, a pasta storage_uploads era servida sem login nenhum em /storage: quem
tivesse o endereço baixava o laudo. Agora cada arquivo só sai para quem tem
direito, sempre com login (cabeçalho Authorization: Bearer):

  arquivo de exame       a gestante dona do exame; ou profissional APROVADO
                         com vínculo ATIVO com ela (o acesso fica registrado
                         em logs_acesso, como pede a LGPD)
  documento profissional o próprio profissional que enviou
                         (a equipe abre pela rota /admin)

Qualquer outro caso recebe 404, para não confirmar nem que o arquivo existe.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Profissional
from app.models.clinical import Exame
from app.models.relations import Vinculo, LogAcesso
from app.security.jwt_auth import get_current_any_user
from app.storage.object_storage import resolver_arquivo_armazenado

router = APIRouter(tags=["Arquivos protegidos"])

CABECALHOS_PRIVADOS = {
    "Cache-Control": "private, no-store",
    "Content-Disposition": "inline",
}


def _nao_encontrado() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado.")


@router.get("/storage/{nome_arquivo}")
def baixar_arquivo(
    nome_arquivo: str,
    usuario: dict = Depends(get_current_any_user),
    db: Session = Depends(get_db)
):
    caminho = resolver_arquivo_armazenado(nome_arquivo)
    if caminho is None:
        raise _nao_encontrado()

    url = f"/storage/{caminho.name}"
    user_id = usuario.get("sub")
    perfil = usuario.get("perfil")

    exame = db.query(Exame).filter(Exame.arquivo_url == url).first()
    if exame:
        if perfil == "gestante" and exame.gestante_id == user_id:
            return FileResponse(caminho, headers=CABECALHOS_PRIVADOS)

        if perfil == "profissional":
            prof = db.query(Profissional).filter(Profissional.id == user_id).first()
            vinculo_ativo = db.query(Vinculo).filter(
                Vinculo.profissional_id == user_id,
                Vinculo.gestante_id == exame.gestante_id,
                Vinculo.status == "ativo"
            ).first()
            if prof and prof.status_verificacao == "aprovado" and vinculo_ativo:
                db.add(LogAcesso(
                    gestante_id=exame.gestante_id,
                    acessado_por_id=user_id,
                    acessado_por_tipo="profissional",
                    recurso=f"arquivo_exame_{exame.id}"[:100],
                    data_hora=datetime.utcnow()
                ))
                db.commit()
                return FileResponse(caminho, headers=CABECALHOS_PRIVADOS)
        raise _nao_encontrado()

    dono = db.query(Profissional).filter(Profissional.documento_comprovante_path == url).first()
    if dono and perfil == "profissional" and dono.id == user_id:
        return FileResponse(caminho, headers=CABECALHOS_PRIVADOS)

    raise _nao_encontrado()
