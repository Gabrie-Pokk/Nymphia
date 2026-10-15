"""
Nymphia -- Rotas da equipe: conferência e aprovação de profissionais.

Todo profissional entra como "pendente". Ele consegue fazer login, mas não vê,
não convida e não anota nada sobre pacientes até a equipe aprovar.

Como a equipe aprova (passo a passo):
  1. GET  /admin/profissionais                lista quem está pendente
  2. GET  /admin/profissionais/{id}/documento abre o documento enviado
  3. Confere o registro no portal do Conselho
     (CRM: portal.cfm.org.br/busca-medicos; COREN: site do COREN do estado)
  4. POST /admin/profissionais/{id}/aprovar   ou
     POST /admin/profissionais/{id}/rejeitar  (com o motivo)

Toda decisão e toda abertura de documento ficam na tabela auditoria_admin.
Todas as rotas exigem o cabeçalho X-Admin-Token (ver app/security/admin.py).
O script scripts/admin_profissionais.py faz tudo isso pela linha de comando.
"""
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Profissional, AuditoriaAdmin
from app.security.admin import exigir_admin
from app.services.email_service import enviar_email
from app.storage.object_storage import resolver_arquivo_armazenado

router = APIRouter(prefix="/admin", tags=["Equipe Nymphia"])


class DecisaoRejeicao(BaseModel):
    motivo: str = Field(..., min_length=5, max_length=500)


def _onde_conferir(prof: Profissional) -> str:
    if prof.registro_tipo == "CRM":
        return "portal.cfm.org.br/busca-medicos"
    return f"site do COREN-{prof.registro_uf}"


def _resumo(prof: Profissional) -> dict:
    return {
        "id": prof.id,
        "nome": prof.nome,
        "email": prof.email,
        "registro": f"{prof.registro_tipo} {prof.registro_numero}/{prof.registro_uf}",
        "status_verificacao": prof.status_verificacao,
        "criado_em": prof.criado_em.isoformat() if prof.criado_em else None,
        "enviou_documento": bool(prof.documento_comprovante_path),
        "onde_conferir": _onde_conferir(prof),
    }


def _buscar(db: Session, profissional_id: str) -> Profissional:
    prof = db.query(Profissional).filter(Profissional.id == profissional_id).first()
    if not prof:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profissional não encontrado.")
    return prof


@router.get("/profissionais")
def listar_profissionais(
    situacao: str = Query("pendente", pattern="^(pendente|aprovado|rejeitado|todos)$"),
    quem: str = Depends(exigir_admin),
    db: Session = Depends(get_db)
):
    consulta = db.query(Profissional)
    if situacao != "todos":
        consulta = consulta.filter(Profissional.status_verificacao == situacao)
    return [_resumo(p) for p in consulta.order_by(Profissional.criado_em.asc()).all()]


@router.get("/profissionais/{profissional_id}/documento")
def abrir_documento(
    profissional_id: str,
    quem: str = Depends(exigir_admin),
    db: Session = Depends(get_db)
):
    prof = _buscar(db, profissional_id)
    caminho = resolver_arquivo_armazenado(prof.documento_comprovante_path or "")
    if caminho is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Este profissional ainda não enviou documento.")
    db.add(AuditoriaAdmin(acao="abrir_documento", alvo_id=prof.id, feito_por=quem, criado_em=datetime.utcnow()))
    db.commit()
    return FileResponse(caminho, headers={"Cache-Control": "private, no-store"})


@router.post("/profissionais/{profissional_id}/aprovar")
def aprovar_profissional(
    profissional_id: str,
    tarefas: BackgroundTasks,
    quem: str = Depends(exigir_admin),
    db: Session = Depends(get_db)
):
    prof = _buscar(db, profissional_id)
    prof.status_verificacao = "aprovado"
    db.add(AuditoriaAdmin(
        acao="aprovar_profissional",
        alvo_id=prof.id,
        feito_por=quem,
        detalhe=f"{prof.registro_tipo} {prof.registro_numero}/{prof.registro_uf}",
        criado_em=datetime.utcnow()
    ))
    db.commit()
    tarefas.add_task(
        enviar_email,
        prof.email,
        "Nymphia: seu registro foi aprovado",
        f"Olá, {prof.nome}.\n\nA equipe Nymphia conferiu seu registro "
        f"{prof.registro_tipo} {prof.registro_numero}/{prof.registro_uf}. "
        "O acesso ao painel de pacientes já está liberado.\n\nEquipe Nymphia"
    )
    return _resumo(prof)


@router.post("/profissionais/{profissional_id}/rejeitar")
def rejeitar_profissional(
    profissional_id: str,
    decisao: DecisaoRejeicao,
    tarefas: BackgroundTasks,
    quem: str = Depends(exigir_admin),
    db: Session = Depends(get_db)
):
    prof = _buscar(db, profissional_id)
    prof.status_verificacao = "rejeitado"
    db.add(AuditoriaAdmin(
        acao="rejeitar_profissional",
        alvo_id=prof.id,
        feito_por=quem,
        detalhe=decisao.motivo.strip(),
        criado_em=datetime.utcnow()
    ))
    db.commit()
    tarefas.add_task(
        enviar_email,
        prof.email,
        "Nymphia: não foi possível confirmar seu registro",
        f"Olá, {prof.nome}.\n\nNão conseguimos confirmar o registro "
        f"{prof.registro_tipo} {prof.registro_numero}/{prof.registro_uf}.\n"
        f"Motivo: {decisao.motivo.strip()}\n\n"
        "Se houver engano, responda este e-mail com o documento do Conselho.\n\nEquipe Nymphia"
    )
    return _resumo(prof)
