"""
Cópia única do banco antigo para o novo (app/copia_de_banco.py).

O Postgres grátis do Render da Nymphia expira em 19/10/2026. A troca de banco
é feita pelo próprio servidor, de servidor para servidor. Aqui os dois bancos
são SQLite; a mesma sequência foi testada à mão com dois Postgres 16.
"""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.copia_de_banco import copiar_banco_antigo_se_preciso
from app.database import Base
from app.models.auth import Gestante
from app.models.clinical import CheckinRegistro


def _banco(caminho):
    engine = create_engine(f"sqlite:///{caminho}")
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def bancos(tmp_path):
    origem = _banco(tmp_path / "antigo.db")
    destino = _banco(tmp_path / "novo.db")
    with Session(origem) as s:
        maria = Gestante(nome="Maria Teste", email="maria@ex.com", senha_hash="hash-da-maria")
        s.add(maria)
        s.flush()
        s.add_all([
            CheckinRegistro(gestante_id=maria.id, humor=3, sintomas=["enjoo"], categorias_bertimbau=None),
            CheckinRegistro(gestante_id=maria.id, humor=1, sintomas=[], categorias_bertimbau={"ansiedade": 0.8}),
        ])
        s.commit()
    with origem.begin() as c:
        c.execute(text("CREATE TABLE manutencoes_executadas (nome VARCHAR(100) PRIMARY KEY, executada_em VARCHAR(40) NOT NULL)"))
        c.execute(text("INSERT INTO manutencoes_executadas VALUES ('rotacao_senha_vazada_2026_10_08', '2026-10-08')"))
        c.execute(text("CREATE TABLE segredos_servidor (nome VARCHAR(100) PRIMARY KEY, valor TEXT NOT NULL, criado_em VARCHAR(40) NOT NULL)"))
        c.execute(text("INSERT INTO segredos_servidor VALUES ('jwt_hs256', 'chave-do-banco-antigo', '2026-10-15')"))
        # Um JSON 'null' (diferente de NULL) numa coluna obrigatória precisa passar igual
        c.execute(text("UPDATE checkin_registros SET alerta_sintoma_fisico = 'null' WHERE humor = 1"))
        # E um NULL de verdade (o ORM gravaria JSON 'null' para None)
        c.execute(text("UPDATE checkin_registros SET categorias_bertimbau = NULL WHERE humor = 3"))
    url_origem = f"sqlite:///{tmp_path / 'antigo.db'}"
    return origem, destino, url_origem


def _contar(engine, tabela):
    with engine.connect() as c:
        return c.execute(text(f"SELECT COUNT(*) FROM {tabela}")).scalar()


def test_sem_variavel_nao_faz_nada(bancos, monkeypatch):
    _, destino, _ = bancos
    monkeypatch.delenv("NYMPHIA_DATABASE_URL_ANTIGO", raising=False)
    assert copiar_banco_antigo_se_preciso(destino=destino) is None
    assert _contar(destino, "gestantes") == 0


def test_copia_tudo_para_o_banco_novo(bancos):
    origem, destino, url = bancos
    resumo = copiar_banco_antigo_se_preciso(destino=destino, url_origem=url)
    assert resumo["copiado"] is True
    assert resumo["tabelas"]["gestantes"] == 1
    assert _contar(destino, "checkin_registros") == 2
    # A chave dos logins vem junto: quem estava logado continua logado
    with destino.connect() as c:
        assert c.execute(text("SELECT valor FROM segredos_servidor")).scalar() == "chave-do-banco-antigo"
        assert c.execute(text("SELECT COUNT(*) FROM manutencoes_executadas")).scalar() == 1


def test_json_passa_exatamente_como_estava(bancos):
    _, destino, url = bancos
    copiar_banco_antigo_se_preciso(destino=destino, url_origem=url)
    with destino.connect() as c:
        linhas = c.execute(text(
            "SELECT humor, categorias_bertimbau IS NULL, alerta_sintoma_fisico, sintomas "
            "FROM checkin_registros ORDER BY humor"
        )).all()
    assert linhas[0][1] == 0 and linhas[0][2] == "null"  # JSON 'null' continua JSON 'null'
    assert linhas[1][1] == 1  # NULL continua NULL
    assert linhas[1][3] == '["enjoo"]'


def test_banco_novo_com_contas_nao_recebe_copia(bancos):
    _, destino, url = bancos
    copiar_banco_antigo_se_preciso(destino=destino, url_origem=url)
    resumo = copiar_banco_antigo_se_preciso(destino=destino, url_origem=url)
    assert resumo == {"copiado": False, "motivo": "destino_com_contas"}
    assert _contar(destino, "gestantes") == 1


def test_o_que_o_banco_novo_criou_sozinho_da_lugar_ao_antigo(bancos):
    # Se o servidor já ligou uma vez com o banco novo, ele criou uma chave
    # própria e anotou manutenções. Sem contas, isso é trocado pelo do antigo.
    _, destino, url = bancos
    with destino.begin() as c:
        c.execute(text("CREATE TABLE segredos_servidor (nome VARCHAR(100) PRIMARY KEY, valor TEXT NOT NULL, criado_em VARCHAR(40) NOT NULL)"))
        c.execute(text("INSERT INTO segredos_servidor VALUES ('jwt_hs256', 'chave-nova-provisoria', '2026-10-16')"))
    copiar_banco_antigo_se_preciso(destino=destino, url_origem=url)
    with destino.connect() as c:
        assert c.execute(text("SELECT valor FROM segredos_servidor")).scalar() == "chave-do-banco-antigo"


def test_falha_para_a_inicializacao_e_nao_deixa_nada_pela_metade(bancos, tmp_path, caplog):
    _, destino, _ = bancos
    with pytest.raises(RuntimeError, match="banco novo ficou como estava"):
        copiar_banco_antigo_se_preciso(
            destino=destino,
            url_origem="postgresql://alguem:SenhaQueNaoPodeVazar@127.0.0.1:1/nada",
        )
    assert _contar(destino, "gestantes") == 0
    assert "SenhaQueNaoPodeVazar" not in caplog.text


def test_endereco_invalido_e_avisado(bancos):
    _, destino, _ = bancos
    with pytest.raises(RuntimeError, match="não é um endereço de banco válido"):
        copiar_banco_antigo_se_preciso(destino=destino, url_origem="isso não é um endereço")


def test_mesmo_banco_nao_copia(bancos, tmp_path):
    _, destino, _ = bancos
    resumo = copiar_banco_antigo_se_preciso(destino=destino, url_origem=f"sqlite:///{tmp_path / 'novo.db'}")
    assert resumo == {"copiado": False, "motivo": "mesmo_banco"}


def test_na_inicializacao_a_copia_vem_antes_das_manutencoes(monkeypatch):
    # Se as manutenções rodassem antes, o banco novo anotaria manutenções
    # próprias e criaria outra chave dos logins antes de receber os dados.
    import asyncio
    import app.copia_de_banco as copia
    import app.database as banco
    import app.main as principal

    ordem = []
    monkeypatch.setattr(banco, "engine", create_engine("sqlite://"))
    monkeypatch.setattr(banco, "executar_migracoes_automaticas", lambda: ordem.append("migracoes"))
    monkeypatch.setattr(banco, "executar_manutencoes_unicas", lambda: ordem.append("manutencoes"))
    monkeypatch.setattr(copia, "copiar_banco_antigo_se_preciso", lambda: ordem.append("copia"))
    monkeypatch.setattr(principal, "carregar_modelos_ml", lambda: None)

    async def ligar_e_desligar():
        async with principal.lifespan(principal.app):
            pass

    asyncio.run(ligar_e_desligar())
    assert ordem == ["migracoes", "copia", "manutencoes"]
