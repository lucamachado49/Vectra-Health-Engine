# Fontes de Dados — Vectra Health

## Visão Geral

O Vectra Health integra dados de **5 fontes públicas** para construir o dataset analítico de previsão de risco epidemiológico.

---

## 1. InfoDengue / AlertaDengue

- **Organização**: Fundação Oswaldo Cruz (Fiocruz) + Programa de Computação Científica (Procc)
- **URL**: https://info.dengue.mat.br
- **API**: https://info.dengue.mat.br/api/alertcity
- **Acesso**: Público, sem autenticação
- **Formato**: CSV via query string
- **Cobertura**: Municípios brasileiros com vigilância ativa
- **Granularidade**: Semanal (semana epidemiológica)
- **Doenças**: Dengue, Zika, Chikungunya

### Parâmetros da API

```
GET https://info.dengue.mat.br/api/alertcity
  ?geocode=<IBGE>
  &disease=dengue
  &format=csv
  &ew_start=1
  &ew_end=53
  &ey_start=2020
  &ey_end=2025
```

### Arquivo gerado
`data/raw/infodengue/dengue_sp_selected_2020_2025_raw.csv`

---

## 2. NASA POWER API

- **Organização**: NASA — Langley Research Center
- **URL**: https://power.larc.nasa.gov
- **API**: https://power.larc.nasa.gov/api/temporal/daily/point
- **Acesso**: Público, sem autenticação
- **Formato**: JSON
- **Cobertura**: Global (ponto de coordenada)
- **Granularidade**: Diária

### Variáveis coletadas

| Código | Descrição | Unidade |
|--------|-----------|---------|
| T2M | Temperatura média a 2m | °C |
| T2M_MAX | Temperatura máxima | °C |
| T2M_MIN | Temperatura mínima | °C |
| RH2M | Umidade relativa a 2m | % |
| PRECTOTCORR | Precipitação corrigida | mm/dia |

### Arquivos gerados
- `data/raw/nasa_power/nasa_power_sao_paulo_2020_2025_raw.json`
- `data/raw/nasa_power/nasa_power_sao_paulo_2020_2025_raw.csv`

---

## 3. IBGE SIDRA — Estimativas Populacionais

- **Organização**: Instituto Brasileiro de Geografia e Estatística (IBGE)
- **URL**: https://sidra.ibge.gov.br
- **API**: https://apisidra.ibge.gov.br
- **Acesso**: Público, sem autenticação
- **Formato**: JSON
- **Tabela utilizada**: 6579 (Estimativa da população residente)
- **Variável**: 9324 (População estimada)

### Endpoint

```
GET https://apisidra.ibge.gov.br/values/t/6579/n6/all/v/9324/p/2021
```

### Arquivo gerado
`data/raw/ibge/populacao_municipios_2021_raw.csv`

---

## 4. geobr — Malha Municipal Brasileira

- **Organização**: IPEA + IBGE
- **Pacote Python**: `geobr`
- **Instalação**: `pip install geobr`
- **Acesso**: Público
- **Formato**: GeoJSON / GeoDataFrame
- **Cobertura**: Todos os municípios brasileiros
- **Anos disponíveis**: 2000, 2001, ..., 2022

### Arquivo gerado
`data/raw/geo/municipios_sp_2020_raw.geojson`

---

## 5. DataSUS / CNES — Capacidade Hospitalar

- **Organização**: Ministério da Saúde / DATASUS
- **URL**: https://cnes.datasus.gov.br
- **Acesso**: Download manual (CSV exportado)
- **Dados coletados**: Leitos hospitalares por município

### Arquivo gerado
`data/raw/datasus/cnes_leitos_raw.csv`

---

## Citação e Uso

Todos os dados utilizados são públicos e gratuitos. Ao utilizar este projeto:

1. Cite as fontes originais (InfoDengue, NASA POWER, IBGE, geobr, DATASUS)
2. Verifique as condições de uso de cada API
3. Este projeto é para fins acadêmicos e de pesquisa

---

## Atualização dos dados

Os dados podem ser atualizados rodando:

```bash
python -m src.data.collect_data
python -m src.data.preprocess_and_integrate
python -m src.features.build_features
```
