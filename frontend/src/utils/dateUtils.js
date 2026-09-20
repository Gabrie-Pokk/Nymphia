/**
 * Utilitários de Formatação de Data e Hora para o Nymphia
 * Garante que timestamps armazenados em UTC pelo backend sejam sempre
 * convertidos corretamente para o fuso horário local do usuário (ex: Horário de Brasília, UTC-3).
 */

export function parseDate(dateInput) {
  if (!dateInput) return new Date();
  if (dateInput instanceof Date) return dateInput;

  let str = String(dateInput).trim();
  // Se a string ISO não possuir indicação de fuso (sem 'Z' e sem offset +/-XX:XX)
  // adicionamos 'Z' para indicar que o timestamp do servidor está em UTC.
  if (!str.endsWith('Z') && !str.includes('+') && !str.match(/T.*-\d{2}:\d{2}$/)) {
    // Trata tanto 'YYYY-MM-DDTHH:MM:SS' quanto 'YYYY-MM-DD HH:MM:SS'
    str = str.replace(' ', 'T') + 'Z';
  }
  return new Date(str);
}

export function formatDateTime(dateInput, options = { dateStyle: 'short', timeStyle: 'short' }) {
  if (!dateInput) return '';
  const d = parseDate(dateInput);
  if (isNaN(d.getTime())) return String(dateInput);
  return d.toLocaleString('pt-BR', options);
}

export function formatDate(dateInput, options = { dateStyle: 'short' }) {
  if (!dateInput) return '';
  const d = parseDate(dateInput);
  if (isNaN(d.getTime())) return String(dateInput);
  return d.toLocaleDateString('pt-BR', options);
}

export function formatTime(dateInput, options = { timeStyle: 'short' }) {
  if (!dateInput) return '';
  const d = parseDate(dateInput);
  if (isNaN(d.getTime())) return String(dateInput);
  return d.toLocaleTimeString('pt-BR', options);
}
