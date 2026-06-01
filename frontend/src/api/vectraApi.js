/**
 * frontend/src/api/vectraApi.js — Cliente HTTP para a API do Vectra Health.
 *
 * Centraliza todas as chamadas à API FastAPI.
 * Usa VITE_API_BASE_URL do .env ou fallback para localhost.
 */

const API_BASE_URL = import.meta?.env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

/**
 * GET request para a API Vectra Health.
 * @param {string} path - Path da API (ex: '/health')
 * @returns {Promise<any>}
 */
export async function apiGet(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) throw new Error(`GET ${path} falhou com status ${response.status}`);
  return response.json();
}

/**
 * POST request para a API Vectra Health.
 * @param {string} path - Path da API (ex: '/predict')
 * @param {object} payload - Payload JSON
 * @returns {Promise<any>}
 */
export async function apiPost(path, payload) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`POST ${path} falhou com status ${response.status}`);
  return response.json();
}

// Funções de API específicas
export const fetchHealth = () => apiGet('/health');
export const fetchLatestRisk = (limit = 20) => apiGet(`/risk/latest?limit=${limit}`);
export const fetchRiskByGeocode = (geocode) => apiGet(`/risk/${geocode}`);
export const fetchMunicipalities = () => apiGet('/municipalities');
export const fetchCausalTimeline = (geocode) => apiGet(`/risk/${geocode}/timeline`);
export const fetchResilienceGraph = (geocode) => apiGet(`/risk/${geocode}/resilience-graph`);
/** Executa o grafo LangGraph e retorna todos os steps de uma vez (JSON). */
export const fetchAutonomousExecution = (protocolId) => apiGet(`/execution/${protocolId}`);

/**
 * Abre uma conexão SSE para receber steps do LangGraph em streaming real.
 * @param {string} protocolId
 * @param {function} onStep  — chamado com cada string de step
 * @param {function} onDone  — chamado com {audit_hash, alertas} ao terminar
 * @returns {EventSource}    — chame .close() para encerrar
 */
export function streamAutonomousExecution(protocolId, onStep, onDone) {
  const url = `${API_BASE_URL}/execution/${protocolId}/stream`;
  const es = new EventSource(url);

  es.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.done) {
        onDone(data);
        es.close();
      } else if (data.step) {
        onStep(data.step);
      }
    } catch {
      onStep(event.data);
    }
  };

  es.onerror = () => {
    onDone({ done: true, error: true });
    es.close();
  };

  return es;
}
export const postPredict = (geocode, ano = null, semana = null) =>
  apiPost('/predict', { geocode, ano, semana_epidemiologica: semana });
export const postAgentProtocol = (payload) => apiPost('/llm-agent/protocol', payload);
export const postAgentReview = (payload) => apiPost('/llm-agent/review', payload);
export const fetchCopilotAnswer = (payload) => apiPost('/copilot/query', payload);
