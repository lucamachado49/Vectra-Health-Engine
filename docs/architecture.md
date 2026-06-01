# Arquitetura do Sistema — Vectra Health

## Visão Geral

O Vectra Health é uma plataforma de previsão epidemiológica composta por **5 camadas** que se integram em um pipeline end-to-end.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CAMADA DE DADOS                          │
│  InfoDengue  │  NASA POWER  │  IBGE SIDRA  │  geobr  │  CNES   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    CAMADA DE PROCESSAMENTO                       │
│         Coleta → Limpeza → Integração → Feature Engineering     │
│              src/data/ + src/features/ + src/utils/             │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                      CAMADA DE ML                               │
│     Logistic Regression │ Random Forest │ XGBoost               │
│              src/models/ + models/*.pkl                         │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                       CAMADA DE API                             │
│           FastAPI + LLM Agent + Human-in-the-Loop               │
│              api/main.py + api/routers/ + api/services/         │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    CAMADA DE INTERFACE                           │
│              Dashboard React + Vite + Recharts                  │
│                         frontend/src/                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Componentes Detalhados

### 1. Coleta de Dados (`src/data/`)

| Módulo | Responsabilidade |
|--------|-----------------|
| `collect_data.py` | Orquestrador de coleta |
| `fetch_infodengue.py` | InfoDengue AlertCity API |
| `fetch_nasa_power.py` | NASA POWER diário |
| `fetch_ibge.py` | IBGE SIDRA populações |
| `fetch_datasus.py` | DataSUS/CNES leitos |
| `fetch_geodata.py` | geobr malha municipal |
| `preprocess_and_integrate.py` | Limpeza e integração |

### 2. Feature Engineering (`src/features/`)

| Módulo | Features geradas |
|--------|-----------------|
| `epidemiological_features.py` | Lags de casos, média móvel, variação semanal, incidência |
| `climate_features.py` | Médias e acumulados climáticos, índice de receptividade |
| `target_definition.py` | `target_surto_binario`, `risco_surto_multiclasse` |
| `build_features.py` | Orquestrador + environmental_risk_score |

### 3. Modelos (`src/models/`)

| Módulo | Responsabilidade |
|--------|-----------------|
| `train_baseline.py` | Logistic Regression pipeline |
| `train_random_forest.py` | Random Forest pipeline |
| `train_xgboost.py` | XGBoost pipeline (opcional) |
| `evaluate.py` | Métricas, seleção do melhor modelo |
| `predict.py` | Inferência com modelo salvo |
| `train_models.py` | Orquestrador completo |

### 4. API (`api/`)

```
api/
├── main.py              ← Ponto de entrada, startup, /health
├── routers/
│   ├── risk.py          ← GET /risk/latest, GET /risk/{geocode}, POST /predict
│   ├── municipalities.py ← GET /municipalities
│   └── agent.py         ← POST /llm-agent/protocol, POST /llm-agent/review
├── services/
│   ├── prediction_service.py  ← VectraAPIService (modelo + dados)
│   ├── geodata_service.py     ← GeoJSON para o frontend
│   └── llm_agent_service.py  ← VectraLLMAgentService (LLM ou fallback)
└── schemas/
    ├── risk_schema.py         ← Schemas de risco e predição
    └── agent_schema.py        ← Schemas do agente e HITL
```

### 5. Frontend (`frontend/`)

```
frontend/src/
├── App.jsx              ← Layout raiz + Header
├── api/vectraApi.js     ← Cliente HTTP centralizado
├── components/
│   ├── RiskMap.jsx              ← Mapa conceitual de risco
│   ├── RiskScoreCard.jsx        ← MetricCard + MiniMetric
│   ├── AlertPanel.jsx           ← Ranking operacional
│   ├── FeatureImportanceChart.jsx ← Explicabilidade
│   ├── AgentRecommendation.jsx  ← Protocolo do agente
│   └── HumanApprovalModal.jsx   ← Botões de decisão
└── pages/
    ├── Dashboard.jsx            ← Página principal
    ├── MunicipalityDetail.jsx   ← Detalhes + tendência
    └── AgentCenter.jsx          ← LLM Agent + HITL
```

---

## Fluxo de Dados

```
1. raw/ → preprocess_and_integrate.py → interim/
2. interim/ → build_features.py → processed/
3. processed/ → train_models.py → models/*.pkl
4. models/*.pkl → API → /predict → JSON
5. processed/latest_risk_snapshot.csv → API → /risk/latest → Dashboard
6. /predict + /risk/latest → LLM Agent → Protocolo HITL → Gestor
```

---

## Decisões Arquiteturais

### Por que FastAPI?
- Performance assíncrona nativa
- Schemas automáticos com Pydantic
- Documentação OpenAPI automática

### Por que Random Forest como modelo principal?
- Interpretabilidade via feature importance
- Robusto a outliers epidemiológicos
- Não requer normalização dos dados
- Funciona bem com dados tabulares heterogêneos

### Por que Recall como métrica prioritária?
Em epidemiologia, **falso negativo é mais grave** que falso positivo:
- Um alarme falso = custo financeiro extra
- Um surto não detectado = colapso hospitalar

### Por que Human-in-the-Loop obrigatório?
Decisões de saúde pública têm **consequências diretas sobre vidas humanas**. Nenhum protocolo é executado sem aprovação explícita do gestor responsável.
