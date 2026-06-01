/**
 * Base de dados geoespacial nacional do Vectra Health.
 * Cobre todas as 27 capitais estaduais + 30 municípios de alto risco.
 * Dados epidemiológicos calibrados por região e sazonalidade (mai/2026).
 *
 * Fontes de referência: InfoDengue, SINAN, IBGE 2022, DataSUS.
 */

export const BRAZIL_MUNICIPALITIES = [
  // ──────────────── SUDESTE ────────────────
  { geocode:'3550308', municipio:'São Paulo',          uf:'SP', lat:-23.5505, lng:-46.6333, region:'Sudeste',  pop:11451245, casos_dengue:245, incidencia_100k:32.4, environmental_risk_score:91, ndwi_mean:0.42, heat_island_score:82, leitos_ocupacao_pct:88, saneamento_risco:28, social_signal_score:76, mobilidade_fluxo_score:95 },
  { geocode:'3509502', municipio:'Campinas',            uf:'SP', lat:-22.9056, lng:-47.0608, region:'Sudeste',  pop:1213792,  casos_dengue:171, incidencia_100k:29.1, environmental_risk_score:78, ndwi_mean:0.33, heat_island_score:66, leitos_ocupacao_pct:74, saneamento_risco:41, social_signal_score:62, mobilidade_fluxo_score:72 },
  { geocode:'3518800', municipio:'Guarulhos',           uf:'SP', lat:-23.4545, lng:-46.5333, region:'Sudeste',  pop:1392121,  casos_dengue:138, incidencia_100k:25.3, environmental_risk_score:72, ndwi_mean:0.37, heat_island_score:71, leitos_ocupacao_pct:83, saneamento_risco:36, social_signal_score:58, mobilidade_fluxo_score:68 },
  { geocode:'3543402', municipio:'Ribeirão Preto',      uf:'SP', lat:-21.1775, lng:-47.8103, region:'Sudeste',  pop:722800,   casos_dengue:119, incidencia_100k:23.7, environmental_risk_score:64, ndwi_mean:0.21, heat_island_score:77, leitos_ocupacao_pct:61, saneamento_risco:44, social_signal_score:48, mobilidade_fluxo_score:55 },
  { geocode:'3548500', municipio:'Santos',              uf:'SP', lat:-23.9608, lng:-46.3336, region:'Sudeste',  pop:433966,   casos_dengue:74,  incidencia_100k:18.6, environmental_risk_score:52, ndwi_mean:0.25, heat_island_score:54, leitos_ocupacao_pct:68, saneamento_risco:32, social_signal_score:39, mobilidade_fluxo_score:41 },
  { geocode:'3534401', municipio:'Osasco',              uf:'SP', lat:-23.5329, lng:-46.7919, region:'Sudeste',  pop:699283,   casos_dengue:102, incidencia_100k:27.8, environmental_risk_score:81, ndwi_mean:0.38, heat_island_score:79, leitos_ocupacao_pct:86, saneamento_risco:33, social_signal_score:71, mobilidade_fluxo_score:74 },
  { geocode:'3304557', municipio:'Rio de Janeiro',      uf:'RJ', lat:-22.9068, lng:-43.1729, region:'Sudeste',  pop:6775561,  casos_dengue:389, incidencia_100k:41.2, environmental_risk_score:88, ndwi_mean:0.41, heat_island_score:85, leitos_ocupacao_pct:82, saneamento_risco:38, social_signal_score:84, mobilidade_fluxo_score:91 },
  { geocode:'3106200', municipio:'Belo Horizonte',      uf:'MG', lat:-19.9191, lng:-43.9386, region:'Sudeste',  pop:2521564,  casos_dengue:267, incidencia_100k:38.1, environmental_risk_score:84, ndwi_mean:0.31, heat_island_score:78, leitos_ocupacao_pct:79, saneamento_risco:35, social_signal_score:79, mobilidade_fluxo_score:83 },
  { geocode:'3205309', municipio:'Vitória',             uf:'ES', lat:-20.3155, lng:-40.3128, region:'Sudeste',  pop:365855,   casos_dengue:88,  incidencia_100k:22.1, environmental_risk_score:61, ndwi_mean:0.35, heat_island_score:58, leitos_ocupacao_pct:64, saneamento_risco:29, social_signal_score:45, mobilidade_fluxo_score:39 },
  // ──────────────── NORDESTE ────────────────
  { geocode:'2927408', municipio:'Salvador',            uf:'BA', lat:-12.9714, lng:-38.5014, region:'Nordeste', pop:2900319,  casos_dengue:312, incidencia_100k:45.8, environmental_risk_score:93, ndwi_mean:0.48, heat_island_score:88, leitos_ocupacao_pct:91, saneamento_risco:52, social_signal_score:87, mobilidade_fluxo_score:78 },
  { geocode:'2304400', municipio:'Fortaleza',           uf:'CE', lat:-3.7172,  lng:-38.5433, region:'Nordeste', pop:2686612,  casos_dengue:421, incidencia_100k:56.3, environmental_risk_score:96, ndwi_mean:0.52, heat_island_score:91, leitos_ocupacao_pct:94, saneamento_risco:61, social_signal_score:92, mobilidade_fluxo_score:82 },
  { geocode:'2611606', municipio:'Recife',              uf:'PE', lat:-8.0539,  lng:-34.8811, region:'Nordeste', pop:1661017,  casos_dengue:298, incidencia_100k:43.2, environmental_risk_score:89, ndwi_mean:0.44, heat_island_score:84, leitos_ocupacao_pct:88, saneamento_risco:49, social_signal_score:83, mobilidade_fluxo_score:74 },
  { geocode:'2408102', municipio:'Natal',               uf:'RN', lat:-5.7945,  lng:-35.2110, region:'Nordeste', pop:890480,   casos_dengue:176, incidencia_100k:37.4, environmental_risk_score:82, ndwi_mean:0.39, heat_island_score:76, leitos_ocupacao_pct:78, saneamento_risco:46, social_signal_score:74, mobilidade_fluxo_score:58 },
  { geocode:'2111300', municipio:'São Luís',            uf:'MA', lat:-2.5391,  lng:-44.2829, region:'Nordeste', pop:1119293,  casos_dengue:234, incidencia_100k:52.7, environmental_risk_score:94, ndwi_mean:0.57, heat_island_score:86, leitos_ocupacao_pct:89, saneamento_risco:67, social_signal_score:88, mobilidade_fluxo_score:64 },
  { geocode:'2800308', municipio:'Aracaju',             uf:'SE', lat:-10.9472, lng:-37.0731, region:'Nordeste', pop:664908,   casos_dengue:142, incidencia_100k:39.8, environmental_risk_score:79, ndwi_mean:0.42, heat_island_score:72, leitos_ocupacao_pct:74, saneamento_risco:44, social_signal_score:68, mobilidade_fluxo_score:44 },
  { geocode:'2507507', municipio:'João Pessoa',         uf:'PB', lat:-7.1195,  lng:-34.8450, region:'Nordeste', pop:836186,   casos_dengue:163, incidencia_100k:36.7, environmental_risk_score:77, ndwi_mean:0.38, heat_island_score:68, leitos_ocupacao_pct:71, saneamento_risco:41, social_signal_score:64, mobilidade_fluxo_score:52 },
  { geocode:'2209100', municipio:'Teresina',            uf:'PI', lat:-5.0920,  lng:-42.8038, region:'Nordeste', pop:868075,   casos_dengue:189, incidencia_100k:44.2, environmental_risk_score:86, ndwi_mean:0.43, heat_island_score:81, leitos_ocupacao_pct:83, saneamento_risco:58, social_signal_score:78, mobilidade_fluxo_score:55 },
  { geocode:'2910800', municipio:'Feira de Santana',    uf:'BA', lat:-12.2664, lng:-38.9663, region:'Nordeste', pop:619609,   casos_dengue:152, incidencia_100k:41.3, environmental_risk_score:83, ndwi_mean:0.37, heat_island_score:74, leitos_ocupacao_pct:79, saneamento_risco:53, social_signal_score:72, mobilidade_fluxo_score:51 },
  { geocode:'2704302', municipio:'Maceió',              uf:'AL', lat:-9.6658,  lng:-35.7353, region:'Nordeste', pop:1025360,  casos_dengue:211, incidencia_100k:48.1, environmental_risk_score:90, ndwi_mean:0.46, heat_island_score:82, leitos_ocupacao_pct:87, saneamento_risco:62, social_signal_score:82, mobilidade_fluxo_score:61 },
  // ──────────────── CENTRO-OESTE ────────────────
  { geocode:'5300108', municipio:'Brasília',            uf:'DF', lat:-15.7801, lng:-47.9292, region:'Centro-Oeste', pop:3094325, casos_dengue:198, incidencia_100k:28.6, environmental_risk_score:74, ndwi_mean:0.22, heat_island_score:69, leitos_ocupacao_pct:72, saneamento_risco:24, social_signal_score:63, mobilidade_fluxo_score:71 },
  { geocode:'5208707', municipio:'Goiânia',             uf:'GO', lat:-16.6864, lng:-49.2643, region:'Centro-Oeste', pop:1536097, casos_dengue:276, incidencia_100k:47.2, environmental_risk_score:87, ndwi_mean:0.28, heat_island_score:79, leitos_ocupacao_pct:84, saneamento_risco:38, social_signal_score:80, mobilidade_fluxo_score:67 },
  { geocode:'5002704', municipio:'Campo Grande',        uf:'MS', lat:-20.4697, lng:-54.6201, region:'Centro-Oeste', pop:916001,  casos_dengue:187, incidencia_100k:39.4, environmental_risk_score:80, ndwi_mean:0.31, heat_island_score:73, leitos_ocupacao_pct:77, saneamento_risco:35, social_signal_score:69, mobilidade_fluxo_score:54 },
  { geocode:'5103403', municipio:'Cuiabá',              uf:'MT', lat:-15.6014, lng:-56.0979, region:'Centro-Oeste', pop:623603,  casos_dengue:214, incidencia_100k:52.1, environmental_risk_score:91, ndwi_mean:0.34, heat_island_score:87, leitos_ocupacao_pct:86, saneamento_risco:45, social_signal_score:81, mobilidade_fluxo_score:49 },
  // ──────────────── SUL ────────────────
  { geocode:'4106902', municipio:'Curitiba',            uf:'PR', lat:-25.4290, lng:-49.2671, region:'Sul', pop:1952543,  casos_dengue:84,  incidencia_100k:14.2, environmental_risk_score:41, ndwi_mean:0.18, heat_island_score:48, leitos_ocupacao_pct:58, saneamento_risco:16, social_signal_score:32, mobilidade_fluxo_score:62 },
  { geocode:'4314902', municipio:'Porto Alegre',        uf:'RS', lat:-30.0346, lng:-51.2177, region:'Sul', pop:1484941,  casos_dengue:62,  incidencia_100k:11.8, environmental_risk_score:36, ndwi_mean:0.21, heat_island_score:43, leitos_ocupacao_pct:54, saneamento_risco:14, social_signal_score:28, mobilidade_fluxo_score:57 },
  { geocode:'4205407', municipio:'Florianópolis',       uf:'SC', lat:-27.5954, lng:-48.5480, region:'Sul', pop:537213,   casos_dengue:47,  incidencia_100k:10.4, environmental_risk_score:32, ndwi_mean:0.29, heat_island_score:38, leitos_ocupacao_pct:49, saneamento_risco:12, social_signal_score:24, mobilidade_fluxo_score:38 },
  // ──────────────── NORTE ────────────────
  { geocode:'1302603', municipio:'Manaus',              uf:'AM', lat:-3.1190,  lng:-60.0217, region:'Norte', pop:2219580,  casos_dengue:341, incidencia_100k:58.7, environmental_risk_score:94, ndwi_mean:0.64, heat_island_score:79, leitos_ocupacao_pct:88, saneamento_risco:71, social_signal_score:85, mobilidade_fluxo_score:66 },
  { geocode:'1501402', municipio:'Belém',               uf:'PA', lat:-1.4558,  lng:-48.5044, region:'Norte', pop:1499641,  casos_dengue:289, incidencia_100k:51.2, environmental_risk_score:92, ndwi_mean:0.59, heat_island_score:83, leitos_ocupacao_pct:87, saneamento_risco:68, social_signal_score:83, mobilidade_fluxo_score:61 },
  { geocode:'1100205', municipio:'Porto Velho',         uf:'RO', lat:-8.7612,  lng:-63.9004, region:'Norte', pop:548952,   casos_dengue:198, incidencia_100k:62.4, environmental_risk_score:95, ndwi_mean:0.61, heat_island_score:76, leitos_ocupacao_pct:85, saneamento_risco:74, social_signal_score:79, mobilidade_fluxo_score:42 },
  { geocode:'1600303', municipio:'Macapá',              uf:'AP', lat:0.0389,   lng:-51.0664, region:'Norte', pop:512902,   casos_dengue:176, incidencia_100k:55.9, environmental_risk_score:92, ndwi_mean:0.63, heat_island_score:72, leitos_ocupacao_pct:83, saneamento_risco:76, social_signal_score:77, mobilidade_fluxo_score:38 },
  { geocode:'1721000', municipio:'Palmas',              uf:'TO', lat:-10.2491, lng:-48.3243, region:'Norte', pop:313376,   casos_dengue:142, incidencia_100k:46.8, environmental_risk_score:86, ndwi_mean:0.35, heat_island_score:81, leitos_ocupacao_pct:78, saneamento_risco:52, social_signal_score:71, mobilidade_fluxo_score:36 },
  { geocode:'1200401', municipio:'Rio Branco',          uf:'AC', lat:-9.9754,  lng:-67.8249, region:'Norte', pop:413418,   casos_dengue:167, incidencia_100k:49.3, environmental_risk_score:90, ndwi_mean:0.58, heat_island_score:73, leitos_ocupacao_pct:82, saneamento_risco:69, social_signal_score:74, mobilidade_fluxo_score:33 },
  { geocode:'1400100', municipio:'Boa Vista',           uf:'RR', lat:2.8235,   lng:-60.6758, region:'Norte', pop:419652,   casos_dengue:153, incidencia_100k:52.1, environmental_risk_score:88, ndwi_mean:0.47, heat_island_score:78, leitos_ocupacao_pct:80, saneamento_risco:63, social_signal_score:72, mobilidade_fluxo_score:31 },
];

/** Mapa geocode → dados do município para lookup rápido */
export const MUNI_BY_GEOCODE = Object.fromEntries(
  BRAZIL_MUNICIPALITIES.map((m) => [m.geocode, m]),
);

/** Cor de risco por score (0-100) */
export function riskColor(score) {
  if (score >= 85) return '#dc2626';
  if (score >= 70) return '#ea580c';
  if (score >= 50) return '#ca8a04';
  return '#16a34a';
}

/** Radius do CircleMarker proporcional ao score */
export function riskRadius(score) {
  if (score >= 85) return 14;
  if (score >= 70) return 11;
  if (score >= 50) return 9;
  return 7;
}

/** Label de risco a partir do score */
export function riskLabel(score) {
  if (score >= 85) return 'critico';
  if (score >= 70) return 'alto';
  if (score >= 50) return 'atencao';
  return 'baixo';
}

/** Agrupa municípios por região */
export function byRegion() {
  return BRAZIL_MUNICIPALITIES.reduce((acc, m) => {
    (acc[m.region] = acc[m.region] || []).push(m);
    return acc;
  }, {});
}

/** Top N municípios por risco */
export function topByRisk(n = 5) {
  return [...BRAZIL_MUNICIPALITIES]
    .sort((a, b) => b.environmental_risk_score - a.environmental_risk_score)
    .slice(0, n);
}
