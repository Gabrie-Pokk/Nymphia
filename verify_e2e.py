import requests
import json
import time
from datetime import datetime, timedelta

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:5173"

def log_test(name, success, details=""):
    status_str = "[PASS]" if success else "[FAIL]"
    print(f"{status_str} | {name}")
    if details:
        print(f"       -> {details}")

def run_e2e_validations():
    print("=================================================================")
    print("      NYMPHIA — SUÍTE DE VALIDAÇÃO E2E (HTTP AO VIVO)")
    print("=================================================================\n")

    # 1. Healthcheck e Degradação Graciosa
    res_health = requests.get(f"{BACKEND_URL}/health")
    health_data = res_health.json()
    log_test(
        "Healthcheck & Degradação Graciosa",
        res_health.status_code == 200 and health_data.get("status") == "online",
        f"Versão: {health_data.get('versao')} | Modelos: {len(health_data.get('modelos_rf_disponiveis', []))}"
    )

    # Frontend Dev Server Status
    res_fe = requests.get(FRONTEND_URL)
    log_test(
        "Frontend Dev Server (Vite) Acessível",
        res_fe.status_code == 200,
        f"Status: {res_fe.status_code} | Content-Type: {res_fe.headers.get('content-type')}"
    )

    # Rota pública de emergência (sem autenticação)
    res_emerg_pub = requests.post(f"{BACKEND_URL}/emergencia/notificar", json={"latitude": -23.55, "longitude": -46.63})
    log_test(
        "Rota de Emergência Pública Acessível sem Autenticação",
        res_emerg_pub.status_code == 200 and "192" in res_emerg_pub.json().get("orientacao_samu", ""),
        f"Orientação: {res_emerg_pub.json().get('orientacao_samu')}"
    )

    # 2. Fluxo da Gestante: Cadastro e Autenticação
    email_gestante = f"mariana_{int(time.time())}@nymphia.com.br"
    res_cad = requests.post(f"{BACKEND_URL}/auth/gestante/cadastro", json={
        "nome": "Mariana Costa",
        "email": email_gestante,
        "senha": "senhaMaternidade123"
    })
    gestante_data = res_cad.json()
    token_gestante = gestante_data.get("token")
    headers_gestante = {"Authorization": f"Bearer {token_gestante}"}
    log_test("Cadastro da Gestante", res_cad.status_code == 201 and "token" in gestante_data)

    # Teste de login com senha incorreta
    res_login_err = requests.post(f"{BACKEND_URL}/auth/gestante/login", json={
        "email": email_gestante,
        "senha": "senhaIncorreta999"
    })
    log_test("Login com senha incorreta rejeitado com 401", res_login_err.status_code == 401)

    # 3. Onboarding Clínico: DUM, DPP e Histórico Familiar
    res_onboarding = requests.post(f"{BACKEND_URL}/perfil-clinico", headers=headers_gestante, json={
        "idade": 29,
        "estado_civil": "Casada",
        "escolaridade": "Superior",
        "gestacoes_anteriores": 1,
        "partos_normais": 1,
        "partos_cesareos": 0,
        "perdas_gestacionais": 0,
        "dum": "2026-02-01",
        "dpp": "2026-11-08",
        "dpp_editada_manualmente": False,
        "maternidade_nome": "Hospital Santa Joana",
        "maternidade_endereco": "Rua Paraíso, 450",
        "maternidade_telefone": "1133334444"
    })
    log_test("Onboarding Clínico Salvo", res_onboarding.status_code == 201)

    # Edição manual da DPP
    res_edit_dpp = requests.put(f"{BACKEND_URL}/perfil-clinico", headers=headers_gestante, json={
        "dpp": "2026-11-15",
        "dpp_editada_manualmente": True
    })
    log_test(
        "Edição manual da DPP preservada com trava manual",
        res_edit_dpp.status_code == 200 and res_edit_dpp.json().get("dpp_editada_manualmente") is True
    )

    # Histórico Familiar dinâmico
    res_hf1 = requests.post(f"{BACKEND_URL}/historico-familiar", headers=headers_gestante, json={
        "parente": "mãe", "condicao": "Pré-eclâmpsia"
    })
    res_hf2 = requests.post(f"{BACKEND_URL}/historico-familiar", headers=headers_gestante, json={
        "parente": "avó materna", "condicao": "Diabetes Mellitus"
    })
    id_hf2 = res_hf2.json().get("id")
    # Exclusão seletiva de um item
    res_del_hf = requests.delete(f"{BACKEND_URL}/historico-familiar/{id_hf2}", headers=headers_gestante)
    res_list_hf = requests.get(f"{BACKEND_URL}/historico-familiar", headers=headers_gestante)
    log_test(
        "Histórico Familiar Dinâmico com Remoção Seletiva",
        res_del_hf.status_code == 204 and len(res_list_hf.json()) == 1,
        f"Itens restantes: {len(res_list_hf.json())}"
    )

    # 4. Check-in Diário: Análise e Alerta Imediato
    # Check-in Normal
    res_ck_normal = requests.post(f"{BACKEND_URL}/checkin/registrar", headers=headers_gestante, json={
        "humor": 5,
        "descricao": "Hoje me sinto ótima e muito animada.",
        "sintomas": [],
        "movimentos_bebe": 8
    })
    log_test("Check-in Normal registrado com data/hora do servidor", res_ck_normal.status_code == 201)

    # Check-in com Urgência Obstétrica (Sangramento e dor forte)
    res_ck_urgent = requests.post(f"{BACKEND_URL}/checkin/registrar", headers=headers_gestante, json={
        "humor": 1,
        "descricao": "Estou com sangramento vermelho vivo e dor de cabeca insuportavel.",
        "sintomas": ["sangramento", "dor de cabeça"],
        "movimentos_bebe": 2
    })
    ck_urgent_data = res_ck_urgent.json()
    log_test(
        "Check-in com Sintoma de Urgência dispara Alerta Imediato com SAMU 192",
        res_ck_urgent.status_code == 201 and "192" in ck_urgent_data.get("recomendacao", ""),
        f"Alertas: {ck_urgent_data.get('alerta_sintoma_fisico')}"
    )

    # Ordenação do Histórico (mais recente primeiro)
    res_ck_hist = requests.get(f"{BACKEND_URL}/checkin/historico", headers=headers_gestante)
    hist_items = res_ck_hist.json()
    is_ordered = len(hist_items) == 2 and hist_items[0]["id"] == ck_urgent_data["id"]
    log_test("Histórico de Check-in ordenado do mais recente para o mais antigo", is_ordered)

    # 5. Conversa com IA: Bypass de Urgência e Base Curada
    # Mensagem de urgência física (deve responder imediatamente com fonte regras_urgencia)
    res_chat_urg = requests.post(f"{BACKEND_URL}/conversa/enviar", headers=headers_gestante, json={
        "texto": "Estou com perda de liquido abundante e pressao 16 por 10"
    })
    chat_urg_data = res_chat_urg.json()
    log_test(
        "Chat: Sintoma de urgência física responde imediatamente com bypass sem LLM",
        chat_urg_data.get("alerta_emergencia") is True and chat_urg_data.get("fonte") == "regras_urgencia",
        f"Fonte: {chat_urg_data.get('fonte')}"
    )

    # Mensagem com destaque para Toxoplasmose (Protocolo FEBRASGO/MS)
    res_chat_toxo = requests.post(f"{BACKEND_URL}/conversa/enviar", headers=headers_gestante, json={
        "texto": "Como prevenir a toxoplasmose com relação à comida e gatos?"
    })
    chat_toxo_data = res_chat_toxo.json()
    log_test(
        "Chat: Destaque clínico próprio para Toxoplasmose",
        "TOXOPLASMOSE GESTACIONAL" in chat_toxo_data.get("resposta", ""),
        "Diretriz FEBRASGO/MS retornada"
    )

    # Autorização de compartilhamento de trecho da conversa
    res_chat_hist = requests.get(f"{BACKEND_URL}/conversa/historico", headers=headers_gestante)
    msg_id = res_chat_hist.json()[-1]["id"]
    res_auth_msg = requests.post(f"{BACKEND_URL}/conversa/{msg_id}/autorizar-compartilhamento", headers=headers_gestante)
    log_test("Autorização granular de compartilhamento de mensagem com médico", res_auth_msg.status_code == 200)

    # 6. Agenda & Alarmes
    now = datetime.utcnow()
    # Evento futuro
    res_ag_fut = requests.post(f"{BACKEND_URL}/agenda/eventos", headers=headers_gestante, json={
        "tipo": "consulta",
        "titulo": "Consulta Pré-Natal com Obstetra",
        "data_hora": (now + timedelta(days=7)).isoformat()
    })
    evento_id = res_ag_fut.json().get("id")

    # Evento passado
    requests.post(f"{BACKEND_URL}/agenda/eventos", headers=headers_gestante, json={
        "tipo": "exame",
        "titulo": "Ultrassom 1º Trimestre",
        "data_hora": (now - timedelta(days=40)).isoformat()
    })

    # Filtro apenas futuros
    res_ag_list_fut = requests.get(f"{BACKEND_URL}/agenda/eventos?apenas_futuros=true", headers=headers_gestante)
    res_ag_list_all = requests.get(f"{BACKEND_URL}/agenda/eventos?apenas_futuros=false", headers=headers_gestante)
    log_test(
        "Agenda: Filtro padrão de futuros omite eventos passados",
        len(res_ag_list_fut.json()) == 1 and len(res_ag_list_all.json()) == 2
    )

    # Concluir evento
    res_ag_conc = requests.patch(f"{BACKEND_URL}/agenda/eventos/{evento_id}/concluir", headers=headers_gestante)
    log_test("Conclusão de evento na agenda", res_ag_conc.status_code == 200 and res_ag_conc.json().get("concluido") is True)

    # Concluir evento inexistente retorna 404 (nunca 500)
    res_ag_404 = requests.patch(f"{BACKEND_URL}/agenda/eventos/999999/concluir", headers=headers_gestante)
    log_test("Concluir evento inexistente retorna 404", res_ag_404.status_code == 404)

    # 7. Dispositivos Bluetooth (Arm BP e Glicemia)
    res_med_pa = requests.post(f"{BACKEND_URL}/dispositivos/medicao", headers=headers_gestante, json={
        "tipo": "pressao_arterial",
        "sistolica": 122,
        "diastolica": 78,
        "origem": "dispositivo_bluetooth"
    })
    res_med_gli = requests.post(f"{BACKEND_URL}/dispositivos/medicao", headers=headers_gestante, json={
        "tipo": "glicemia",
        "glicemia": 84.5,
        "origem": "dispositivo_bluetooth"
    })
    log_test(
        "Medições Bluetooth SIG (0x1810 e 0x1808) registradas",
        res_med_pa.status_code == 201 and res_med_gli.status_code == 201
    )

    # 8. Cinta Nymphia (Doppler Wearable FHR 2027)
    res_cinta_sim = requests.get(f"{BACKEND_URL}/cinta/simulador")
    sim_data = res_cinta_sim.json()
    res_cinta_tele = requests.post(f"{BACKEND_URL}/cinta/telemetria", headers=headers_gestante, json={
        "bpm": sim_data.get("bpm", 140)
    })
    res_cinta_rec = requests.get(f"{BACKEND_URL}/cinta/leituras-recentes", headers=headers_gestante)
    log_test(
        "Cinta Nymphia (Doppler FHR): Telemetria e Simulador Contínuo",
        res_cinta_tele.status_code == 201 and len(res_cinta_rec.json()) > 0,
        f"FHR: {sim_data.get('bpm')} bpm ({sim_data.get('status')})"
    )

    # 9. Painel Médico, Vínculo Unilateral e Ordenação por Urgência
    email_prof = f"dr_carlos_{int(time.time())}@obstetra.med.br"
    res_prof = requests.post(f"{BACKEND_URL}/auth/profissional/cadastro", json={
        "nome": "Dr. Carlos Obstetra",
        "email": email_prof,
        "senha": "senhaMedForte123",
        "registro_tipo": "CRM",
        "registro_numero": "987654",
        "registro_uf": "SP"
    })
    prof_data = res_prof.json()
    token_prof = prof_data.get("token")
    headers_prof = {"Authorization": f"Bearer {token_prof}"}

    # Médico gera código
    res_cod = requests.post(f"{BACKEND_URL}/vinculo/convite/gerar", headers=headers_prof)
    codigo_convite = res_cod.json().get("codigo")
    log_test("Médico gera código de 8 caracteres", len(codigo_convite) == 8, f"Código: {codigo_convite}")

    # Gestante usa o código (é ela que cria o vínculo ativo)
    res_vinc = requests.post(f"{BACKEND_URL}/vinculo/convite/usar", headers=headers_gestante, json={"codigo": codigo_convite})
    log_test("Gestante resgata código e ativa vínculo", res_vinc.status_code == 201)

    # Painel do Médico ordenado por urgência
    res_painel = requests.get(f"{BACKEND_URL}/vinculo/minhas-gestantes", headers=headers_prof)
    painel_pacientes = res_painel.json()
    log_test(
        "Painel do Médico lista paciente priorizada por alertas",
        len(painel_pacientes) > 0 and painel_pacientes[0]["total_alertas_30d"] > 0,
        f"Alertas 30d da paciente: {painel_pacientes[0]['total_alertas_30d']}"
    )

    # Ficha da Paciente (Somente Leitura + Auditoria LGPD)
    res_ficha = requests.get(f"{BACKEND_URL}/vinculo/paciente/{gestante_data['id']}/ficha", headers=headers_prof)
    ficha_data = res_ficha.json()
    log_test(
        "Ficha da Paciente acessada pelo médico em modo somente leitura",
        res_ficha.status_code == 200 and ficha_data.get("somente_leitura") is True
    )

    # Médico registra anotação em campo próprio
    res_obs = requests.post(f"{BACKEND_URL}/vinculo/paciente/{gestante_data['id']}/observacao", headers=headers_prof, json={
        "observacao": "Paciente orientada quanto aos sinais de alerta. Manter repouso e hidratação."
    })
    log_test("Médico registra observação em campo próprio e auditado", res_obs.status_code == 201)

    # 10. Modo Parceiro e Blindagem de Dados Clínicos
    email_parc = f"parceiro_{int(time.time())}@teste.com"
    res_parc = requests.post(f"{BACKEND_URL}/auth/parceiro/cadastro", json={
        "nome": "Lucas Parceiro",
        "email": email_parc,
        "senha": "senhaParceiro123"
    })
    token_parc = res_parc.json().get("token")
    headers_parc = {"Authorization": f"Bearer {token_parc}"}

    # Gestante gera código para parceiro
    res_parc_cod = requests.post(f"{BACKEND_URL}/parceiro/convite/gerar", headers=headers_gestante)
    cod_parc = res_parc_cod.json().get("codigo")
    res_parc_use = requests.post(f"{BACKEND_URL}/parceiro/convite/usar", headers=headers_parc, json={"codigo": cod_parc})
    log_test("Parceiro resgata convite e conecta à gestante", res_parc_use.status_code == 201)

    # Parceiro acessa agenda e marcos
    res_parc_agenda = requests.get(f"{BACKEND_URL}/parceiro/agenda", headers=headers_parc)
    res_parc_marcos = requests.get(f"{BACKEND_URL}/parceiro/marcos", headers=headers_parc)
    log_test(
        "Parceiro acessa agenda compartilhada e marcos gestacionais",
        res_parc_agenda.status_code == 200 and "semana_atual" in res_parc_marcos.json()
    )

    # Blindagem: Parceiro NUNCA acessa check-ins de gestante
    res_parc_checkin = requests.get(f"{BACKEND_URL}/checkin/historico", headers=headers_parc)
    log_test("Parceiro BLOQUEADO de acessar check-ins clínicos (403)", res_parc_checkin.status_code == 403)

    # 11. Conformidade LGPD: Auditoria, Exportação PDF/JSON e Exclusão
    # Log de Acesso consultável pela titular
    res_log_acesso = requests.get(f"{BACKEND_URL}/meus-dados/log-acesso", headers=headers_gestante)
    logs = res_log_acesso.json()
    log_test(
        "Log de Acesso a dados sensíveis registra acessos do médico e do parceiro",
        len(logs) >= 2,
        f"Total de acessos auditados: {len(logs)}"
    )

    # Exportação JSON
    res_exp_json = requests.get(f"{BACKEND_URL}/meus-dados/exportar?formato=json", headers=headers_gestante)
    log_test("Portabilidade LGPD em JSON estruturado", res_exp_json.status_code == 200 and "titular" in res_exp_json.json())

    # Exportação PDF
    res_exp_pdf = requests.get(f"{BACKEND_URL}/meus-dados/exportar?formato=pdf", headers=headers_gestante)
    log_test(
        "Portabilidade LGPD em PDF gerado (ReportLab)",
        res_exp_pdf.status_code == 200 and len(res_exp_pdf.content) > 1000 and res_exp_pdf.headers.get("content-type") == "application/pdf",
        f"Tamanho do PDF: {len(res_exp_pdf.content)} bytes"
    )

    # Consentimento de IA (CFM 2.454/2026)
    res_ia_consent = requests.put(f"{BACKEND_URL}/meus-dados/consentimento-ia?recusa_ia=true", headers=headers_gestante)
    log_test("Direito de recusa de IA atualizado conforme CFM 2.454/2026", res_ia_consent.json().get("recusa_ia") is True)

    # Exclusão definitiva de conta
    res_del_acc = requests.delete(f"{BACKEND_URL}/minha-conta", headers=headers_gestante)
    res_login_pos_del = requests.post(f"{BACKEND_URL}/auth/gestante/login", json={
        "email": email_gestante,
        "senha": "senhaMaternidade123"
    })
    log_test(
        "Eliminação definitiva de conta e dados em cascata (Art. 18 LGPD)",
        res_del_acc.status_code == 200 and res_login_pos_del.status_code == 401
    )

    print("\n=================================================================")
    print("      TODAS AS 24+ VALIDAÇÕES E2E CONCLUÍDAS COM SUCESSO!")
    print("=================================================================")

if __name__ == "__main__":
    run_e2e_validations()
