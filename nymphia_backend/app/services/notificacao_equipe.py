"""
Aviso por e-mail para os profissionais com vínculo ativo com a gestante.

O e-mail não leva nome nem dado de saúde (e-mail não é canal seguro para
isso): só diz que há um alerta novo e pede para abrir o painel, onde o acesso
fica registrado no log da LGPD.

Só conta como "avisado" quando o servidor de e-mail aceitou a mensagem. Sem
SMTP configurado nada é enviado e a resposta diz isso, em vez de fingir.
"""
import logging
from typing import List

from sqlalchemy.orm import Session

from app.models.auth import Profissional
from app.models.relations import Vinculo
from app.services.email_service import enviar_email

logger = logging.getLogger("nymphia.notificacao")

ASSUNTO = "Nymphia: alerta novo de uma paciente"
CORPO = (
    "Olá,\n\n"
    "Uma gestante vinculada a você registrou um alerta no Nymphia ({motivo}).\n"
    "Abra o painel do profissional para ver os detalhes.\n\n"
    "Este e-mail não traz dados da paciente de propósito.\n"
)


def emails_da_equipe(db: Session, gestante_id: str) -> List[str]:
    vinculos = db.query(Vinculo).filter(Vinculo.gestante_id == gestante_id, Vinculo.status == "ativo").all()
    ids = [v.profissional_id for v in vinculos]
    if not ids:
        return []
    profissionais = db.query(Profissional).filter(Profissional.id.in_(ids)).all()
    return [p.email for p in profissionais if p.email]


def tem_equipe_vinculada(db: Session, gestante_id: str) -> bool:
    return db.query(Vinculo).filter(Vinculo.gestante_id == gestante_id, Vinculo.status == "ativo").first() is not None


def avisar_equipe(emails: List[str], motivo: str) -> bool:
    """Envia o aviso para cada e-mail. True se pelo menos um foi aceito pelo servidor."""
    algum = False
    for email in emails:
        try:
            algum = enviar_email(email, ASSUNTO, CORPO.format(motivo=motivo)) or algum
        except Exception as erro:  # nunca derruba quem chamou
            logger.error("Falha ao avisar a equipe: %s", erro)
    return algum
