import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante, Profissional, Parceiro, TokenRedefinicaoSenha
from app.services.email_service import enviar_email
from app.schemas.all_schemas import (
    GestanteRegister, GestanteLogin,
    ProfissionalRegister, ProfissionalLogin, LoginUnificadoPayload, CrmValidacaoResponse,
    ParceiroRegister, ParceiroLogin,
    AuthResponse,
    EsqueciSenhaPayload, EsqueciSenhaResponse, RedefinirSenhaPayload
)
from app.security.jwt_auth import (
    hash_password, verify_password, create_access_token,
    get_current_profissional
)
from app.storage.object_storage import save_uploaded_file
from app.services.crm_service import consultar_situacao_crm, normalizar_registro

VALIDADE_TOKEN_REDEFINICAO = timedelta(minutes=30)
MENSAGEM_ESQUECI_SENHA = (
    "Se o e-mail estiver cadastrado, enviamos um link para redefinir a senha. "
    "Se ele não chegar em alguns minutos, fale com o suporte da Nymphia."
)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _url_publica() -> str:
    # Vence NYMPHIA_URL_PUBLICA. Sem ela: no Render, RENDER_EXTERNAL_URL; no
    # Coolify, o primeiro endereço de COOLIFY_URL (ele cria essa variável).
    coolify = (os.getenv("COOLIFY_URL") or "").split(",")[0].strip()
    if coolify and not coolify.startswith(("http://", "https://")):
        coolify = "https://" + coolify
    return (
        os.getenv("NYMPHIA_URL_PUBLICA")
        or os.getenv("RENDER_EXTERNAL_URL")
        or coolify
        or "https://nymphia-global.onrender.com"
    ).rstrip("/")

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# --- CONSULTA E VALIDAÇÃO DE CRM (CFM / CONSELHO REGIONAL) ---
@router.get("/profissional/validar-crm", response_model=CrmValidacaoResponse)
def validar_crm_online(
    crm: str = Query(..., description="Número de registro no CRM (apenas dígitos)"),
    uf: str = Query("SP", description="UF do CRM (sigla do estado)"),
    db: Session = Depends(get_db)
):
    """
    Confere o formato do CRM e, para SP, consulta o CREMESP. Não aprova ninguém:
    a aprovação do profissional é sempre manual. Ver app/services/crm_service.py.
    """
    resultado = consultar_situacao_crm(crm=crm, uf=uf, db=db)
    return CrmValidacaoResponse(**resultado)


# --- GESTANTE ---
@router.post("/gestante/cadastro", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_gestante(payload: GestanteRegister, db: Session = Depends(get_db)):
    existente = db.query(Gestante).filter(Gestante.email == payload.email.lower()).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado no sistema")

    agora = datetime.utcnow()
    gestante = Gestante(
        nome=payload.nome.strip(),
        email=payload.email.lower(),
        senha_hash=hash_password(payload.senha),
        recusa_ia=payload.recusa_ia,
        termos_aceitos_em=agora,
        termos_versao=payload.termos_versao or "1.0-2026",
        consentimento_dados_saude=payload.consentimento_dados_saude,
        consentimento_dados_saude_em=agora
    )
    db.add(gestante)
    db.commit()
    db.refresh(gestante)

    token = create_access_token(data={"sub": gestante.id, "perfil": "gestante"})
    return AuthResponse(
        token=token,
        perfil="gestante",
        id=gestante.id,
        nome=gestante.nome,
        recusa_ia=gestante.recusa_ia,
        termos_versao=gestante.termos_versao
    )

@router.post("/gestante/login", response_model=AuthResponse)
def login_gestante(payload: GestanteLogin, db: Session = Depends(get_db)):
    gestante = db.query(Gestante).filter(Gestante.email == payload.email.lower()).first()
    if not gestante or not verify_password(payload.senha, gestante.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha incorretos")

    token = create_access_token(data={"sub": gestante.id, "perfil": "gestante"})
    return AuthResponse(
        token=token,
        perfil="gestante",
        id=gestante.id,
        nome=gestante.nome,
        recusa_ia=gestante.recusa_ia
    )

# --- LOGIN UNIFICADO INTELIGENTE (COM SUPORTE A CRM PARA MÉDICOS) ---
@router.post("/login", response_model=AuthResponse)
def login_unificado(payload: LoginUnificadoPayload, db: Session = Depends(get_db)):
    email_clean = payload.email.strip().lower() if payload.email else ""
    perfil_req = (payload.perfil or "").lower()

    # 1. Fluxo específico quando o usuário solicita acesso como Profissional ou fornece CRM
    if perfil_req == "profissional" or payload.crm:
        if not payload.crm:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Por favor, informe o número e UF do seu CRM para acessar o painel médico."
            )

        crm_limpo = normalizar_registro(payload.crm)
        uf_limpa = (payload.crm_uf or "SP").strip().upper()

        # Só bloqueia o que dá para afirmar: formato impossível ou registro
        # inativo segundo o próprio CREMESP. Nunca aprova ninguém.
        checagem_crm = consultar_situacao_crm(crm_limpo, uf_limpa, db=db)
        if not checagem_crm["valido"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CRM {crm_limpo}/{uf_limpa}: {checagem_crm['mensagem']}"
            )

        # Localiza o profissional por CRM/UF ou por E-mail
        prof = None
        if email_clean:
            prof = db.query(Profissional).filter(Profissional.email == email_clean).first()
            if prof:
                if normalizar_registro(prof.registro_numero) != crm_limpo or prof.registro_uf != uf_limpa:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"O CRM {crm_limpo}/{uf_limpa} informado não confere com o cadastro deste e-mail."
                    )
        
        if not prof:
            prof = db.query(Profissional).filter(
                Profissional.registro_numero == crm_limpo,
                Profissional.registro_uf == uf_limpa
            ).first()

        if not prof or not verify_password(payload.senha, prof.senha_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas: CRM, UF, e-mail ou senha incorretos."
            )

        if prof.status_verificacao == "rejeitado":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cadastro profissional rejeitado ou suspenso pela moderação ética do CRM."
            )

        token = create_access_token(data={"sub": prof.id, "perfil": "profissional"})
        return AuthResponse(
            token=token,
            perfil="profissional",
            id=prof.id,
            nome=prof.nome,
            status_verificacao=prof.status_verificacao
        )

    # 2. Tenta como Gestante (se não for profissional explícito)
    if email_clean:
        gestante = db.query(Gestante).filter(Gestante.email == email_clean).first()
        if gestante and verify_password(payload.senha, gestante.senha_hash):
            token = create_access_token(data={"sub": gestante.id, "perfil": "gestante"})
            return AuthResponse(
                token=token,
                perfil="gestante",
                id=gestante.id,
                nome=gestante.nome,
                recusa_ia=gestante.recusa_ia
            )

        # 3. Tenta como Parceiro
        parceiro = db.query(Parceiro).filter(Parceiro.email == email_clean).first()
        if parceiro and verify_password(payload.senha, parceiro.senha_hash):
            token = create_access_token(data={"sub": parceiro.id, "perfil": "parceiro"})
            return AuthResponse(
                token=token,
                perfil="parceiro",
                id=parceiro.id,
                nome=parceiro.nome
            )

        # 4. Tenta como Profissional genérico (fallback se omitiu campo de CRM mas email é de médico)
        prof = db.query(Profissional).filter(Profissional.email == email_clean).first()
        if prof and verify_password(payload.senha, prof.senha_hash):
            if prof.status_verificacao == "rejeitado":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cadastro profissional rejeitado pela moderação médica"
                )
            token = create_access_token(data={"sub": prof.id, "perfil": "profissional"})
            return AuthResponse(
                token=token,
                perfil="profissional",
                id=prof.id,
                nome=prof.nome,
                status_verificacao=prof.status_verificacao
            )

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha incorretos")


# --- PROFISSIONAL ESPECÍFICO ---
@router.post("/profissional/cadastro", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_profissional(payload: ProfissionalRegister, db: Session = Depends(get_db)):
    existente = db.query(Profissional).filter(Profissional.email == payload.email.lower()).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado no sistema")

    tipo = payload.registro_tipo.upper()
    numero = normalizar_registro(payload.registro_numero)
    uf = payload.registro_uf.strip().upper()

    # Um registro só pode ter uma conta
    duplicado = db.query(Profissional).filter(
        Profissional.registro_tipo == tipo,
        Profissional.registro_numero == numero,
        Profissional.registro_uf == uf
    ).first()
    if duplicado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este registro profissional já tem conta na Nymphia. Se for o seu, entre com ele ou fale com o suporte."
        )

    checagem = consultar_situacao_crm(numero, uf, db=db, registro_tipo=tipo)
    if not checagem["valido"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Não foi possível aceitar o registro: {checagem['mensagem']}"
        )

    prof = Profissional(
        nome=payload.nome.strip(),
        email=payload.email.lower(),
        senha_hash=hash_password(payload.senha),
        registro_tipo=tipo,
        registro_numero=numero,
        registro_uf=uf,
        # Toda aprovação é manual, feita pela equipe depois de conferir o documento
        status_verificacao="pendente",
        termos_aceitos_em=datetime.utcnow(),
        termos_versao=payload.termos_versao or "1.0-2026"
    )
    db.add(prof)
    db.commit()
    db.refresh(prof)

    token = create_access_token(data={"sub": prof.id, "perfil": "profissional"})
    return AuthResponse(
        token=token,
        perfil="profissional",
        id=prof.id,
        nome=prof.nome,
        status_verificacao=prof.status_verificacao,
        termos_versao=prof.termos_versao
    )

@router.post("/profissional/login", response_model=AuthResponse)
def login_profissional(payload: ProfissionalLogin, db: Session = Depends(get_db)):
    email_clean = payload.email.strip().lower() if payload.email else ""
    crm_limpo = normalizar_registro(payload.crm) if payload.crm else None
    uf_limpa = (payload.crm_uf or "SP").strip().upper() if payload.crm_uf else "SP"

    # Só bloqueia formato impossível ou registro inativo segundo o CREMESP
    if crm_limpo:
        checagem = consultar_situacao_crm(crm_limpo, uf_limpa, db=db)
        if not checagem["valido"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CRM {crm_limpo}/{uf_limpa}: {checagem['mensagem']}"
            )

    prof = None
    if email_clean:
        prof = db.query(Profissional).filter(Profissional.email == email_clean).first()
        if prof and crm_limpo and (normalizar_registro(prof.registro_numero) != crm_limpo or prof.registro_uf != uf_limpa):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="O CRM informado não coincide com os dados cadastrais deste e-mail."
            )
    elif crm_limpo:
        prof = db.query(Profissional).filter(
            Profissional.registro_numero == crm_limpo,
            Profissional.registro_uf == uf_limpa
        ).first()

    if not prof or not verify_password(payload.senha, prof.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="CRM, e-mail ou senha incorretos")

    if prof.status_verificacao == "rejeitado":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cadastro profissional rejeitado ou suspenso pelo Conselho Regional de Medicina."
        )

    token = create_access_token(data={"sub": prof.id, "perfil": "profissional"})
    return AuthResponse(
        token=token,
        perfil="profissional",
        id=prof.id,
        nome=prof.nome,
        status_verificacao=prof.status_verificacao
    )

@router.post("/profissional/upload-documento")
async def upload_documento_profissional(
    arquivo: UploadFile = File(...),
    prof: Profissional = Depends(get_current_profissional),
    db: Session = Depends(get_db)
):
    saved_url = await save_uploaded_file(arquivo, prefix=f"prof_{prof.id}")
    prof.documento_comprovante_path = saved_url
    db.commit()
    return {"status": "documento_recebido", "caminho": saved_url}

# --- PARCEIRO ---
@router.post("/parceiro/cadastro", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_parceiro(payload: ParceiroRegister, db: Session = Depends(get_db)):
    existente = db.query(Parceiro).filter(Parceiro.email == payload.email.lower()).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado no sistema")

    parceiro = Parceiro(
        nome=payload.nome.strip(),
        email=payload.email.lower(),
        senha_hash=hash_password(payload.senha),
        termos_aceitos_em=datetime.utcnow(),
        termos_versao=payload.termos_versao or "1.0-2026"
    )
    db.add(parceiro)
    db.commit()
    db.refresh(parceiro)

    token = create_access_token(data={"sub": parceiro.id, "perfil": "parceiro"})
    return AuthResponse(
        token=token,
        perfil="parceiro",
        id=parceiro.id,
        nome=parceiro.nome,
        termos_versao=parceiro.termos_versao
    )

@router.post("/parceiro/login", response_model=AuthResponse)
def login_parceiro(payload: ParceiroLogin, db: Session = Depends(get_db)):
    parceiro = db.query(Parceiro).filter(Parceiro.email == payload.email.lower()).first()
    if not parceiro or not verify_password(payload.senha, parceiro.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha incorretos")

    token = create_access_token(data={"sub": parceiro.id, "perfil": "parceiro"})
    return AuthResponse(
        token=token,
        perfil="parceiro",
        id=parceiro.id,
        nome=parceiro.nome
    )


# --- RECUPERAÇÃO E REDEFINIÇÃO DE SENHA ---
#
# Como funciona agora:
# 1. /auth/esqueci-senha gera um código aleatório de 256 bits, guarda no banco
#    só o hash SHA-256 dele, e manda o link por e-mail. A resposta da API é
#    sempre a mesma mensagem, exista a conta ou não, e NUNCA contém o código.
# 2. /auth/redefinir-senha recebe o código, confere o hash, a validade (30 min)
#    e se ainda não foi usado. Cada código vale uma única vez.
# O código não é um JWT, então não serve como sessão em nenhuma rota.

_MODELOS_POR_PERFIL = {"gestante": Gestante, "profissional": Profissional, "parceiro": Parceiro}
MENSAGEM_LINK_INVALIDO = "Link de redefinição inválido, expirado ou já usado. Peça um novo link."


def _localizar_conta(db: Session, email: str, perfil: Optional[str]):
    ordem = [perfil] if perfil else ["gestante", "profissional", "parceiro"]
    for nome_perfil in ordem:
        modelo = _MODELOS_POR_PERFIL[nome_perfil]
        conta = db.query(modelo).filter(modelo.email == email).first()
        if conta:
            return conta, nome_perfil
    return None, None


def _invalidar_tokens_abertos(db: Session, usuario_id: str, perfil: str, agora: datetime) -> None:
    db.query(TokenRedefinicaoSenha).filter(
        TokenRedefinicaoSenha.usuario_id == usuario_id,
        TokenRedefinicaoSenha.perfil == perfil,
        TokenRedefinicaoSenha.usado_em.is_(None)
    ).update({TokenRedefinicaoSenha.usado_em: agora}, synchronize_session=False)


def _enviar_link_redefinicao(destinatario: str, nome: str, token: str) -> None:
    link = f"{_url_publica()}/?redefinir={token}"
    corpo = (
        f"Olá, {nome}.\n\n"
        "Recebemos um pedido para redefinir a senha da sua conta na Nymphia.\n"
        f"Para criar uma senha nova, abra este link em até 30 minutos:\n\n{link}\n\n"
        "O link funciona uma única vez. Se você não fez esse pedido, ignore este e-mail: "
        "sua senha atual continua valendo.\n\n"
        "Equipe Nymphia"
    )
    enviar_email(destinatario, "Nymphia: redefinição de senha", corpo)


@router.post("/esqueci-senha", response_model=EsqueciSenhaResponse)
def esqueci_senha(
    payload: EsqueciSenhaPayload,
    tarefas: BackgroundTasks,
    db: Session = Depends(get_db)
):
    email_clean = payload.email.strip().lower()
    conta, perfil = _localizar_conta(db, email_clean, payload.perfil or None)

    if conta:
        agora = datetime.utcnow()
        _invalidar_tokens_abertos(db, conta.id, perfil, agora)
        token = secrets.token_urlsafe(32)
        db.add(TokenRedefinicaoSenha(
            usuario_id=conta.id,
            perfil=perfil,
            token_hash=_hash_token(token),
            criado_em=agora,
            expira_em=agora + VALIDADE_TOKEN_REDEFINICAO
        ))
        db.commit()
        # O envio roda depois da resposta, para o tempo de resposta não
        # denunciar se o e-mail existe ou não.
        tarefas.add_task(_enviar_link_redefinicao, conta.email, conta.nome, token)

    return EsqueciSenhaResponse(sucesso=True, mensagem=MENSAGEM_ESQUECI_SENHA)


@router.post("/redefinir-senha")
def redefinir_senha(payload: RedefinirSenhaPayload, db: Session = Depends(get_db)):
    agora = datetime.utcnow()
    registro = db.query(TokenRedefinicaoSenha).filter(
        TokenRedefinicaoSenha.token_hash == _hash_token(payload.token.strip())
    ).first()

    if not registro or registro.usado_em is not None or registro.expira_em <= agora:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=MENSAGEM_LINK_INVALIDO)

    modelo = _MODELOS_POR_PERFIL.get(registro.perfil)
    conta = db.query(modelo).filter(modelo.id == registro.usuario_id).first() if modelo else None
    if not conta:
        registro.usado_em = agora
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=MENSAGEM_LINK_INVALIDO)

    conta.senha_hash = hash_password(payload.nova_senha)
    # Derruba todas as sessões abertas antes da troca (inclusive a de quem
    # eventualmente tenha roubado um token)
    conta.sessoes_validas_desde = agora
    registro.usado_em = agora
    _invalidar_tokens_abertos(db, conta.id, registro.perfil, agora)
    db.commit()

    return {
        "sucesso": True,
        "mensagem": "Senha redefinida. Você já pode entrar com a senha nova."
    }

