# Métricas reais dos modelos de risco (versão 2)

Gerado a partir de `nymphia_backend/modelos/metricas_modelos_v2.json` (treino de 2026-10-15 17:12, scikit-learn 1.7.2).
Todos os números abaixo saem desse arquivo, que o script `scripts/treinar_modelos_v2.py` escreve ao treinar. Nada foi arredondado à mão nem estimado.

## O que mudou da versão 1 para a 2

A versão 1 (julho de 2026) usava dados que só existem depois do parto: Apgar, peso ao nascer, semanas no parto, tipo e local do parto e número total de consultas. No app, sem esses dados, o servidor preenchia valores inventados (Apgar 9 e 10, 3.200 g, São Paulo para todo mundo), e o resultado dependia quase só da idade. As métricas da versão 1 (AUC de 0,68 a 0,78) não valiam para o uso real no pré-natal: nos modelos do SINASC foram medidas com os dados do parto, e nos do SIH boa parte do ganho vinha do código de estado e de município, que reflete diferenças na forma de registrar a internação. Os arquivos `rf_*.joblib` e `isolation_forest_anomalia.joblib` foram retirados do repositório.

Regras da versão 2:

1. Só entra o que se sabe durante a gestação e que o app pergunta.
2. Dado não informado fica desconhecido; o app não inventa valor.
3. Treino, calibração e teste em partes separadas (60%, 20% e 20%, estratificadas, semente 42).
4. Probabilidade calibrada (regressão isotônica sobre a parte de calibração).
5. Ponto de corte escolhido para pegar 80% dos casos (prioridade: não deixar passar casos).
6. Comparação com um modelo só com a idade, para mostrar o que as outras variáveis acrescentam.

## Resultado no conjunto de teste

| Condição | Base | Variáveis | Teste (casos) | Prevalência | AUC-ROC | AUC só com idade | AUC-PR | Brier | Erro de calibração |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Prematuridade ou baixo peso (bem-estar fetal) | SINASC | idade, estado_civil, escolaridade, gestacoes_anteriores, partos_normais, partos_cesareos, perdas_anteriores, fetos, mes_inicio_prenatal | 766.074 (119.122) | 15,55% | 0,614 | 0,539 | 0,2948 | 0,1222 | 0,0010 |
| Malformação congênita | SINASC | idade, estado_civil, escolaridade, gestacoes_anteriores, partos_normais, partos_cesareos, perdas_anteriores, fetos, mes_inicio_prenatal | 754.443 (6.591) | 0,87% | 0,565 | 0,544 | 0,0116 | 0,0086 | 0,0004 |
| Pré-eclâmpsia | SIH 2022 (caso-controle) | idade, regiao | 32.109 (1.976) | 6,15% | 0,654 | 0,608 | 0,1050 | 0,0567 | 0,0044 |
| Eclâmpsia | SIH 2022 (caso-controle) | idade, regiao | 30.325 (192) | 0,63% | 0,565 | 0,556 | 0,0079 | 0,0063 | 0,0011 |
| Diabetes gestacional | SIH 2022 (caso-controle) | idade, regiao | 30.949 (816) | 2,64% | 0,683 | 0,688 | 0,0494 | 0,0254 | 0,0019 |
| Infecção urinária (ITU) | SIH 2022 (caso-controle) | idade, regiao | 30.151 (18) | 0,06% | 0,584 | 0,441 | 0,0008 | 0,0006 | 0,0004 |

## No ponto de corte de 80% de sensibilidade

| Condição | Limiar | Sensibilidade | Especificidade | Valor preditivo positivo | Valor preditivo negativo | Fração sinalizada |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Prematuridade ou baixo peso (bem-estar fetal) | 0,1232 | 80,2% | 29,5% | 17,33% | 89,02% | 72,0% |
| Malformação congênita | 0,0076 | 82,9% | 22,6% | 0,93% | 99,34% | 77,5% |
| Pré-eclâmpsia | 0,0459 | 80,3% | 40,3% | 8,11% | 96,90% | 60,9% |
| Eclâmpsia | 0,0053 | 83,9% | 23,4% | 0,69% | 99,56% | 76,7% |
| Diabetes gestacional | 0,0152 | 90,0% | 30,3% | 3,38% | 99,11% | 70,2% |
| Infecção urinária (ITU) | 0,0007 | 94,4% | 25,8% | 0,08% | 99,99% | 74,2% |

Fração sinalizada: parte das gestantes que ficaria acima do limiar. Com sensibilidade de 80%, os modelos sinalizam de 61% a 77% das gestantes, o que mostra o tamanho da limitação: com o que se sabe no começo do pré-natal, estes dados separam pouco quem vai ter a condição de quem não vai.

## Como ler

- **Prematuridade ou baixo peso (bem-estar fetal)**: AUC 0,614 contra 0,539 só com a idade. É o modelo mais útil, sobretudo por causa do número de bebês (gêmeos têm muito mais prematuridade) e do mês de início do pré-natal. A probabilidade é calibrada: nos dez grupos de risco, a média prevista e a observada diferem no máximo 0,0017.
- **Malformação congênita**: AUC 0,565, pouco acima do acaso (0,5). Com dados do começo da gestação, o modelo quase não distingue; a estimativa fica perto da média (0,87%). Ultrassom morfológico e exames são o caminho, não este número.
- **Pré-eclâmpsia**: AUC 0,654 com idade e região (só idade: 0,608). O app mostra quantas vezes a média, não porcentagem, porque o SIH é um desenho de caso-controle (internações pela condição contra partos normais) e não dá a frequência real na população. Os fatores clínicos perguntados no cadastro (pré-eclâmpsia anterior, pressão alta e diabetes de antes da gravidez, gêmeos, primeira gestação, IMC, casos na família) pesam mais e aparecem à parte, com o risco relativo publicado.
- **Eclâmpsia**: AUC 0,565 (só idade: 0,556), com 192 casos no teste. Na prática é um efeito de idade.
- **Diabetes gestacional**: AUC 0,683, igual ou um pouco abaixo do modelo só com idade (0,688): a região não acrescenta. O rastreio de verdade é a glicemia de jejum e a curva glicêmica.
- **Infecção urinária (ITU)**: desligado no app. Só 92 casos (N39 em leito obstétrico). Infecção urinária na gestação é registrada como O23, que não veio nesta base. Não usar até treinar com O23. No teste havia 18 casos.

## Variáveis excluídas e por quê

- **SINASC, APGAR1, APGAR5, PESO, SEMAGESTAC, GESTACAO**: medidos no parto; são o próprio desfecho.
- **SINASC, PARTO, LOCNASC, CODESTAB e leitos do CNES**: dizem como e onde o bebê nasceu, só se sabe no parto.
- **SINASC, CONSULTAS**: número total de consultas; quem nasce antes tem menos consultas, o modelo aprenderia a resposta.
- **SIH, SEXO**: sempre feminino em leito obstétrico; não informa nada.
- **SIH, MUNIC_RES como número**: código de município tratado como quantidade não tem sentido; virou estado (categoria).
- **SIH, diagnósticos secundários**: preenchidos em menos de 1% das internações; não sustentam um modelo.
- **SIH, estado (UF) em vez de região**: subia a AUC (pré-eclâmpsia 0,66 para 0,70; diabetes 0,68 para 0,75), mas o ganho vinha de diferenças entre estados na forma de registrar a internação; a região guarda a diferença real, como a pré-eclâmpsia mais frequente no Nordeste.
- **SIH, raça/cor**: o ganho vinha de a raça faltar mais nos casos (30%) do que nos controles (21%), um efeito do registro do hospital; entre os registros preenchidos não havia diferença.

## Hiperparâmetros

- Classificador: `HistGradientBoostingClassifier` (scikit-learn), `max_iter=400`, `learning_rate=0.06`, `max_leaf_nodes=31`, `l2_regularization=1.0`, `early_stopping=True` (10% de validação, 20 iterações sem melhora), variáveis categóricas nativas, semente 42. `min_samples_leaf=200` nos modelos do SINASC e 50 nos do SIH.
- Calibração: `CalibratedClassifierCV(FrozenEstimator(modelo), method="isotonic")`, ajustada só na parte de calibração.
- Comparação: uma floresta aleatória (150 árvores, profundidade 10) treinada nas mesmas variáveis teve AUC de validação igual ou menor em todos os casos, exceto ITU (que está desligado).
- Atipicidade: `IsolationForest` com 200 árvores e contaminação de 5%, nas mesmas variáveis do SINASC. Serve só para avisar que o cadastro foge do comum (por exemplo, um erro de digitação); não é risco.

## Como reproduzir

```bash
python scripts/treinar_modelos_v2.py        # todos os modelos
python scripts/treinar_modelos_v2.py sih    # só os do SIH
```

Os scripts antigos `scripts/calcular_metricas_reais.py` e `scripts/retreinar_sih_sem_sexo.py` dependem dos modelos da versão 1, que saíram do repositório; ficam só como histórico.

## Respostas curtas para a banca

- **Quantas camadas e neurônios?** Nenhum: os modelos são árvores de decisão com reforço de gradiente (gradient boosting), não redes neurais.
- **Por que a AUC é baixa?** Porque agora o modelo só usa o que se sabe no pré-natal. A versão 1 tinha AUC maior porque, no SINASC, via dados do parto (que não existem quando a gestante usa o app) e, no SIH, usava estado e município, que medem mais a forma de registrar do que o risco.
- **O app dá diagnóstico?** Não. Mostra estimativas populacionais e os fatores clínicos com efeito publicado, e quem decide é a equipe de saúde.
- **E o BERTimbau?** Não roda em produção (falta memória no servidor gratuito) e não foi validado clinicamente. A triagem emocional do app passou a ser a Escala de Edimburgo (EPDS), uma escala validada no Brasil, e o texto livre do check-in passa pelas regras de sinais de alerta (palavras-chave só escolhem a frase de acolhimento).
