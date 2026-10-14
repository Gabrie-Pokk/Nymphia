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


def test_tabela_ufrj_ms_pontos_de_corte():
    """Valida as categorias oficiais da UFRJ / Ministério da Saúde (Agosto de 2022)."""
    assert "baixo_peso" in TABELA_GANHO_UFRJ_MS_2022
    assert "adequado" in TABELA_GANHO_UFRJ_MS_2022
    assert "sobrepeso" in TABELA_GANHO_UFRJ_MS_2022
    assert "obesidade" in TABELA_GANHO_UFRJ_MS_2022

    # Metas de ganho total
    assert TABELA_GANHO_UFRJ_MS_2022["baixo_peso"]["ganho_total_min"] == 12.5
    assert TABELA_GANHO_UFRJ_MS_2022["baixo_peso"]["ganho_total_max"] == 18.0
    assert TABELA_GANHO_UFRJ_MS_2022["adequado"]["ganho_total_min"] == 11.5
    assert TABELA_GANHO_UFRJ_MS_2022["adequado"]["ganho_total_max"] == 16.0
    assert TABELA_GANHO_UFRJ_MS_2022["sobrepeso"]["ganho_total_min"] == 7.0
    assert TABELA_GANHO_UFRJ_MS_2022["sobrepeso"]["ganho_total_max"] == 11.5
    assert TABELA_GANHO_UFRJ_MS_2022["obesidade"]["ganho_total_min"] == 5.0
    assert TABELA_GANHO_UFRJ_MS_2022["obesidade"]["ganho_total_max"] == 9.0

    # Taxas de ganho semanal
    assert TABELA_GANHO_UFRJ_MS_2022["baixo_peso"]["ganho_semanal_min"] == 0.44
    assert TABELA_GANHO_UFRJ_MS_2022["baixo_peso"]["ganho_semanal_max"] == 0.58
    assert TABELA_GANHO_UFRJ_MS_2022["adequado"]["ganho_semanal_min"] == 0.35
    assert TABELA_GANHO_UFRJ_MS_2022["adequado"]["ganho_semanal_max"] == 0.50
    assert TABELA_GANHO_UFRJ_MS_2022["sobrepeso"]["ganho_semanal_min"] == 0.23
    assert TABELA_GANHO_UFRJ_MS_2022["sobrepeso"]["ganho_semanal_max"] == 0.33
    assert TABELA_GANHO_UFRJ_MS_2022["obesidade"]["ganho_semanal_min"] == 0.17
    assert TABELA_GANHO_UFRJ_MS_2022["obesidade"]["ganho_semanal_max"] == 0.27


def test_convergencia_curva_ufrj_semanas():
    """Valida a progressão no 1º trimestre e convergência na 40ª semana."""
    # Semana 13: Ganho total esperado de 0,5 a 2,0 kg
    g_min_13, g_max_13 = calcular_faixa_ganho_esperado_ufrj("adequado", 13)
    assert g_min_13 == 0.50
    assert g_max_13 == 2.00

    # Semana 40: Convergência exata para as faixas totais
    for cat_chave, valores in TABELA_GANHO_UFRJ_MS_2022.items():
        g_min_40, g_max_40 = calcular_faixa_ganho_esperado_ufrj(cat_chave, 40)
        assert g_min_40 == valores["ganho_total_min"]
        assert g_max_40 == valores["ganho_total_max"]


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
    assert "UFRJ / Ministério da Saúde" in ufrj["referencia"]
    assert ufrj["status"] == "ADEQUADO"
    assert ufrj["fora_do_escopo"] is False
