from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante
from app.models.relations import LogAcesso
from app.schemas.all_schemas import LogAcessoOut
from app.security.jwt_auth import get_current_gestante
from app.services.export_service import export_gestante_json, export_gestante_pdf

router = APIRouter(tags=["Conformidade LGPD e Portabilidade"])

@router.get("/meus-dados/exportar")
def exportar_meus_dados(
    formato: str = Query("json", pattern="^(json|pdf)$"),
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Portabilidade de dados pessoais (Art. 18, V da LGPD).
    Permite exportação em JSON estruturado ou PDF diagramado.
    """
    if formato == "pdf":
        pdf_bytes = export_gestante_pdf(gestante.id, db)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=nymphia_prontuario_{gestante.id[:8]}.pdf"}
        )
    else:
        json_data = export_gestante_json(gestante.id, db)
        return json_data

@router.get("/meus-dados/log-acesso", response_model=List[LogAcessoOut])
def listar_log_acesso(
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Transparência ativa (Art. 18 da LGPD):
    A gestante consulta quem acessou os dados dela (profissional ou parceiro) e quando.
    """
    return db.query(LogAcesso).filter(LogAcesso.gestante_id == gestante.id).order_by(LogAcesso.data_hora.desc()).all()

@router.put("/meus-dados/consentimento-ia")
def atualizar_consentimento_ia(
    recusa_ia: bool,
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Resolução CFM 2.454/2026: Direito de informação e de recusa do uso de IA.
    A gestante pode utilizar a plataforma recusando a análise automatizada por IA.
    """
    gestante.recusa_ia = recusa_ia
    db.commit()
    db.refresh(gestante)
    return {
        "status": "atualizado",
        "recusa_ia": gestante.recusa_ia,
        "mensagem": "Preferencia de consentimento de inteligência artificial atualizada com sucesso"
    }

@router.delete("/minha-conta", status_code=status.HTTP_200_OK)
def excluir_minha_conta(
    gestante: Gestante = Depends(get_current_gestante),
    db: Session = Depends(get_db)
):
    """
    Direito de eliminação de dados sensíveis (Art. 18, VI da LGPD).
    Exclui a conta e limpa em cascata todos os dados associados.
    """
    db.delete(gestante)
    db.commit()
    return {"status": "excluida", "mensagem": "Conta e todos os dados associados foram completamente removidos"}
