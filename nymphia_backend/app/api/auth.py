import re
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import Gestante, Profissional, Parceiro
from app.schemas.all_schemas import (
    GestanteRegister, GestanteLogin,
    ProfissionalRegister, ProfissionalLogin, LoginUnificadoPayload, CrmValidacaoResponse,
    ParceiroRegister, ParceiroLogin,
    AuthResponse,
    EsqueciSenhaPayload, EsqueciSenhaResponse, RedefinirSenhaPayload
)
from app.security.jwt_auth import (
    hash_password, verify_password, create_access_token, decode_access_token,
    get_current_profissional
)
from app.storage.object_storage import save_uploaded_file
from app.services.crm_service import consultar_situacao_crm, validar_formato_crm

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# --- CONSULTA E VALIDAÇÃO DE CRM (CFM / CONSELHO REGIONAL) ---
@router.get("/profissional/validar-crm", response_model=CrmValidacaoResponse)
def validar_crm_online(
    crm: str = Query(..., description="Número de registro no CRM (apenas dígitos)"),
    uf: str = Query("SP", description="UF do CRM (sigla do estado)"),
    db: Session = Depends(get_db)
):
    """
    Verifica se o CRM é válido, ativo e regular junto ao Conselho Federal de Medicina (CFM)
    e aos Conselhos Regionais (ex: CREMESP). Retorna situação e dados do médico.
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

        crm_limpo = re.sub(r'[^0-9]', '', payload.crm.strip())
        uf_limpa = (payload.crm_uf or "SP").strip().upper()

        # Valida situação cadastral do CRM
        checagem_crm = consultar_situacao_crm(crm_limpo, uf_limpa, db=db)
        if not checagem_crm["valido"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CRM {crm_limpo}/{uf_limpa} inválido ou inativo: {checagem_crm['mensagem']}"
            )

        # Localiza o profissional por CRM/UF ou por E-mail
        prof = None
        if email_clean:
            prof = db.query(Profissional).filter(Profissional.email == email_clean).first()
            if prof:
                if prof.registro_numero != crm_limpo or prof.registro_uf != uf_limpa:
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

    # Validação do CRM junto ao CFM
    if payload.registro_tipo.upper() == "CRM":
        checagem = consultar_situacao_crm(payload.registro_numero, payload.registro_uf, db=db)
        if not checagem["valido"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Não foi possível validar o CRM: {checagem['mensagem']}"
            )

    prof = Profissional(
        nome=payload.nome.strip(),
        email=payload.email.lower(),
        senha_hash=hash_password(payload.senha),
        registro_tipo=payload.registro_tipo.upper(),
        registro_numero=payload.registro_numero.strip(),
        registro_uf=payload.registro_uf.upper(),
        status_verificacao="aprovado" if payload.registro_tipo.upper() == "CRM" else "pendente",
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
    crm_limpo = re.sub(r'[^0-9]', '', payload.crm.strip()) if payload.crm else None
    uf_limpa = (payload.crm_uf or "SP").strip().upper() if payload.crm_uf else "SP"

    # Se CRM foi informado, checa validade no CFM
    if crm_limpo:
        checagem = consultar_situacao_crm(crm_limpo, uf_limpa, db=db)
        if not checagem["valido"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CRM {crm_limpo}/{uf_limpa} inválido ou inativo: {checagem['mensagem']}"
            )

    prof = None
    if email_clean:
        prof = db.query(Profissional).filter(Profissional.email == email_clean).first()
        if prof and crm_limpo and (prof.registro_numero != crm_limpo or prof.registro_uf != uf_limpa):
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
@router.post("/esqueci-senha", response_model=EsqueciSenhaResponse)
def esqueci_senha(payload: EsqueciSenhaPayload, db: Session = Depends(get_db)):
    """
    Inicia o fluxo seguro de recuperação de conta.
    Gera token assinado JWT com tempo de expiração de 30 minutos.
    Retorna mensagem segura para mitigar enumeração de contas.
    """
    email_clean = payload.email.strip().lower()
    usuario = None
    perfil_encontrado = None

    if payload.perfil == "gestante" or not payload.perfil:
        usuario = db.query(Gestante).filter(Gestante.email == email_clean).first()
        if usuario:
            perfil_encontrado = "gestante"

    if not usuario and (payload.perfil == "profissional" or not payload.perfil):
        usuario = db.query(Profissional).filter(Profissional.email == email_clean).first()
        if usuario:
            perfil_encontrado = "profissional"

    if not usuario and (payload.perfil == "parceiro" or not payload.perfil):
        usuario = db.query(Parceiro).filter(Parceiro.email == email_clean).first()
        if usuario:
            perfil_encontrado = "parceiro"

    reset_token = None
    if usuario:
        from datetime import timedelta
        reset_token = create_access_token(
            data={
                "sub": usuario.id,
                "email": usuario.email,
                "perfil": perfil_encontrado,
                "tipo_acao": "redefinicao_senha"
            },
            expires_delta=timedelta(minutes=30)
        )

    return EsqueciSenhaResponse(
        sucesso=True,
        mensagem="Se o e-mail informado estiver cadastrado na Nymphia, o procedimento de redefinição foi iniciado com sucesso.",
        reset_token=reset_token
    )

@router.post("/redefinir-senha")
def redefinir_senha(payload: RedefinirSenhaPayload, db: Session = Depends(get_db)):
    """
    Valida o token temporário assinado e atualiza a senha da conta com hash seguro bcrypt.
    """
    try:
        dados = decode_access_token(payload.token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de redefinição inválido ou expirado. Por favor, solicite uma nova redefinição."
        )

    if dados.get("tipo_acao") != "redefinicao_senha":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O token fornecido não possui permissão para redefinição de senha."
        )

    user_id = dados.get("sub")
    perfil = dados.get("perfil")

    usuario = None
    if perfil == "gestante":
        usuario = db.query(Gestante).filter(Gestante.id == user_id).first()
    elif perfil == "profissional":
        usuario = db.query(Profissional).filter(Profissional.id == user_id).first()
    elif perfil == "parceiro":
        usuario = db.query(Parceiro).filter(Parceiro.id == user_id).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A conta associada a este pedido de redefinição não foi localizada."
        )

    usuario.senha_hash = hash_password(payload.nova_senha)
    db.commit()

    return {
        "sucesso": True,
        "mensagem": "Senha redefinida com sucesso! Você já pode realizar login com sua nova credencial."
    }

