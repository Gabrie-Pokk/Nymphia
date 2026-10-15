// Evita "Dr(a). Dra. Fulana": só acrescenta o título quando o nome ainda não tem um.
const TEM_TITULO = /^\s*(dr\(a\)|dra|dr|enf[a]?|prof[a]?)\.?\s/i;

export function nomeComTitulo(nome, padrao = 'Profissional') {
  const limpo = (nome || '').trim();
  if (!limpo) return padrao;
  return TEM_TITULO.test(limpo) ? limpo : `Dr(a). ${limpo}`;
}
