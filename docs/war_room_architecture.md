# Vectra Health War Room Architecture

## Execution Plan

1. Replace the static dashboard with a fullscreen geospatial command center.
2. Use Leaflet dark tiles as the operational surface.
3. Render risk points and computer-vision heatmaps directly over the map.
4. Expose floating panels for metrics, ranking, Copilot, causal timeline, HITL, and logistics graph.
5. Serve advanced context through FastAPI endpoints instead of hardcoded UI copy.
6. Expand feature engineering with operational, sanitation, mobility, and social-sensor signals.
7. Add causal modeling with an X-Learner to estimate intervention impact.

## Updated Folder Architecture

```text
vectra-health/
├── api/
│   ├── routers/
│   │   ├── risk.py                    # risk, timeline, graph, copilot endpoints
│   │   └── agent.py                   # HITL and execution trace endpoints
│   ├── schemas/
│   │   ├── risk_schema.py             # geospatial, causal and copilot schemas
│   │   └── agent_schema.py
│   └── services/
│       ├── prediction_service.py      # risk, timeline, graph, lightweight RAG
│       ├── geodata_service.py
│       └── llm_agent_service.py       # LLM protocol + LangGraph-like trace
├── frontend/
│   └── src/
│       ├── App.jsx                    # command shell and mode selector
│       ├── pages/
│       │   └── Dashboard.jsx          # fullscreen War Room
│       ├── api/
│       │   └── vectraApi.js           # API client
│       └── styles/
│           └── globals.css            # dark glassmorphism design system
└── src/
    ├── features/
    │   └── orthogonal_features.py     # CNES, SNIS, mobility, social sensors
    └── models/
        └── train_causal_x_learner.py  # causal intervention impact
```

## Key Technical Decisions

- React/Vite remains the frontend runtime. The issue was product architecture and visual system, not the language.
- Leaflet is used instead of a static AI-generated map image.
- The computer-vision layer is operational: NDWI and heat-island masks overlay the map.
- The Copilot is RAG-shaped: the first implementation queries FastAPI context and can later route to NVIDIA Llama 3.3.
- HITL approval now reveals an execution terminal, simulating an autonomous LangGraph workflow after human approval.
- X-Learner is separated from the classifier to distinguish prediction from causal impact estimation.

## Essential API Contracts

```http
GET  /risk/latest
GET  /risk/{geocode}/timeline
GET  /risk/{geocode}/resilience-graph
POST /copilot/query
POST /llm-agent/protocol
POST /llm-agent/review
GET  /llm-agent/execution/{protocol_id}
```
