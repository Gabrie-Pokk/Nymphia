"""
Nymphia -- Rotas de perfis de acesso e vínculo

Princípio central, refletido no código abaixo, não só em comentário:
o profissional NUNCA grava um vínculo com status "ativo". Ele só gera
um código. É a gestante, usando o código, quem ativa -- o INSERT do
vínculo ativo só acontece dentro do endpoint que a gestante chama.
"""
import os
import random
import string

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth import criar_token, exigir_gestante, exigir_profissional, hash_senha, verificar_senha
from app.db import get_db
from app.models_perfis import CodigoConvite, Gestante, Profissional, Vinculo
from app.schemas import (
    ConviteGerado, ConviteUsar, GestanteCadastro, GestanteLogin, GestanteVinculada,
    ProfissionalCadastro, ProfissionalLogin, TokenResposta, VinculoInfo,
)

router = APIRouter()


def _gerar_codigo(tamanho=8) -> str:
    alfabeto = string.ascii_uppercase + string.digits
    return "".join(random.choices(alfabeto, k=tamanho))


# ============================================================
# Cadastro e login -- Gestante
# ============================================================
@router.post("/auth/gestante/cadastro", response_model=TokenResposta)
def gestante_cadastro(dados: GestanteCadastro, db: Session = Depends(get_db)):
    if db.query(Gestante).filter(Gestante.email == dados.email).first():
        raise HTTPException(status_code=409, detail="Já existe uma conta com este e-mail.")
    gestante = Gestante(nome=dados.nome, email=dados.email, senha_hash=hash_senha(dados.senha))
    db.add(gestante)
    db.commit()
    db.refresh(gestante)
    return TokenResposta(
        token=criar_token(gestante.id, "gestante"), perfil="gestante",
        id=gestante.id, nome=gestante.nome,
    )


@router.post("/auth/gestante/login", response_model=TokenResposta)
def gestante_login(dados: GestanteLogin, db: Session = Depends(get_db)):
    gestante = db.query(Gestante).filter(Gestante.email == dados.email).first()
    if not gestante or not verificar_senha(dados.senha, gestante.senha_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
    return TokenResposta(
        token=criar_token(gestante.id, "gestante"), perfil="gestante",
        id=gestante.id, nome=gestante.nome,
    )


# ============================================================
# Cadastro e login -- Profissional
# ============================================================
@router.post("/auth/profissional/cadastro", response_model=TokenResposta)
def profissional_cadastro(dados: ProfissionalCadastro, db: Session = Depends(get_db)):
    if db.query(Profissional).filter(Profissional.email == dados.email).first():
        raise HTTPException(status_code=409, detail="Já existe uma conta com este e-mail.")
    profissional = Profissional(
        nome=dados.nome, email=dados.email, senha_hash=hash_senha(dados.senha),
        registro_tipo=dados.registro_tipo.upper(), registro_numero=dados.registro_numero,
        registro_uf=dados.registro_uf.upper(), status_verificacao="pendente",
    )
    db.add(profissional)
    db.commit()
    db.refresh(profissional)
    # Acesso liberado imediatamente (provisório) -- é o modelo já decidido:
    # upload de documento + conferência manual posterior, sem bloquear o
    # profissional enquanto isso.
    return TokenResposta(
        token=criar_token(profissional.id, "profissional"), perfil="profissional",
        id=profissional.id, nome=profissional.nome, status_verificacao=profissional.status_verificacao,
    )


@router.post("/auth/profissional/login", response_model=TokenResposta)
def profissional_login(dados: ProfissionalLogin, db: Session = Depends(get_db)):
    profissional = db.query(Profissional).filter(Profissional.email == dados.email).first()
    if not profissional or not verificar_senha(dados.senha, profissional.senha_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
    if profissional.status_verificacao == "rejeitado":
        raise HTTPException(
            status_code=403,
            detail="Cadastro profissional não aprovado na conferência de registro. Entre em contato com o suporte.",
        )
    return TokenResposta(
        token=criar_token(profissional.id, "profissional"), perfil="profissional",
        id=profissional.id, nome=profissional.nome, status_verificacao=profissional.status_verificacao,
    )


# ============================================================
# Vínculo -- caminho do código de convite
# ============================================================
@router.post("/vinculo/convite/gerar", response_model=ConviteGerado)
def gerar_convite(profissional_id: str = Depends(exigir_profissional), db: Session = Depends(get_db)):
    """Só o profissional gera o código. Gerar um código NÃO cria vínculo
    nenhum -- só a gestante, ao usá-lo, ativa a ligação."""
    codigo = _gerar_codigo()
    while db.query(CodigoConvite).filter(CodigoConvite.codigo == codigo).first():
        codigo = _gerar_codigo()  # evita colisão, ainda que improvável
    convite = CodigoConvite(codigo=codigo, profissional_id=profissional_id)
    db.add(convite)
    db.commit()
    return ConviteGerado(codigo=codigo)


@router.post("/vinculo/convite/usar", response_model=VinculoInfo)
def usar_convite(
    dados: ConviteUsar,
    gestante_id: str = Depends(exigir_gestante),
    db: Session = Depends(get_db),
):
    """Só a GESTANTE chama este endpoint. O ato de digitar o código é o
    consentimento dela -- o vínculo já nasce ativo, sem etapa extra."""
    convite = db.query(CodigoConvite).filter(CodigoConvite.codigo == dados.codigo.upper()).first()
    if not convite:
        raise HTTPException(status_code=404, detail="Código de convite não encontrado.")
    if convite.usado == "sim":
        raise HTTPException(status_code=409, detail="Este código já foi utilizado.")

    vinculo_existente = (
        db.query(Vinculo)
        .filter(Vinculo.gestante_id == gestante_id, Vinculo.profissional_id == convite.profissional_id)
        .first()
    )
    if vinculo_existente and vinculo_existente.status == "ativo":
        raise HTTPException(status_code=409, detail="Você já está vinculada a este profissional.")

    vinculo = Vinculo(
        gestante_id=gestante_id, profissional_id=convite.profissional_id,
        status="ativo", origem="convite",
    )
    convite.usado = "sim"
    db.add(vinculo)
    db.commit()
    db.refresh(vinculo)

    profissional = db.query(Profissional).filter(Profissional.id == convite.profissional_id).first()
    return VinculoInfo(
        id=vinculo.id, profissional_id=vinculo.profissional_id,
        profissional_nome=profissional.nome if profissional else "Desconhecido",
        status=vinculo.status, origem=vinculo.origem,
    )


@router.post("/vinculo/{vinculo_id}/revogar")
def revogar_vinculo(vinculo_id: int, gestante_id: str = Depends(exigir_gestante), db: Session = Depends(get_db)):
    """Só a gestante DONA do vínculo pode revogar -- confere isso antes
    de qualquer coisa, não confia só no id vir na URL."""
    vinculo = db.query(Vinculo).filter(Vinculo.id == vinculo_id).first()
    if not vinculo or vinculo.gestante_id != gestante_id:
        raise HTTPException(status_code=404, detail="Vínculo não encontrado.")
    vinculo.status = "revogado"
    db.commit()
    return {"status": "revogado"}


@router.post("/auth/profissional/upload-documento")
async def upload_documento(
    arquivo: UploadFile = File(...),
    profissional_id: str = Depends(exigir_profissional),
    db: Session = Depends(get_db),
):
    extensoes_permitidas = {".pdf", ".jpg", ".jpeg", ".png"}
    extensao = os.path.splitext(arquivo.filename)[1].lower()
    if extensao not in extensoes_permitidas:
        raise HTTPException(400, "Envie PDF, JPG ou PNG.")

    conteudo = await arquivo.read()
    if len(conteudo) > 10 * 1024 * 1024:
        raise HTTPException(400, "Arquivo maior que 10MB.")

    nome_arquivo = f"{profissional_id}{extensao}"
    caminho = os.path.join("uploads_documentos", nome_arquivo)
    with open(caminho, "wb") as f:
        f.write(conteudo)

    profissional = db.query(Profissional).filter(Profissional.id == profissional_id).first()
    profissional.documento_comprovante_path = caminho
    db.commit()

    return {"status": "documento recebido, aguardando conferência"}


@router.get("/vinculo/minhas-gestantes", response_model=list[GestanteVinculada])
def minhas_gestantes(profissional_id: str = Depends(exigir_profissional), db: Session = Depends(get_db)):
    """Lista só as gestantes com vínculo ATIVO com ESTE profissional --
    filtra pelo id que veio do token, nunca de parâmetro da requisição."""
    vinculos = (
        db.query(Vinculo)
        .filter(Vinculo.profissional_id == profissional_id, Vinculo.status == "ativo")
        .all()
    )
    resultado = []
    for v in vinculos:
        gestante = db.query(Gestante).filter(Gestante.id == v.gestante_id).first()
        if gestante:
            resultado.append(GestanteVinculada(
                gestante_id=gestante.id, nome=gestante.nome,
                vinculo_id=v.id, vinculo_status=v.status,
            ))
    return resultado
