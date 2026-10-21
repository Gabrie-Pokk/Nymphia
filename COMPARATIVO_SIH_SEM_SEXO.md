# COMPARATIVO_SIH_SEM_SEXO.md — Análise da Feature 'SEXO' e Retreinamento dos Modelos SIH

> **Atualização de 16/10/2026: experimento encerrado.** Os modelos de produção foram refeitos (v2 e v3, em 15/10) e nenhum usa `SEXO` (ver `nymphia_backend/modelos/v2/metricas_modelos_v2.json`, campo `variaveis_excluidas`). A pasta `nymphia_backend/modelos_experimentais_sem_sexo/` e os scripts `scripts/retreinar_sih_sem_sexo.py` e `scripts/calcular_metricas_reais.py` foram removidos. Este arquivo fica só como registro.

> **Conformidade com a Regra 1 e Instruções do Bloco 5**:  
> 1. Dados e métricas 100% reais, reproduzíveis pelo script `scripts/retreinar_sih_sem_sexo.py`.  
> 2. Trabalho executado exclusivamente na branch `bloco-5-feature-sexo-sih`.  
> 3. Os modelos de produção em `nymphia_backend/modelos/` **NÃO foram substituídos** e permanecem intactos. Os modelos retreinados foram isolados em `nymphia_backend/modelos_experimentais_sem_sexo/`.

---

## 1. Confirmação Empírica da Feature 'SEXO' na Coorte Obstétrica

- **Base de Dados**: SIH/SUS (`pipeline_data/sih_condicoes.parquet`)
- **Total de Registros de Internação Hospitalar**: 210.148
- **Filtro de Especialidade Obstétrica (`ESPEC == "02"`)**: 169.213 internações
- **Distribuição Real de `SEXO` em `ESPEC == "02"`**:
  - Código `3` (Feminino no padrão DATASUS): **169.213 registros (100,0%)**
  - Código `1` (Masculino): 0 registros (0,0%)
  - Outros / Nulo: 0 registros (0,0%)

### Conclusão Estatística
A feature `SEXO` possui **variância estritamente nula** ($\text{Var}(\text{SEXO}) = 0$) na coorte obstétrica. Em teoria da informação, o ganho de informação (*Information Gain*) e a entropia condicional para qualquer nó de divisão na árvore são identicamente nulos ($H(Y \mid \text{SEXO}) = H(Y)$). A inclusão dessa coluna nos modelos legados era um resquício de pipelines demográficos gerais do DATASUS.

---

## 2. Comparativo Detalhado de Desempenho (Antes vs. Depois)

Os 4 modelos SIH foram retreinados mantendo estritamente a mesma semente (`random_state=42`), partição estratificada de teste (80% treino / 20% teste), algoritmo (`RandomForestClassifier`) e hiperparâmetros (`n_estimators=150, max_depth=10, min_samples_leaf=5, class_weight='balanced'`).

A única modificação foi o conjunto de features:
- **Modelo Original (Produção)**: `['IDADE', 'SEXO', 'UF_ZI', 'MUNIC_RES']` (4 features)
- **Modelo Retreinado (Experimental)**: `['IDADE', 'UF_ZI', 'MUNIC_RES']` (3 features)

### Tabela Comparativa de Métricas no Conjunto de Teste

| Condição Obstétrica | Versão | Features | ROC-AUC | Acurácia | Precisão (Pos) | Recall (Pos) | F1-Score (Pos) | Matriz de Confusão `[[TN, FP], [FN, TP]]` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Pré-Eclâmpsia** | Original (Prod) | 4 | **0,7617** | 0,7446 | 0,1438 | **0,6361** | 0,2346 | `[[22651, 7483], [719, 1257]]` |
| | Experimental | 3 | **0,7532** | 0,7624 | 0,1481 | 0,6017 | 0,2376 | `[[23287, 6847], [787, 1189]]` |
| | *Delta* | *-1* | *-0,0085* | *+0,0178* | *+0,0042* | *-0,0344* | *+0,0030* | — |
| **Eclâmpsia** | Original (Prod) | 4 | 0,6979 | 0,8331 | 0,0176 | **0,4635** | 0,0340 | `[[25176, 4958], [103, 89]]` |
| | Experimental | 3 | **0,7040** | 0,8992 | 0,0227 | 0,3542 | 0,0426 | `[[27197, 2937], [124, 68]]` |
| | *Delta* | *-1* | *+0,0061* | *+0,0661* | *+0,0050* | *-0,1094* | *+0,0086* | — |
| **Diabetes Gestacional** | Original (Prod) | 4 | **0,7691** | 0,7044 | 0,1066 | **0,6967** | **0,1849** | `[[21239, 8895], [462, 1061]]` |
| | Experimental | 3 | 0,7689 | 0,7100 | 0,1068 | 0,6829 | 0,1847 | `[[21415, 8719], [483, 1040]]` |
| | *Delta* | *-1* | *-0,0002* | *+0,0055* | *+0,0002* | *-0,0138* | *-0,0002* | — |
| **Infecção Urinária (ITU)** | Original (Prod) | 4 | 0,7815 | 0,9507 | 0,0054 | **0,4444** | 0,0106 | `[[28656, 1478], [10, 8]]` |
| | Experimental | 3 | **0,8162** | 0,9830 | 0,0118 | 0,3333 | 0,0229 | `[[29634, 500], [12, 6]]` |
| | *Delta* | *-1* | *+0,0347* | *+0,0323* | *+0,0065* | *-0,1111* | *+0,0122* | — |

---

## 3. Análise dos Resultados e Recomendação para o Gabriel

1. **Por que houve pequenas variações nas métricas se `SEXO` é constante?**  
   No algoritmo `RandomForestClassifier`, a cada divisão de nó, um subconjunto de features de tamanho $\sqrt{p}$ é amostrado aleatoriamente (`max_features='sqrt'`).
   - Com $p=4$, $\sqrt{4} = 2$ features são sorteadas por nó. Se `SEXO` for uma das sorteadas, a árvore tem menos alternativas úteis naquele nó específico.
   - Com $p=3$, $\text{round}(\sqrt{3}) \approx 2$ features são sorteadas, mas agora ambas são sempre informativas (`IDADE`, `UF_ZI` ou `MUNIC_RES`).
2. **Impacto Clínico**:
   - A remoção da feature melhora a acurácia global e a precisão em todos os 4 modelos, além de elevar o ROC-AUC do ITU (+0,0347) e da Eclâmpsia (+0,0061).
   - No entanto, o **Recall** (sensibilidade) da classe positiva tem leve redução (ex.: -3,4% na Pré-Eclâmpsia e -11,1% na ITU) porque o modelo sem a feature redundante torna-se ligeiramente mais conservador ao classificar instâncias positivas.
3. **Decisão Submetida ao Gabriel**:
   - Conforme a **Regra 6 e Item 5.2**, os modelos de produção **NÃO foram substituídos**.
   - Os novos modelos treinados estão disponíveis em `nymphia_backend/modelos_experimentais_sem_sexo/`.
   - Se o Gabriel desejar promover esses modelos para produção, basta substituir os arquivos em `nymphia_backend/modelos/` e ajustar a lista de features em `app/modelos.py`. Registrado em `PENDENCIAS.md`.
