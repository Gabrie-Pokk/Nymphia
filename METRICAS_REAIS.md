# Métricas reais dos modelos de risco (versões 2 e 3)

Gerado a partir de `nymphia_backend/modelos/metricas_modelos_v3.json` (treino de 2026-10-15 22:07), `nymphia_backend/modelos/v2/metricas_modelos_v2.json` (treino de 2026-10-15 17:12) e `pipeline_data/base_sintetica_v3_parametros.json`. Nada foi arredondado à mão nem estimado.

## O que o app usa hoje

| Condição | Versão no app | AUC em dados reais (v3) | AUC da v2 nos mesmos dados | Dados reais usados |
| :--- | :--- | :--- | :--- | :--- |
| Prematuridade ou baixo peso (bem-estar fetal) | v3 (fatores por simulação) | 0,606 | 0,611 | SINASC, fora do treino (23.896 casos) |
| Pré-eclâmpsia | v3 (fatores por simulação) | 0,655 | 0,654 | SIH 2022, parte de teste (1.976 casos) |
| Eclâmpsia | v3 (fatores por simulação) | 0,559 | 0,565 | SIH 2022, parte de teste (192 casos) |
| Diabetes gestacional | v3 (fatores por simulação) | 0,684 | 0,683 | SIH 2022, parte de teste (816 casos) |
| Malformação congênita | v3 (só dados reais) | 0,563 | 0,565 | SINASC, fora do treino (6.591 casos) |
| Infecção urinária (ITU) | desligado | - | - | Só 92 casos (N39 em leito obstétrico). Infecção urinária na gestação é registrada como O23, que não veio nesta base. Não usar até treinar com O23. |

Nos dados reais, os fatores clínicos ficam desconhecidos (o DATASUS não os registra). A v3 ficou com o mesmo desempenho da v2: a diferença máxima foi de 0,007 de AUC, para os dois lados. Ou seja, a base sintética não fez o modelo acertar mais em gestantes reais; ela faz a estimativa responder aos fatores que a gestante informa, na medida mostrada pelos estudos.

## Versão 3: base sintética

### Por que existe

Os fatores de risco mais fortes da gestação (pré-eclâmpsia anterior, pressão alta e diabetes de antes da gravidez, IMC, casos na família) não existem no SINASC nem no SIH. Na v2 eles apareciam só numa lista à parte. Na v3, uma base sintética de 1.200.000 gestantes fictícias junta esses fatores ao perfil real, e o modelo passa a usá-los.

### Como a base é montada

1. **Perfil real.** Cada gestante fictícia parte de um registro real do SINASC (idade, estado civil, escolaridade, gestações, partos, perdas, número de bebês, mês de início do pré-natal). 20% dos registros ficaram de fora, reservados para a conferência em dados reais.
2. **Fatores sorteados** com prevalências brasileiras publicadas.
3. **Desfechos.** Prematuridade/baixo peso usa o desfecho REAL do registro; os fatores são sorteados já sabendo o desfecho, pela regra de Bayes, de modo que o risco real por perfil não muda. Pré-eclâmpsia e diabetes gestacional são simulados: o risco por idade e região vem do SIH real, a média vem de fontes brasileiras e cada fator entra com o efeito publicado. Eclâmpsia é a pré-eclâmpsia vezes a fração de eclâmpsia por idade e região no SIH (10.839 internações, 8,8% de eclâmpsia).

### Prevalências usadas

| Fator | Valor | Fonte |
| :--- | :--- | :--- |
| IMC antes da gravidez | baixo peso 10%, adequado 61%, sobrepeso 18%, obesidade 11% | Marano D, Gama SGN, Domingues RMSM, Souza Júnior PRB. Prevalência e fatores associados aos desvios nutricionais em mulheres na fase pré-gestacional em dois municípios do Estado do Rio de Janeiro. Rev Bras Epidemiol 2014;17(1):45-58 (gestantes do SUS no 1º trimestre, n = 1.535, 2007-2008) |
| Pressão alta antes da gravidez | 7,2% (autorrelato) | Marano D, Gama SGN, Domingues RMSM, Souza Júnior PRB. Prevalência e fatores associados aos desvios nutricionais em mulheres na fase pré-gestacional em dois municípios do Estado do Rio de Janeiro. Rev Bras Epidemiol 2014;17(1):45-58 (gestantes do SUS no 1º trimestre, n = 1.535, 2007-2008) |
| Diabetes antes da gravidez | 1,0% | Marano D, Gama SGN, Domingues RMSM, Souza Júnior PRB. Prevalência e fatores associados aos desvios nutricionais em mulheres na fase pré-gestacional em dois municípios do Estado do Rio de Janeiro. Rev Bras Epidemiol 2014;17(1):45-58 (gestantes do SUS no 1º trimestre, n = 1.535, 2007-2008) |
| Diabetes na família | 32% | Dode MASO, Santos IS. Fatores de risco para diabetes mellitus gestacional na coorte de nascimentos de Pelotas, 2004. Cad Saúde Pública 2009;25(5):1141-52 (n = 4.243) |
| Mãe com pré-eclâmpsia | 2,5% (o app aceita mãe ou irmã) | Ayorinde AA, Bhattacharya S. Inherited predisposition to preeclampsia: analysis of the Aberdeen intergenerational cohort. Pregnancy Hypertens 2017 |
| Pré-eclâmpsia anterior | 3% por gestação anterior com parto | Peraçoli JC et al. Pré-eclâmpsia/eclâmpsia. Protocolo FEBRASGO de Obstetrícia nº 8, 2018 (pré-eclâmpsia em 2% a 5% da população geral) |
| Pré-eclâmpsia (média) | 3% | Peraçoli JC et al. Pré-eclâmpsia/eclâmpsia. Protocolo FEBRASGO de Obstetrícia nº 8, 2018 (pré-eclâmpsia em 2% a 5% da população geral) |
| Diabetes gestacional (média) | 14% | Mocellin LP et al. Gestational diabetes mellitus prevalence in Brazil: a systematic review and meta-analysis. Cad Saúde Pública 2024;40(8):e00064919 |

### Efeito publicado e efeito que o modelo devolve

Conferência de construção: o modelo tem de devolver o efeito que entrou no gerador. Mediana entre gestantes, na escala de razão de chances.

| Condição | Fator | Publicado | No modelo | Fonte |
| :--- | :--- | :--- | :--- | :--- |
| Prematuridade ou baixo peso (bem-estar fetal) | pressão alta antes da gravidez | 3,53 | 3,49 | Bramham K et al |
| Prematuridade ou baixo peso (bem-estar fetal) | diabetes antes da gravidez | 3,48 | 3,54 | Yu L et al |
| Pré-eclâmpsia | pré-eclâmpsia anterior | 8,40 | 8,03 | Bartsch E et al |
| Pré-eclâmpsia | pressão alta antes da gravidez | 5,10 | 4,85 | Bartsch E et al |
| Pré-eclâmpsia | diabetes antes da gravidez | 3,70 | 3,40 | Bartsch E et al |
| Pré-eclâmpsia | IMC abaixo de 18,5 | 0,69 | 0,62 | Zhang Y et al |
| Pré-eclâmpsia | IMC de 25 a 29,9 | 1,70 | 1,54 | Zhang Y et al |
| Pré-eclâmpsia | IMC de 30 ou mais | 2,82 | 2,59 | Zhang Y et al |
| Pré-eclâmpsia | gêmeos | 2,93 | 2,80 | Duckitt K, Harrington D |
| Pré-eclâmpsia | mãe com pré-eclâmpsia | 2,90 | 2,86 | Duckitt K, Harrington D |
| Diabetes gestacional | IMC abaixo de 18,5 | 0,63 | 0,63 | Zhang Y et al |
| Diabetes gestacional | IMC de 25 a 29,9 | 2,20 | 2,21 | Zhang Y et al |
| Diabetes gestacional | IMC de 30 ou mais | 3,46 | 3,39 | Zhang Y et al |
| Diabetes gestacional | diabetes na família | 1,89 | 1,88 | Dode MASO, Santos IS |

Na prematuridade/baixo peso, o efeito da pressão alta é o RR de prematuridade de Bramham et al. (RR 2,7 de prematuridade convertido em OR com a base de 12,2% do estudo); o do diabetes é a razão de chances de prematuridade de Yu et al. Primeiro parto (2,91) e primeira gestação (0,75 no diabetes gestacional) também entram no gerador; ficam fora da tabela porque dependem do número de partos, que o modelo já recebe.

### Conferência em dados reais

- **Prematuridade/baixo peso**, em 153.067 registros do SINASC que nem a v2 nem a v3 viram: AUC 0,606 (v2: 0,611); probabilidade média prevista 15,2% para 15,6% observados; erro de calibração 0,0053. No ponto de 80% de sensibilidade: sensibilidade 83,8%, especificidade 24,1%.
- **"Não sei" de verdade.** Com tudo em branco menos a idade, a v3 prevê 15,6% de prematuridade/baixo peso (real: 15,6%); a v2 previa 10,8%. Na malformação, v3 0,83%, real 0,87%, v2 1,92%. A v2 lia o campo em branco como os registros incompletos do DATASUS, que têm outro perfil; a v3 aprendeu que "não sei" é a média de quem respondeu, porque no treino uma parte das respostas foi escondida de propósito.
- **Pré-eclâmpsia, eclâmpsia e diabetes gestacional**, na parte de teste do SIH (caso-controle, só idade e região): AUC 0,655, 0,559 e 0,684 (v2: 0,654, 0,565 e 0,683).

### Limites (estão também na tela de transparência)

- Fatores independentes entre si, exceto pré-eclâmpsia anterior, que depende do número de partos.
- Efeitos multiplicam a chance (odds); quem tem vários fatores pode ficar com risco superestimado.
- Em cada idade e região, o risco médio da base é igual ao dos dados reais.
- Malformação não recebe fatores nesta versão (sem fonte conferida).
- Os efeitos usados são, na maioria, riscos relativos sem ajuste mútuo. Quem tem um único fator e nenhum outro pode ficar com uma estimativa mais baixa do que a dos estudos (por exemplo, uma gestante de 30 anos que já teve parto, com IMC normal e só pressão alta crônica, fica com pré-eclâmpsia por volta de 4%). Por isso o nível mostrado na pré-eclâmpsia e na eclâmpsia nunca fica abaixo do critério das diretrizes: um fator alto já é risco alto; dois moderados, risco aumentado.
- A AUC na própria base sintética não foi calculada: ela mediria as regras que nós escrevemos, não o desempenho em gestantes reais. O único jeito de medir o efeito dos fatores em gestantes reais é com dados reais que tenham esses fatores registrados (dados do próprio app, com consentimento e aprovação de comitê de ética).

### Como refazer

```bash
python scripts/gerar_base_sintetica.py   # base sintética (semente fixa: sai igual)
python scripts/treinar_modelos_v3.py     # modelos v3 e metricas_modelos_v3.json
```

## Versão 2: só dados reais (referência)

A v2 continua guardada em `nymphia_backend/modelos/v2`. ITU e a atipicidade do perfil ainda vêm dela.

| Condição | Base | Teste (casos) | Prevalência | AUC-ROC | AUC só com idade | AUC-PR | Brier |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Prematuridade ou baixo peso (bem-estar fetal) | SINASC | 766.074 (119.122) | 15,55% | 0,614 | 0,539 | 0,2948 | 0,1222 |
| Malformação congênita | SINASC | 754.443 (6.591) | 0,87% | 0,565 | 0,544 | 0,0116 | 0,0086 |
| Pré-eclâmpsia | SIH 2022 (caso-controle) | 32.109 (1.976) | 6,15% | 0,654 | 0,608 | 0,1050 | 0,0567 |
| Eclâmpsia | SIH 2022 (caso-controle) | 30.325 (192) | 0,63% | 0,565 | 0,556 | 0,0079 | 0,0063 |
| Diabetes gestacional | SIH 2022 (caso-controle) | 30.949 (816) | 2,64% | 0,683 | 0,688 | 0,0494 | 0,0254 |
| Infecção urinária (ITU) | SIH 2022 (caso-controle) | 30.151 (18) | 0,06% | 0,584 | 0,441 | 0,0008 | 0,0006 |

A v1 (julho de 2026) usava dados que só existem depois do parto (Apgar, peso ao nascer, semanas no parto) e, no SIH, estado e município como número; o servidor ainda preenchia valores inventados quando faltava dado. As AUC da v1 (0,68 a 0,78) não valiam para o uso no pré-natal. Os arquivos da v1 saíram do repositório.

### Variáveis excluídas na v2 e por quê

- **SINASC, APGAR1, APGAR5, PESO, SEMAGESTAC, GESTACAO**: medidos no parto; são o próprio desfecho.
- **SINASC, PARTO, LOCNASC, CODESTAB e leitos do CNES**: dizem como e onde o bebê nasceu, só se sabe no parto.
- **SINASC, CONSULTAS**: número total de consultas; quem nasce antes tem menos consultas, o modelo aprenderia a resposta.
- **SIH, SEXO**: sempre feminino em leito obstétrico; não informa nada.
- **SIH, MUNIC_RES como número**: código de município tratado como quantidade não tem sentido; virou estado (categoria).
- **SIH, diagnósticos secundários**: preenchidos em menos de 1% das internações; não sustentam um modelo.
- **SIH, estado (UF) em vez de região**: subia a AUC (pré-eclâmpsia 0,66 para 0,70; diabetes 0,68 para 0,75), mas o ganho vinha de diferenças entre estados na forma de registrar a internação; a região guarda a diferença real, como a pré-eclâmpsia mais frequente no Nordeste.
- **SIH, raça/cor**: o ganho vinha de a raça faltar mais nos casos (30%) do que nos controles (21%), um efeito do registro do hospital; entre os registros preenchidos não havia diferença.

## Respostas curtas para a banca

- **Por que base sintética?** Porque os fatores mais fortes não estão no DATASUS. A base junta o perfil real com os efeitos publicados, e cada número tem fonte.
- **Ela melhorou a AUC?** Não, e não era para melhorar. Em dados reais a v3 tem o mesmo desempenho da v2; o ganho é a estimativa mudar quando a gestante informa, por exemplo, pressão alta antes da gravidez, na medida dos estudos.
- **Vocês publicam a AUC da base sintética?** Não. Ela mediria as nossas próprias regras.
- **Quantas camadas e neurônios?** Nenhum: são árvores de decisão com reforço de gradiente (gradient boosting), não redes neurais.
- **O app dá diagnóstico?** Não. Mostra estimativas populacionais e os fatores com efeito publicado; quem decide é a equipe de saúde.
- **E o BERTimbau?** Não roda em produção (falta memória no servidor gratuito) e não foi validado clinicamente. A triagem emocional do app passou a ser a Escala de Edimburgo (EPDS), validada no Brasil.
