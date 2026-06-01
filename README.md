# Vectra Health

**Plataforma inteligente de prevenção epidemiológica com dados espaciais, machine learning e LLM Agent.**

> Antecipe surtos de dengue, zika, chikungunya e malária antes do colapso do sistema de saúde.

---

## 🎯 Visão Geral

O Vectra Health transforma dados climáticos, epidemiológicos e espaciais em **decisões preventivas de saúde pública**. Em vez de reagir quando os hospitais já estão sobrecarregados, a plataforma identifica regiões em risco **antes** do agravamento do cenário.

### Fluxo da solução

```
Dados espaciais + Epidemiológicos
        ↓
Pré-processamento e integração
        ↓
Feature Engineering (lags, anomalias, índices climáticos)
        ↓
Modelo supervisionado de risco (Random Forest / XGBoost)
        ↓
Explicabilidade (feature importance, ROC, matriz de confusão)
        ↓
API FastAPI
        ↓
LLM Agent com Human-in-the-Loop
        ↓
Dashboard React para tomada de decisão
```

---

## 📁 Estrutura do Projeto

```
vectra-health/
├── src/                          # Código-fonte Python
│   ├── config.py                 # Configuração central e caminhos
│   ├── data/                     # Módulos de coleta e pré-processamento
│   │   ├── collect_data.py       # Orquestrador de coleta
│   │   ├── fetch_infodengue.py   # InfoDengue API
│   │   ├── fetch_nasa_power.py   # NASA POWER API
│   │   ├── fetch_ibge.py         # IBGE SIDRA
│   │   ├── fetch_datasus.py      # DataSUS/CNES
│   │   ├── fetch_geodata.py      # geobr (GeoJSON)
│   │   └── preprocess_and_integrate.py
│   ├── features/                 # Feature engineering
│   │   ├── build_features.py     # Orquestrador
│   │   ├── epidemiological_features.py
│   │   ├── climate_features.py
│   │   └── target_definition.py
│   ├── models/                   # Machine learning
│   │   ├── train_models.py       # Orquestrador de treino
│   │   ├── train_baseline.py     # Logistic Regression
│   │   ├── train_random_forest.py
│   │   ├── train_xgboost.py
│   │   ├── evaluate.py
│   │   └── predict.py
│   ├── visualization/            # Visualizações e relatórios
│   │   ├── generate_reports.py
│   │   ├── plot_confusion_matrix.py
│   │   ├── plot_feature_importance.py
│   │   ├── plot_risk_map.py
│   │   └── dashboard_mock_data.py
│   └── utils/                    # Utilitários reutilizáveis
│       ├── io_utils.py
│       ├── date_utils.py
│       └── geo_utils.py
├── api/                          # API FastAPI
│   ├── main.py                   # Ponto de entrada
│   ├── routers/                  # Endpoints
│   │   ├── risk.py               # /risk/*, /predict, /agent/recommendation
│   │   ├── municipalities.py     # /municipalities
│   │   └── agent.py              # /llm-agent/*
│   ├── services/                 # Lógica de negócio
│   │   ├── prediction_service.py
│   │   ├── geodata_service.py
│   │   └── llm_agent_service.py
│   └── schemas/                  # Schemas Pydantic
│       ├── risk_schema.py
│       └── agent_schema.py
├── frontend/                     # Dashboard React + Vite
│   └── src/
│       ├── App.jsx
│       ├── api/vectraApi.js
│       ├── components/           # Componentes reutilizáveis
│       └── pages/                # Páginas do dashboard
├── notebooks/                    # Jupyter Notebooks do pipeline
├── data/                         # Dados (raw, interim, processed)
├── models/                       # Modelos treinados (.pkl, .json)
├── reports/                      # Figuras, tabelas e sumários
└── docs/                         # Documentação técnica
```

---

## 🚀 Como executar

### Pré-requisitos

- Python 3.10+
- Node.js 18+

### 1. Instalar dependências Python

```bash
pip install -r requirements.txt
```

### 2. Coletar dados

```bash
python -m src.data.collect_data
```

### 3. Pré-processar e integrar

```bash
python -m src.data.preprocess_and_integrate
```

### 4. Feature engineering

```bash
python -m src.features.build_features
```

### 5. Treinar modelos

```bash
python -m src.models.train_models
```

### 6. Iniciar a API

```bash
uvicorn api.main:app --reload
```

A API estará disponível em: http://127.0.0.1:8000
Documentação: http://127.0.0.1:8000/docs

### 7. Iniciar o frontend

```bash
cd frontend
npm install
npm run dev
```

O dashboard estará em: http://localhost:5173

---

## 📊 Fontes de dados

| Fonte | Dados | Endpoint |
|-------|-------|----------|
| InfoDengue | Casos semanais de dengue por município | `info.dengue.mat.br/api/alertcity` |
| NASA POWER | Variáveis climáticas (temperatura, chuva, umidade) | `power.larc.nasa.gov/api` |
| IBGE SIDRA | Estimativas populacionais municipais | `apisidra.ibge.gov.br` |
| geobr | Malha municipal geoespacial | Pacote R/Python |
| DataSUS/CNES | Capacidade hospitalar (leitos, UBS) | CSV manual |

---

## 🤖 Modelos

| Modelo | Tipo | Propósito |
|--------|------|-----------|
| Logistic Regression | Baseline | Interpretabilidade e referência |
| Random Forest | Principal | Robustez e feature importance |
| XGBoost | Avançado | Desempenho preditivo máximo |

**Métrica prioritária: Recall** — Em saúde pública, falsos negativos (regiões em risco não sinalizadas) são mais graves que falsos positivos.

---

## 🔒 LLM Agent com Human-in-the-Loop

Toda recomendação operacional gerada pelo agente começa com status `pending_review` e **requer aprovação humana** antes de qualquer execução. O gestor pode:

- ✅ Aprovar o protocolo
- 🔄 Solicitar revisão
- ❌ Rejeitar

---

## 🌐 Endpoints da API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/health` | Status da API |
| `GET` | `/municipalities` | Lista de municípios |
| `GET` | `/risk/latest` | Snapshot de risco mais recente |
| `GET` | `/risk/{geocode}` | Risco de um município |
| `POST` | `/predict` | Predição do modelo |
| `POST` | `/agent/recommendation` | Recomendação determinística |
| `POST` | `/llm-agent/protocol` | Protocolo do LLM Agent |
| `POST` | `/llm-agent/review` | Revisão humana |
| `GET` | `/llm-agent/protocols` | Lista de protocolos |
| `GET` | `/llm-agent/reviews` | Lista de revisões |

---

## 📄 Licença

Projeto acadêmico — Global Solution FIAP 2025.
