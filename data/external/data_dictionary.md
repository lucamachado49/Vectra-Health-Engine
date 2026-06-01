# Dicionário de Dados — Vectra Health

Este documento descreve todas as variáveis presentes nos datasets gerados pelo pipeline do Vectra Health.

---

## 1. Dataset Raw — InfoDengue

**Arquivo**: `data/raw/infodengue/dengue_sp_selected_2020_2025_raw.csv`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `SE` | int | Semana epidemiológica (YYYYWW) |
| `casos_est` | float | Estimativa de casos |
| `casos_est_min` | float | Limite inferior da estimativa |
| `casos_est_max` | float | Limite superior da estimativa |
| `casos` | float | Casos notificados |
| `p_rt1` | float | Probabilidade Rt > 1 |
| `p_inc100k` | float | Incidência por 100.000 habitantes |
| `Localidade_id` | str | Geocode do município |
| `nivel` | int | Nível de alerta (1=verde, 2=amarelo, 3=laranja, 4=vermelho) |
| `id` | str | Identificador único |
| `versao_modelo` | str | Versão do modelo epidemiológico |
| `Rt` | float | Número reprodutivo efetivo |
| `pop` | float | População |
| `tempmin` | float | Temperatura mínima |
| `umidmin` | float | Umidade mínima |
| `receptividade_clima` | float | Receptividade climática |
| `geocode` | str | Código IBGE do município |
| `disease` | str | Doença (dengue, zika, chikungunya) |

---

## 2. Dataset Climático — NASA POWER

**Arquivo**: `data/raw/nasa_power/nasa_power_sao_paulo_2020_2025_raw.csv`

| Coluna | Tipo | Descrição | Unidade |
|--------|------|-----------|---------|
| `date` | datetime | Data (YYYYMMDD) | — |
| `T2M` | float | Temperatura média a 2m | °C |
| `T2M_MAX` | float | Temperatura máxima | °C |
| `T2M_MIN` | float | Temperatura mínima | °C |
| `RH2M` | float | Umidade relativa a 2m | % |
| `PRECTOTCORR` | float | Precipitação diária corrigida | mm |
| `geocode` | str | Código IBGE associado | — |
| `municipio` | str | Nome do município | — |

---

## 3. Dataset Intermediário — Dados Limpos

**Arquivo**: `data/interim/dengue_clean.csv`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `geocode` | str | Código IBGE do município (7 dígitos, com zeros à esquerda) |
| `municipio` | str | Nome do município |
| `ano` | int | Ano epidemiológico |
| `semana_epidemiologica` | int | Semana epidemiológica (1-53) |
| `casos_dengue` | float | Casos notificados/estimados de dengue |
| `nivel_alerta` | int | Nível de alerta InfoDengue (1-4) |
| `incidencia_100k` | float | Incidência por 100.000 habitantes |
| `rt` | float | Número reprodutivo efetivo Rt |
| `populacao` | float | Estimativa populacional |

---

## 4. Dataset de Features

**Arquivo**: `data/processed/vectra_health_features.csv`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `geocode` | str | Código IBGE do município |
| `municipio` | str | Nome do município |
| `ano` | int | Ano |
| `semana_epidemiologica` | int | Semana epidemiológica |
| `casos_dengue` | float | Casos de dengue |
| `incidencia_100k` | float | Incidência por 100k hab |
| `nivel_alerta` | int | Nível de alerta |
| `temp_media_7d` | float | Temperatura média 7 dias |
| `temp_max_7d` | float | Temperatura máxima 7 dias |
| `temp_min_7d` | float | Temperatura mínima 7 dias |
| `chuva_acumulada_7d` | float | Chuva acumulada 7 dias (mm) |
| `chuva_acumulada_14d` | float | Chuva acumulada 14 dias (mm) |
| `umidade_media_7d` | float | Umidade média 7 dias (%) |
| `casos_lag_1w` | float | Casos na semana anterior |
| `casos_lag_2w` | float | Casos há 2 semanas |
| `casos_lag_4w` | float | Casos há 4 semanas |
| `variacao_semanal` | float | % de variação nos casos |
| `media_movel_4w` | float | Média móvel de 4 semanas |
| `environmental_risk_score` | float | Score ambiental composto (0-100) |
| `risco_ambiental_label` | str | Label de risco (baixo, medio, alto, critico) |

---

## 5. Dataset de Treino

**Arquivo**: `data/processed/vectra_health_train_ready.csv`

Contém todas as colunas do dataset de features mais as variáveis target:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `target_surto_binario` | int | 1 = risco de surto, 0 = sem surto |
| `risco_surto_multiclasse` | str | baixo / medio / alto / critico |
| `risco_surto_ord` | int | 0, 1, 2, 3 (ordinal) |

---

## 6. Dataset de Risco Mais Recente

**Arquivo**: `data/processed/vectra_health_latest_risk_snapshot.csv`

Snapshot das semanas mais recentes para cada município monitorado. Usado pela API no endpoint `/risk/latest`.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `geocode` | str | Código IBGE |
| `municipio` | str | Nome do município |
| `ano` | int | Ano |
| `semana_epidemiologica` | int | Semana epidemiológica |
| `casos_dengue` | float | Casos de dengue |
| `incidencia_100k` | float | Incidência por 100k |
| `environmental_risk_score` | float | Score ambiental (0-100) |
| `risco_ambiental_label` | str | baixo / medio / alto / critico |
| `temp_media_7d` | float | Temperatura média 7d |
| `chuva_acumulada_7d` | float | Chuva acumulada 7d |
| `umidade_media_7d` | float | Umidade média 7d |

---

## Convenções

- **geocode**: Código IBGE de 7 dígitos, sempre formatado com zeros à esquerda (ex: `3550308` para São Paulo)
- **Valores ausentes**: `NaN` para numéricos, `None` para strings
- **Datas**: ISO 8601 (YYYY-MM-DD) ou semanas epidemiológicas (YYYYWW)
- **Scores**: Normalizados entre 0 e 100, onde 100 = máximo risco
