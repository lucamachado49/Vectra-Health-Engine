# Model Card — Vectra Health

## Informações Gerais

| Atributo | Valor |
|----------|-------|
| **Nome** | Vectra Health Risk Classifier |
| **Versão** | 0.1.0 |
| **Tipo** | Classificação binária supervisionada |
| **Domínio** | Epidemiologia / Saúde Pública |
| **Target** | Risco de surto de dengue (binário: 0 / 1) |
| **Granularidade** | Município × Semana epidemiológica |
| **Período dos dados** | 2020–2025 |

---

## Modelos Implementados

### 1. Logistic Regression (baseline)
- **Propósito**: Modelo interpretável de referência
- **Pré-processamento**: Imputação mediana + StandardScaler
- **Hiperparâmetros**: `max_iter=2000`, `class_weight=balanced`
- **Arquivo salvo**: `models/baseline_logistic_regression.pkl`

### 2. Random Forest (principal)
- **Propósito**: Modelo robusto com feature importance nativa
- **Pré-processamento**: Imputação mediana (sem escala para árvores)
- **Hiperparâmetros**: `n_estimators=400`, `min_samples_leaf=2`, `class_weight=balanced_subsample`
- **Arquivo salvo**: `models/random_forest_classifier.pkl`

### 3. XGBoost (avançado, opcional)
- **Propósito**: Máximo desempenho preditivo
- **Pré-processamento**: Imputação mediana
- **Hiperparâmetros**: `n_estimators=300`, `max_depth=4`, `learning_rate=0.05`, `scale_pos_weight=auto`
- **Arquivo salvo**: `models/xgboost_classifier.pkl`

---

## Dados de Treinamento

### Fontes
- InfoDengue (casos semanais de dengue)
- NASA POWER (variáveis climáticas diárias → agrupadas semanalmente)
- IBGE SIDRA (população municipal)
- DataSUS/CNES (capacidade hospitalar)

### Divisão treino/teste
- **Método**: Divisão temporal (cronológica) — dados mais antigos para treino, mais recentes para teste
- **Proporção**: 75% treino / 25% teste
- **Motivo**: Evitar vazamento temporal em séries epidemiológicas

### Balanceamento de classes
- Surtos são eventos raros → classes desbalanceadas
- Tratamento: `class_weight=balanced` (LR) e `balanced_subsample` (RF)
- XGBoost: `scale_pos_weight` calculado automaticamente

---

## Features (Top 10 mais relevantes)

| Feature | Categoria | Descrição |
|---------|-----------|-----------|
| `casos_lag_1w` | Epidemiológica | Casos na semana anterior |
| `casos_lag_2w` | Epidemiológica | Casos há 2 semanas |
| `media_movel_4w` | Epidemiológica | Média móvel de 4 semanas |
| `chuva_acumulada_14d` | Climática | Chuva acumulada em 14 dias |
| `chuva_acumulada_7d` | Climática | Chuva acumulada em 7 dias |
| `temp_media_7d` | Climática | Temperatura média 7 dias |
| `umidade_media_7d` | Climática | Umidade média 7 dias |
| `incidencia_100k` | Epidemiológica | Incidência por 100k hab |
| `environmental_risk_score` | Composta | Score ambiental composto |
| `variacao_semanal` | Epidemiológica | Variação % semanal nos casos |

---

## Métricas de Avaliação

### Métrica prioritária: **Recall**

Em saúde pública, **não identificar uma região em risco** (falso negativo) é mais grave do que gerar um alerta desnecessário (falso positivo). Por isso, o Recall (sensibilidade) é a métrica principal.

### Métricas calculadas

| Métrica | Descrição |
|---------|-----------|
| Recall (Sensibilidade) | TP / (TP + FN) — **Prioritária** |
| Precisão | TP / (TP + FP) |
| F1-Score | Média harmônica entre Precisão e Recall |
| Acurácia | (TP + TN) / Total |
| ROC-AUC | Área sob a curva ROC |

### Artefatos gerados
- `reports/figures/confusion_matrix_*.png`
- `reports/figures/roc_curve_*.png`
- `reports/figures/feature_importance_*.png`
- `models/model_metrics.json`

---

## Limitações

1. **Cobertura geográfica**: Modelo treinado principalmente com municípios do Estado de SP. Generalização para outros estados pode exigir reajuste.

2. **Lag de dados**: InfoDengue tem latência de 1–2 semanas na consolidação dos casos. As previsões refletem essa limitação.

3. **Mudança climática**: O modelo usa padrões históricos 2020–2025. Eventos climáticos extremos fora desse padrão podem reduzir a acurácia.

4. **Outras doenças**: O modelo foi treinado para dengue. Aplicar a zika/chikungunya requer revalidação.

5. **Dados de capacidade hospitalar**: CNES é atualizado mensalmente. Leitos temporários em crises podem não estar refletidos.

---

## Uso Responsável

- Este modelo é uma **ferramenta de apoio à decisão**, não um substituto ao julgamento especializado.
- Todas as ações operacionais devem passar por **aprovação humana** (Human-in-the-Loop).
- Os outputs devem ser interpretados por **profissionais de saúde pública**.
- **Não utilize** as predições para comunicação direta ao público sem validação especializada.

---

## Contato e Manutenção

Projeto acadêmico — Global Solution FIAP 2025.
Para dúvidas técnicas, consulte a documentação em `docs/` e os notebooks em `notebooks/`.
