import React from 'react';

// Perguntas usadas pelos modelos de risco v2 e pelos fatores clínicos.
// Todas aceitam "não sei": resposta vazia fica desconhecida, nada é inventado.

export const UFS = [
  [12, 'Acre'], [27, 'Alagoas'], [16, 'Amapá'], [13, 'Amazonas'], [29, 'Bahia'], [23, 'Ceará'],
  [53, 'Distrito Federal'], [32, 'Espírito Santo'], [52, 'Goiás'], [21, 'Maranhão'], [51, 'Mato Grosso'],
  [50, 'Mato Grosso do Sul'], [31, 'Minas Gerais'], [15, 'Pará'], [25, 'Paraíba'], [41, 'Paraná'],
  [26, 'Pernambuco'], [22, 'Piauí'], [33, 'Rio de Janeiro'], [24, 'Rio Grande do Norte'],
  [43, 'Rio Grande do Sul'], [11, 'Rondônia'], [14, 'Roraima'], [42, 'Santa Catarina'], [35, 'São Paulo'],
  [28, 'Sergipe'], [17, 'Tocantins']
];

export const CAMPOS_RISCO = [
  'numero_fetos', 'mes_inicio_prenatal', 'uf_residencia', 'pre_eclampsia_previa', 'hipertensao_cronica', 'diabetes_previo',
  'historico_familiar_pe', 'historico_familiar_dm'
];

// Valor do formulário para o formato da API (vazio vira null)
export function paraApi(valores) {
  const numero = (v) => (v === '' || v === null || v === undefined ? null : Number(v));
  const simNao = (v) => (v === 'sim' ? true : v === 'nao' ? false : null);
  return {
    numero_fetos: numero(valores.numero_fetos),
    mes_inicio_prenatal: numero(valores.mes_inicio_prenatal),
    uf_residencia: numero(valores.uf_residencia),
    pre_eclampsia_previa: simNao(valores.pre_eclampsia_previa),
    hipertensao_cronica: simNao(valores.hipertensao_cronica),
    diabetes_previo: simNao(valores.diabetes_previo),
    historico_familiar_pe: simNao(valores.historico_familiar_pe),
    historico_familiar_dm: simNao(valores.historico_familiar_dm)
  };
}

// Do formato da API para o formulário
export function daApi(perfil) {
  const texto = (v) => (v === null || v === undefined ? '' : String(v));
  const simNao = (v) => (v === true ? 'sim' : v === false ? 'nao' : '');
  return {
    numero_fetos: texto(perfil?.numero_fetos),
    mes_inicio_prenatal: texto(perfil?.mes_inicio_prenatal),
    uf_residencia: texto(perfil?.uf_residencia),
    pre_eclampsia_previa: simNao(perfil?.pre_eclampsia_previa),
    hipertensao_cronica: simNao(perfil?.hipertensao_cronica),
    diabetes_previo: simNao(perfil?.diabetes_previo),
    historico_familiar_pe: simNao(perfil?.historico_familiar_pe),
    historico_familiar_dm: simNao(perfil?.historico_familiar_dm)
  };
}

function SimNao({ id, rotulo, valor, onChange }) {
  return (
    <div className="form-group">
      <label htmlFor={id}>{rotulo}</label>
      <select id={id} className="form-control" value={valor} onChange={(e) => onChange(e.target.value)}>
        <option value="">Não sei</option>
        <option value="sim">Sim</option>
        <option value="nao">Não</option>
      </select>
    </div>
  );
}

export default function PerguntasRiscoGestacional({ valores, onChange }) {
  const muda = (campo) => (valor) => onChange(campo, valor);
  return (
    <div>
      <div className="form-group">
        <label htmlFor="risco-fetos">Quantos bebês nesta gestação?</label>
        <select id="risco-fetos" className="form-control" value={valores.numero_fetos}
          onChange={(e) => onChange('numero_fetos', e.target.value)}>
          <option value="">Ainda não sei</option>
          <option value="1">Um</option>
          <option value="2">Gêmeos</option>
          <option value="3">Trigêmeos ou mais</option>
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="risco-mes">Em que mês da gravidez você começou o pré-natal?</label>
        <select id="risco-mes" className="form-control" value={valores.mes_inicio_prenatal}
          onChange={(e) => onChange('mes_inicio_prenatal', e.target.value)}>
          <option value="">Ainda não comecei ou não sei</option>
          {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((m) => (
            <option key={m} value={m}>{m}º mês</option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="risco-uf">Estado onde você mora</label>
        <select id="risco-uf" className="form-control" value={valores.uf_residencia}
          onChange={(e) => onChange('uf_residencia', e.target.value)}>
          <option value="">Prefiro não informar</option>
          {UFS.map(([codigo, nome]) => (
            <option key={codigo} value={codigo}>{nome}</option>
          ))}
        </select>
      </div>

      <p className="text-muted" style={{ fontSize: '0.8rem', margin: '4px 0 8px' }}>
        Sua saúde antes desta gravidez. São os fatores que mais mudam o cuidado no pré-natal.
      </p>
      <SimNao id="risco-pe" rotulo="Teve pré-eclâmpsia em outra gravidez?"
        valor={valores.pre_eclampsia_previa} onChange={muda('pre_eclampsia_previa')} />
      <SimNao id="risco-has" rotulo="Tem pressão alta desde antes desta gravidez?"
        valor={valores.hipertensao_cronica} onChange={muda('hipertensao_cronica')} />
      <SimNao id="risco-dm" rotulo="Tem diabetes desde antes desta gravidez?"
        valor={valores.diabetes_previo} onChange={muda('diabetes_previo')} />
      <SimNao id="risco-familia-pe" rotulo="Sua mãe ou irmã teve pré-eclâmpsia?"
        valor={valores.historico_familiar_pe} onChange={muda('historico_familiar_pe')} />
      <SimNao id="risco-familia-dm" rotulo="Alguém da família (pais, irmãos ou avós) tem diabetes?"
        valor={valores.historico_familiar_dm} onChange={muda('historico_familiar_dm')} />
    </div>
  );
}
