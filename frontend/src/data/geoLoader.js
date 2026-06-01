/**
 * geoLoader.js — Carregamento sob demanda dos assets geoespaciais.
 * Os arquivos vivem em /public/geo/ e são servidos estaticamente pelo Vite.
 */

const GEO_BASE = '/geo';

/** Mapa de região → lista de UFs */
export const REGION_UFS = {
  Norte:          ['RO', 'AC', 'AM', 'RR', 'PA', 'AP', 'TO'],
  Nordeste:       ['MA', 'PI', 'CE', 'RN', 'PB', 'PE', 'AL', 'SE', 'BA'],
  'Centro-Oeste': ['MS', 'MT', 'GO', 'DF'],
  Sudeste:        ['MG', 'ES', 'RJ', 'SP'],
  Sul:            ['PR', 'SC', 'RS'],
};

/** Centro/zoom aproximado por região para o mapa */
export const REGION_VIEW = {
  Todos:          { center: [-14.5, -52], zoom: 4 },
  Norte:          { center: [-4, -60],    zoom: 5 },
  Nordeste:       { center: [-9, -40],    zoom: 5 },
  'Centro-Oeste': { center: [-15, -54],   zoom: 5 },
  Sudeste:        { center: [-20, -45],   zoom: 6 },
  Sul:            { center: [-28, -52],   zoom: 6 },
};

const _cache = new Map();

async function _fetchJson(path) {
  if (_cache.has(path)) return _cache.get(path);
  const res = await fetch(path);
  if (!res.ok) throw new Error(`GeoJSON não encontrado: ${path}`);
  const data = await res.json();
  _cache.set(path, data);
  return data;
}

/** Carrega o manifest (cobertura de dados reais, UFs disponíveis). */
export const loadManifest = () => _fetchJson(`${GEO_BASE}/manifest.json`);

/** Carrega os polígonos dos 27 estados. */
export const loadStates = () => _fetchJson(`${GEO_BASE}/brazil-states.json`);

/** Carrega o risco nacional sintético (geocode → {s,c,i,uf,n,r}). */
export const loadNationalRisk = () => _fetchJson(`${GEO_BASE}/risk-national.json`);

/** Carrega os municípios de uma UF específica. */
export const loadStateMunicipalities = (uf) => _fetchJson(`${GEO_BASE}/mun/${uf}.json`);

/**
 * Carrega e combina os municípios de todos os estados de uma região.
 * @param {string} region
 * @returns {Promise<{type:'FeatureCollection', features:Array}>}
 */
export async function loadRegionMunicipalities(region) {
  const ufs = REGION_UFS[region] || [];
  const collections = await Promise.all(
    ufs.map((uf) => loadStateMunicipalities(uf).catch(() => null)),
  );
  const features = collections
    .filter(Boolean)
    .flatMap((fc) => fc.features);
  return { type: 'FeatureCollection', features };
}

/** Todas as UFs do Brasil. */
export const ALL_UFS = Object.values(REGION_UFS).flat();

/**
 * Carrega TODOS os municípios do Brasil (27 UFs, ~5.564 polígonos).
 * @returns {Promise<{type:'FeatureCollection', features:Array}>}
 */
export async function loadAllMunicipalities() {
  const collections = await Promise.all(
    ALL_UFS.map((uf) => loadStateMunicipalities(uf).catch(() => null)),
  );
  const features = collections.filter(Boolean).flatMap((fc) => fc.features);
  return { type: 'FeatureCollection', features };
}

/** Cor de risco por score (mesma escala do design system). */
export function scoreColor(score) {
  if (score >= 85) return '#dc2626';
  if (score >= 70) return '#ea580c';
  if (score >= 50) return '#ca8a04';
  if (score >= 30) return '#65a30d';
  return '#16a34a';
}
