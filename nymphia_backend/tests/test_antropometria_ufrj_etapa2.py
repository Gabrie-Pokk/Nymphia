import pytest
from datetime import datetime, date, timedelta
from app.services.anthropometry_service import (
    TABELA_GANHO_UFRJ_MS_2022,
    calcular_imc,
    classificar_imc_pre_gestacional,
    calcular_faixa_ganho_esperado_ufrj,
    classificar_ganho_ponderal_ufrj_ms,
    classificar_curva_atalah
)
from app.models.clinical import PerfilClinico, RegistroAntropometrico


def test_tabela_brasileira_febrasgo_2023():
    """
    Valores acumulados da FEBRASGO 2023 (Surita et al., RBGO 45(2):104-108, Quadro 1),
    conferidos em 15/10/2026. Antes o código usava os valores do IOM 2009.
    """
    esperado = {
        "baixo_peso": {13: (0.2, 1.2), 27: (5.6, 7.2), 40: (9.7, 12.2)},
        "adequado": {13: (-1.8, 0.7), 27: (3.1, 6.3), 40: (8.0, 12.0)},
        "sobrepeso": {13: (-1.6, -0.05), 27: (2.3, 3.7), 40: (7.0, 9.0)},
        "obesidade": {13: (-1.6, -0.05), 27: (1.1, 2.7), 40: (5.0, 7.2)},
    }
    for categoria, marcos in esperado.items():
        assert TABELA_GANHO_UFRJ_MS_2022[categoria]["marcos"] == marcos
        assert TABELA_GANHO_UFRJ_MS_2022[categoria]["ganho_total_min"] == marcos[40][0]
        assert TABELA_GANHO_UFRJ_MS_2022[categoria]["ganho_total_max"] == marcos[40][1]
        # A faixa calculada bate exatamente com os marcos publicados
        for semana, faixa in marcos.items():
            assert calcular_faixa_ganho_esperado_ufrj(categoria, semana) == faixa


def test_valores_do_iom_nao_estao_mais_na_tabela():
    totais = {(d["ganho_total_min"], d["ganho_total_max"]) for d in TABELA_GANHO_UFRJ_MS_2022.values()}
    for valor_iom in [(12.5, 18.0), (11.5, 16.0), (7.0, 11.5), (5.0, 9.0)]:
        assert valor_iom not in totais


def test_interpolacao_entre_marcos():
    # Semana 0: nenhum ganho
    assert calcular_faixa_ganho_esperado_ufrj("adequado", 0) == (0.0, 0.0)
    # Semana 20 (meio do caminho entre 13 e 27): média dos marcos
    assert calcular_faixa_ganho_esperado_ufrj("adequado", 20) == (0.65, 3.5)
    # Depois de 40 semanas vale a faixa da 40ª
    assert calcular_faixa_ganho_esperado_ufrj("adequado", 42) == (8.0, 12.0)


def test_eutrofica_com_15_kg_na_40a_semana_esta_acima():
    """Com o IOM este caso aparecia como adequado (11,5 a 16 kg)."""
    res = classificar_ganho_ponderal_ufrj_ms(semana=40, peso_atual_kg=75.0, peso_pre_kg=60.0, altura_cm=165.0)
    assert res["status"] == "ACIMA"
    assert res["ganho_esperado_min_kg"] == 8.0
    assert res["ganho_esperado_max_kg"] == 12.0


def test_cortes_de_imc():
    assert classificar_imc_pre_gestacional(18.49)["categoria"] == "Baixo Peso"
    assert classificar_imc_pre_gestacional(18.5)["categoria"] == "Adequado (Eutrófica)"
    assert classificar_imc_pre_gestacional(24.99)["categoria"] == "Adequado (Eutrófica)"
    assert classificar_imc_pre_gestacional(25.0)["categoria"] == "Sobrepeso"
    assert classificar_imc_pre_gestacional(30.0)["categoria"] == "Obesidade"


def test_adolescente_fora_do_escopo_ufrj():
    """
    Gestantes adolescentes (< 18 anos) devem ser sinalizadas com declaração explícita
    de limitação de escopo da curva UFRJ/MS 2022 (Parte 9 do parecer e Seção 38.1.1 do projeto).
    """
    res = classificar_ganho_ponderal_ufrj_ms(
        semana=24,
        peso_atual_kg=60.0,
        peso_pre_kg=54.0,
        altura_cm=160.0,
        idade_gestante=16
    )
    assert res["fora_do_escopo"] is True
    assert res["motivo_fora_do_escopo"] == "adolescente"
    assert "padronizadas para gestantes adultas" in res["aviso_escopo"]
    assert "menos de 18 anos" in res["aviso_escopo"]


def test_gestacao_multipla_fora_do_escopo_ufrj():
    """Gestações múltiplas (gemelares) devem ser sinalizadas como fora de escopo."""
    res = classificar_ganho_ponderal_ufrj_ms(
        semana=28,
        peso_atual_kg=72.0,
        peso_pre_kg=60.0,
        altura_cm=165.0,
        idade_gestante=30,
        gestacao_multipla=True
    )
    assert res["fora_do_escopo"] is True
    assert res["motivo_fora_do_escopo"] == "gestacao_multipla"
    assert "gemelares" in res["aviso_escopo"]


def test_comunicacao_obrigatoria_sem_julgamento():
    """
    Regra de Comunicação Obrigatória (Seção 38.1.1):
    Quando o ganho está fora da faixa, o texto NUNCA avalia pejorativamente a pessoa.
    Termos de julgamento sobre imagem corporal são vedados.
    """
    # Ganho excessivo: 14 kg na semana 20 (adequado seria ~4 a 6 kg)
    res_acima = classificar_ganho_ponderal_ufrj_ms(
        semana=20,
        peso_atual_kg=74.0,
        peso_pre_kg=60.0,
        altura_cm=165.0,
        idade_gestante=26
    )
    assert res_acima["status"] == "ACIMA"
    orientacao_acima = res_acima["orientacao"].lower()
    assert "você ganhou peso demais" not in orientacao_acima
    assert "engordou demais" not in orientacao_acima
    assert "acima da faixa estimada" in orientacao_acima
    assert "vale comentar com seu obstetra" in orientacao_acima

    # Ganho insuficiente: 0.2 kg na semana 24
    res_abaixo = classificar_ganho_ponderal_ufrj_ms(
        semana=24,
        peso_atual_kg=60.2,
        peso_pre_kg=60.0,
        altura_cm=165.0,
        idade_gestante=26
    )
    assert res_abaixo["status"] == "ABAIXO"
    orientacao_abaixo = res_abaixo["orientacao"].lower()
    assert "ganhou pouco" not in orientacao_abaixo
    assert "abaixo da faixa estimada" in orientacao_abaixo
    assert "vale compartilhar essa evolução" in orientacao_abaixo


def test_endpoint_painel_antropometria_retorna_ufrj(client, db_session):
    """
    Valida a integração da rota GET /antropometria/painel retornando
    o diagnóstico da UFRJ / Ministério da Saúde (2022).
    """
    import uuid
    email = f"gestante_ufrj_{uuid.uuid4().hex[:6]}@teste.com"
    cad_res = client.post("/auth/gestante/cadastro", json={
        "nome": "Gestante Teste UFRJ",
        "email": email,
        "senha": "senhaSegura123",
        "aceite_termos": True,
        "consentimento_dados_saude": True
    })
    assert cad_res.status_code in (200, 201)
    gestante_token = cad_res.json()["token"]
    headers = {"Authorization": f"Bearer {gestante_token}"}

    # Sem cadastro clínico, altura e peso não são aceitos (nada de DUM inventada)
    sem_perfil = client.post("/antropometria/perfil-base", json={
        "altura_cm": 165.0, "peso_pre_gestacional": 60.0
    }, headers=headers)
    assert sem_perfil.status_code == 409

    # Cadastro clínico com DUM de 22 semanas atrás
    dum = date.today() - timedelta(days=22 * 7)
    perfil_res = client.post("/perfil-clinico", json={
        "idade": 28, "gestacoes_anteriores": 0, "partos_normais": 0, "partos_cesareos": 0,
        "perdas_gestacionais": 0, "dum": dum.isoformat(), "dpp": (dum + timedelta(days=280)).isoformat()
    }, headers=headers)
    assert perfil_res.status_code == 201, perfil_res.text

    # Atualiza perfil base (altura e peso pré-gestacional)
    base_res = client.post("/antropometria/perfil-base", json={
        "altura_cm": 165.0,
        "peso_pre_gestacional": 60.0
    }, headers=headers)
    assert base_res.status_code == 200

    # Insere uma pesagem
    reg_res = client.post("/antropometria/registro", json={
        "semana_gestacional": 22,
        "peso_atual_kg": 65.0,
        "altura_uterina_cm": 21.0
    }, headers=headers)
    assert reg_res.status_code == 201

    # Consulta painel
    res = client.get("/antropometria/painel", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["altura_cm"] == 165.0
    assert data["peso_pre_gestacional"] == 60.0
    assert data["peso_atual_kg"] == 65.0
    assert data["ganho_peso_acumulado_kg"] == 5.0

    # Validação do campo avaliacao_ganho_ufrj
    assert "avaliacao_ganho_ufrj" in data
    ufrj = data["avaliacao_ganho_ufrj"]
    assert ufrj is not None
    assert "FEBRASGO 2023" in ufrj["referencia"]
    # Semana 22 (informada na pesagem), eutrófica: faixa de 1,35 a 4,3 kg; 5 kg fica acima
    assert ufrj["semana"] == 22
    assert ufrj["status"] == "ACIMA"
    # A curva de Atalah não é mais usada
    assert data["avaliacao_atalah"] is None
    assert ufrj["fora_do_escopo"] is False
