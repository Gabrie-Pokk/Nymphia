"""
Nymphia -- Envio de e-mail transacional.

Usado hoje só para o link de redefinição de senha. Funciona por SMTP com
STARTTLS, configurado por variáveis de ambiente:

  SMTP_HOST, SMTP_PORT (padrão 587), SMTP_USER, SMTP_PASSWORD, SMTP_FROM

Se o SMTP não estiver configurado, a função devolve False e não envia nada.
Nesse caso o token de redefinição NÃO é exposto em lugar nenhum: a pessoa
recebe a orientação de falar com o suporte.
"""
import os
import ssl
import smtplib
import logging
from email.message import EmailMessage

logger = logging.getLogger("nymphia.email")


def smtp_configurado() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM"))


def enviar_email(destinatario: str, assunto: str, corpo_texto: str) -> bool:
    """Envia um e-mail de texto simples. Devolve True se o servidor aceitou."""
    if not smtp_configurado():
        logger.warning("SMTP não configurado: e-mail para %s não enviado.", destinatario)
        return False

    mensagem = EmailMessage()
    mensagem["Subject"] = assunto
    mensagem["From"] = os.environ["SMTP_FROM"]
    mensagem["To"] = destinatario
    mensagem.set_content(corpo_texto)

    host = os.environ["SMTP_HOST"]
    porta = int(os.getenv("SMTP_PORT", "587"))
    usuario = os.getenv("SMTP_USER")
    senha = os.getenv("SMTP_PASSWORD")

    try:
        contexto = ssl.create_default_context()
        with smtplib.SMTP(host, porta, timeout=15) as servidor:
            servidor.starttls(context=contexto)
            if usuario and senha:
                servidor.login(usuario, senha)
            servidor.send_message(mensagem)
        return True
    except Exception as erro:
        logger.error("Falha ao enviar e-mail para %s: %s", destinatario, erro)
        return False
