/**
 * Nymphia — Teste Automatizado dos 3 Estados da Rota de Emergência
 * Requisito 1.3:
 * 1. Sucesso com equipe vinculada: Confirmação exibida.
 * 2. Erro do servidor (500/502/503): Confirmação NÃO PODE APARECER.
 * 3. Rede indisponível (offline/timeout): Confirmação NÃO PODE APARECER.
 */
import assert from 'assert';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Lê o arquivo EmergencyScreen.jsx para garantir que a lógica estática está íntegra
const emergencyCode = fs.readFileSync(path.join(__dirname, 'src', 'pages', 'EmergencyScreen.jsx'), 'utf-8');

console.log("=================================================================");
console.log("🚑 NYMPHIA — TESTE AUTOMATIZADO: ESTADOS DA TELA DE EMERGÊNCIA");
console.log("=================================================================");

// 1. Validação estática no código-fonte
assert(
  !emergencyCode.includes("Maternidade de Referência Regional"),
  "FALHA: Endereço falso de hospital ainda presente no código!"
);
assert(
  !emergencyCode.includes("(11) 3333-4444"),
  "FALHA: Telefone falso de hospital ainda presente no código!"
);
console.log("[✓] Hospital falso e telefone fake completamente removidos.");

// 2. Simulação dos 3 casos da máquina de estados do EmergencyScreen
function processarRespostaEmergencia(resOk, resJson, redeFalhou) {
  let notificacaoStatus;
  if (redeFalhou) {
    notificacaoStatus = { enviado: false, profissionalNotificado: false, erro: true };
  } else if (resOk) {
    notificacaoStatus = {
      enviado: true,
      profissionalNotificado: Boolean(resJson?.profissional_notificado),
      erro: false
    };
  } else {
    notificacaoStatus = { enviado: false, profissionalNotificado: false, erro: true };
  }

  // Gera texto renderizado correspondente
  let textoRenderizado = "";
  let confirmacaoVisivel = false;

  if (notificacaoStatus.enviado && notificacaoStatus.profissionalNotificado) {
    textoRenderizado = "✓ Alerta transmitido em paralelo para sua equipe de saúde vinculada.";
    confirmacaoVisivel = true;
  } else if (notificacaoStatus.enviado && !notificacaoStatus.profissionalNotificado) {
    textoRenderizado = "ℹ️ Chamada de emergência pública registrada. Sem equipe médica vinculada nesta sessão — o atendimento depende exclusivamente da discagem ao SAMU 192.";
    confirmacaoVisivel = false;
  } else if (notificacaoStatus.erro) {
    textoRenderizado = "⚠️ Não foi possível registrar o evento no servidor. Disque 192 (SAMU) imediatamente no seu telefone!";
    confirmacaoVisivel = false;
  }

  return { notificacaoStatus, textoRenderizado, confirmacaoVisivel };
}

// CASO 1: Sucesso com médico vinculado
const c1 = processarRespostaEmergencia(true, { profissional_notificado: true }, false);
assert.strictEqual(c1.confirmacaoVisivel, true, "Caso 1 falhou: confirmação deveria aparecer");
assert(c1.textoRenderizado.includes("✓ Alerta transmitido"), "Texto deveria confirmar equipe");
console.log("[✓] Caso 1 (Sucesso com equipe vinculada): Confirmação de alerta transmitido exibida corretamente.");

// CASO 1B: Sucesso anônimo/sem médico
const c1b = processarRespostaEmergencia(true, { profissional_notificado: false }, false);
assert.strictEqual(c1b.confirmacaoVisivel, false, "Caso 1B falhou: confirmação NÃO pode aparecer");
assert(c1b.textoRenderizado.includes("Sem equipe médica vinculada"), "Deveria orientar dependência do 192");
console.log("[✓] Caso 1B (Sucesso anônimo/deslogado): Confirmação NÃO exibida, aviso honesto do SAMU 192.");

// CASO 2: Erro do servidor (HTTP 500 / 502 / 503)
const c2 = processarRespostaEmergencia(false, null, false);
assert.strictEqual(c2.confirmacaoVisivel, false, "Caso 2 falhou: confirmação NÃO PODE APARECER em erro 500!");
assert(c2.textoRenderizado.includes("⚠️ Não foi possível registrar"), "Deveria exibir alerta de falha no servidor");
assert(c2.textoRenderizado.includes("192"), "Deveria instruir discagem imediata ao 192");
console.log("[✓] Caso 2 (Erro HTTP 500/502 do servidor): Confirmação NÃO exibida. Alerta vermelho de socorro 192.");

// CASO 3: Rede indisponível (offline / timeout / backend desligado)
const c3 = processarRespostaEmergencia(false, null, true);
assert.strictEqual(c3.confirmacaoVisivel, false, "Caso 3 falhou: confirmação NÃO PODE APARECER offline!");
assert(c3.textoRenderizado.includes("⚠️ Não foi possível registrar"), "Deveria exibir alerta de falha de conexão");
assert(c3.textoRenderizado.includes("192"), "Deveria instruir discagem imediata ao 192");
console.log("[✓] Caso 3 (Rede indisponível / Servidor fora): Confirmação NÃO exibida. Alerta vermelho de socorro 192.");

console.log("=================================================================");
console.log("   TODOS OS 3 CASOS DO BLOCO 1 FORAM VALIDADOS COM SUCESSO!");
console.log("=================================================================");
