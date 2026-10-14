# METRICAS_REAIS.md — Relatório de Métricas e Hiperparâmetros dos Modelos Nymphia

> **Aviso de Conformidade Rigorosa (Regra Inviolável 1)**:  
> Nenhum número contido neste documento foi estimado, arredondado arbitrariamente ou inventado. Todos os hiperparâmetros foram inspecionados diretamente dos arquivos de modelo binários (`.joblib`, `config.json` e `model.safetensors`), e todas as métricas foram calculadas/reproduzidas sobre os conjuntos de teste reais a partir dos dados do DATASUS (SINASC e SIH).

---

## 1. Resumo Executivo das Métricas Reais de Produção

Todos os modelos supervisionados foram avaliados sobre partição de teste estratificada (20% dos dados, `random_state=42`), mantendo fidelidade absoluta ao protocolo original de treino.

| Condição / Modelo | Arquivo Joblib | Amostras Teste (Neg / Pos) | Prevalência Positiva | Acurácia | Precisão (Pos) | Recall (Pos) | F1-Score (Pos) | F1 Macro | F1 Ponderado | ROC-AUC | Matriz de Confusão `[[TN, FP], [FN, TP]]` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Pré-Eclâmpsia** | `rf_pre_eclampsia.joblib` | 32.110 (30.134 / 1.976) | 6,15% | **0,7446** | 0,1438 | 0,6361 | 0,2346 | 0,5407 | 0,8090 | **0,7617** | `[[22651, 7483], [719, 1257]]` |
| **Eclâmpsia** | `rf_eclampsia.joblib` | 30.326 (30.134 / 192) | 0,63% | **0,8331** | 0,0176 | 0,4635 | 0,0340 | 0,4713 | 0,9031 | **0,6979** | `[[25176, 4958], [103, 89]]` |
| **Diabetes Gestacional** | `rf_diabetes_gestacional.joblib` | 31.657 (30.134 / 1.523) | 4,81% | **0,7044** | 0,1066 | 0,6967 | 0,1849 | 0,5022 | 0,7890 | **0,7691** | `[[21239, 8895], [462, 1061]]` |
| **Infecção Urinária (ITU)** | `rf_itu.joblib` | 30.152 (30.134 / 18) | 0,06% | **0,9507** | 0,0054 (0,01) | 0,4444 | 0,0106 | 0,4927 | 0,9741 | **0,7815** | `[[28656, 1478], [10, 8]]` |
| **Malformação Congênita** | `rf_malformacao.joblib` | 694.066 (687.934 / 6.132) | 0,88% | **0,8614** | 0,0252 | 0,3893 | 0,0473 | 0,4863 | 0,9175 | **0,6751** | `[[595515, 92419], [3745, 2387]]` |
| **Bem-Estar Fetal** | `rf_bem_estar_fetal.joblib` | 611.505 (513.404 / 98.101) | 16,04% | **0,7258** | 0,2967 | 0,5172 | 0,3771 | 0,6012 | 0,7539 | **0,6907** | `[[393137, 120267], [47368, 50733]]` |
| **Atipicidade Clínica** | `isolation_forest_anomalia.joblib` | 3.057.521 (Total base) | Não-supervisionado | — | — | — | — | — | — | **0,6137** | Detecção multivariada: Taxa de atipicidade em desfecho grave real = 19,4% vs 8,2% em controles saudáveis |

---

## 2. Proporção de Classes e Explicação do Desbalanceamento Extremo (Para a Banca)

### 2.1 Distribuição Amostral (Treino vs. Teste)

1. **Pré-Eclâmpsia (SIH)**:
   - Treino (80%): 128.437 amostras (120.533 normais, 7.904 casos [6,15%])
   - Teste (20%): 32.110 amostras (30.134 normais, 1.976 casos [6,15%])
2. **Eclâmpsia (SIH)**:
   - Treino (80%): 121.300 amostras (120.533 normais, 767 casos [0,63%])
   - Teste (20%): 30.326 amostras (30.134 normais, 192 casos [0,63%])
3. **Diabetes Gestacional (SIH)**:
   - Treino (80%): 126.625 amostras (120.533 normais, 6.092 casos [4,81%])
   - Teste (20%): 31.657 amostras (30.134 normais, 1.523 casos [4,81%])
4. **Infecção Urinária / ITU (SIH)**:
   - Treino (80%): 120.607 amostras (120.533 normais, 74 casos [0,06%])
   - Teste (20%): 30.152 amostras (30.134 normais, 18 casos [0,06%])
5. **Malformação Congênita (SINASC)**:
   - Treino (80%): 2.776.261 amostras (2.751.731 normais, 24.530 casos [0,88%])
   - Teste (20%): 694.066 amostras (687.934 normais, 6.132 casos [0,88%])
6. **Bem-Estar Fetal (SINASC + CNES)**:
   - Treino (80%): 2.446.020 amostras (2.053.616 sem risco, 392.404 com risco [16,04%])
   - Teste (20%): 611.505 amostras (513.404 sem risco, 98.101 com risco [16,04%])

### 2.2 Defesa Teórica e Clínica para a Banca: Por que a Precisão é Baixa?

Em triagem clínica populacional e epidemiológica, existe um clássico **trade-off entre Precisão e Sensibilidade (Recall)**:

$$\text{Precisão} = \frac{TP}{TP + FP}, \quad \text{Recall} = \frac{TP}{TP + FN}$$

1. **Efeito do Teorema de Bayes em Eventos Raros**: Quando a prevalência de uma condição em base hospitalar é ínfima (por exemplo, na ITU hospitalar com apenas 18 casos em 30.152 internações [0,06%]), mesmo um modelo com altíssima especificidade (95,1% — 28.656 verdadeiros negativos de 30.134) gerará uma quantidade absoluta de falsos positivos (1.478) superior aos verdadeiros positivos (8).
2. **Priorização Clínica Deliberada (Custo Assimétrico do Erro)**:
   - Em obstetrícia, um **Falso Negativo** (uma gestante com infecção urinária oculta ou pré-eclâmpsia iminente liberada sem alerta) pode resultar em choque séptico, trabalho de parto prematuro extremo ou morte materna.
   - Um **Falso Positivo** resulta apenas na recomendação de uma urocultura com antibiograma ou aferição pressórica ambulatorial — procedimento de baixo custo, não invasivo e seguro.
   - Por essa razão, todos os modelos foram configurados com `class_weight='balanced'`, instruindo as árvores a penalizarem pesadamente os erros na classe minoritária. O objetivo deliberado de design é maximizar o **Recall** (sensibilidade) e a área sob a curva ROC (**ROC-AUC**), aceitando uma precisão matemática baixa na classe positiva.

---

## 3. Hiperparâmetros Reais Extraídos dos Modelos

### 3.1 Modelos de Árvore (Random Forest e Isolation Forest)

Inspecionados via `model.get_params()` e atributos de treino:

| Modelo | Estimadores (`n_estimators`) | Profundidade Máx (`max_depth`) | Mínimo por Folha (`min_samples_leaf`) | Ponderação (`class_weight`) | Features de Entrada | Semente (`random_state`) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `rf_bem_estar_fetal.joblib` | 150 | 14 | 5 | `'balanced'` | 13 features demográficas, obstétricas e leitos SUS | 42 |
| `rf_malformacao.joblib` | 150 | 14 | 5 | `'balanced'` | 17 features do SINASC (Apgar, Peso, Consultas, etc.) | 42 |
| `rf_pre_eclampsia.joblib` | 150 | 10 | 5 | `'balanced'` | 4 features (`IDADE`, `SEXO`, `UF_ZI`, `MUNIC_RES`) | 42 |
| `rf_eclampsia.joblib` | 150 | 10 | 5 | `'balanced'` | 4 features (`IDADE`, `SEXO`, `UF_ZI`, `MUNIC_RES`) | 42 |
| `rf_diabetes_gestacional.joblib` | 150 | 10 | 5 | `'balanced'` | 4 features (`IDADE`, `SEXO`, `UF_ZI`, `MUNIC_RES`) | 42 |
| `rf_itu.joblib` | 150 | 10 | 5 | `'balanced'` | 4 features (`IDADE`, `SEXO`, `UF_ZI`, `MUNIC_RES`) | 42 |
| `isolation_forest_anomalia.joblib` | 200 | Não aplicável | Não aplicável | Não aplicável (Contamination: 0.1) | 13 features contínuas de sinais vitais | 42 |

### 3.2 Resposta Exata à Banca sobre "Camadas e Neurônios"

> **Pergunta típica de banca**: *"Quantas camadas e neurônios têm os seus modelos de Random Forest?"*  
> **Resposta técnica correta**:  
> *"Os seis modelos de predição clínica da Nymphia são baseados em **Ensembles de Árvores de Decisão (Random Forest)** e **Isolation Forest**, e não em Redes Neurais Artificiais. Portanto, os conceitos de 'camadas', 'neurônios' e funções de ativação contínuas não se aplicam a essas arquiteturas. O espaço dimensional é particionado por hiperplanos ortogonais orientados pelo critério de Gini com 150 estimadores e profundidade restrita a 10 ou 14 níveis para mitigar overfitting.  
> O conceito de camadas e neurônios aplica-se estritamente ao nosso módulo de Processamento de Linguagem Natural (**BERTimbau**), que possui **12 camadas de Transformer (Encoder)**, **768 dimensões de representação oculta (neurônios por camada)**, **12 cabeças de auto-atenção multi-head** e aproximadamente **108,9 milhões de parâmetros treináveis**."*

### 3.3 Hiperparâmetros do BERTimbau Fine-Tuned (`bertimbau_nymphia/modelo_final`)

Extraído de `config.json` e `model.safetensors`:
- **Arquitetura Base**: `BertForSequenceClassification` (`neuralmind/bert-base-portuguese-cased`)
- **Número de Camadas Ocultas (`num_hidden_layers`)**: 12
- **Dimensão Oculta (`hidden_size`)**: 768
- **Cabeças de Atenção (`num_attention_heads`)**: 12
- **Tamanho Intermediário Feed-Forward (`intermediate_size`)**: 3072
- **Vocabulário (`vocab_size`)**: 29.794 tokens
- **Comprimento Máximo de Sequência (`max_position_embeddings`)**: 512
- **Função de Ativação Oculta**: GELU
- **Tipo de Problema**: Classificação Multi-Label (`multi_label_classification`)
- **Número de Classes Clínico-Emocionais**: 6 (`ansiedade`, `tristeza_desanimo`, `estresse_sobrecarga`, `medo_inseguranca`, `bem_estar`, `sintoma_fisico`)
- **Total de Parâmetros**: **108.927.750** (108,93 milhões de parâmetros)

---

## 4. Resolução Definitiva do Conflito: Precisão do Modelo de ITU

- **Situação**: A documentação do sistema (`DOCUMENTACAO_SISTEMA_NYMPHIA.md`, Seção 5.1) citava precisão de 0,01 para o modelo de ITU, enquanto um arquivo preliminar (`metricas-modelos-completo.md`) marcava a precisão como "pendente".
- **Veredito Comprovado pelo Código e Dados**:  
  A documentação de 0,01 está **absolutamente correta** e foi confirmada pela execução real do conjunto de teste (`scripts/calcular_metricas_reais.py`) e pelo arquivo de log de treino (`pipeline_data/metricas_itu.txt`):
  
  $$\text{Precisão do ITU} = \frac{TP}{TP + FP} = \frac{8}{8 + 1478} = \frac{8}{1486} \approx 0,00538 \xrightarrow{\text{arredondamento 2 casas}} 0,01$$
  
  O arquivo preliminar estava incompleto simplesmente por atraso de transcrição do log de execução para o documento auxiliar. O valor real, confirmado matematicamente pela matriz de confusão `[[28656, 1478], [10, 8]]`, é **0,01**.

---

## 5. Como Reproduzir os Números

O script de reprodução integral está versionado em:
[`scripts/calcular_metricas_reais.py`](file:///c:/Users/famil/Documents/Nymphia/nymphia/scripts/calcular_metricas_reais.py)

Para reexecutar a qualquer momento no ambiente Python do projeto:
```bash
python scripts/calcular_metricas_reais.py
```
