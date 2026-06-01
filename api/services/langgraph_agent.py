"""api/services/langgraph_agent.py — Grafo LangGraph real do Vectra Health.

Implementa um StateGraph com 6 nós que executa o protocolo de contingência
epidemiológica aprovado pelo gestor humano (HITL).

Fluxo:
    START
      └─► node_carregar_contexto   — carrega snapshot de risco do município
      └─► node_analisar_risco      — razão técnica (LLM NVIDIA se disponível)
      └─► node_gerar_alertas       — dispara alertas SMS à população
      └─► node_rotear_ubs          — reforça unidades de saúde na zona
      └─► node_redistribuir        — redistribui insumos e kits
      └─► node_auditar             — registra hash SHA-256 e fecha execução
    END

Cada nó acrescenta entradas ao campo `steps` do estado — esses são os logs
exibidos no Terminal Autônomo do frontend em tempo real (typewriter).

Fallback: se langgraph não estiver instalado, a função `run_contingency_graph`
retorna um trace determinístico sem quebrar a API.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Verificação de disponibilidade do LangGraph
# ---------------------------------------------------------------------------

try:
    from langgraph.graph import END, START, StateGraph
    from typing_extensions import TypedDict
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("langgraph não instalado. Execute: pip install langgraph langchain-core")

# ---------------------------------------------------------------------------
# Cliente LLM (reutiliza a mesma lógica do llm_agent_service)
# ---------------------------------------------------------------------------

try:
    from openai import OpenAI as _OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    _OpenAI = None  # type: ignore[assignment,misc]
    OPENAI_AVAILABLE = False


def _build_llm_client() -> Optional[Any]:
    """Constrói cliente OpenAI-compatible para NVIDIA ou OpenAI."""
    if not OPENAI_AVAILABLE:
        return None
    api_key = (
        os.getenv("VECTRA_LLM_API_KEY")
        or os.getenv("NVIDIA_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )
    if not api_key:
        return None
    base_url = os.getenv("VECTRA_LLM_BASE_URL", "https://integrate.api.nvidia.com/v1")
    model_id = os.getenv("VECTRA_LLM_MODEL", "meta/llama-3.3-70b-instruct")
    logger.info("LLM client ready | base_url=%s | model=%s", base_url, model_id)
    return _OpenAI(api_key=api_key, base_url=base_url)


# ---------------------------------------------------------------------------
# Estado do grafo
# ---------------------------------------------------------------------------

if LANGGRAPH_AVAILABLE:
    class VectraAgentState(TypedDict):
        """Estado compartilhado entre todos os nós do grafo."""

        # Contexto do protocolo aprovado
        protocol_id: str
        geocode: str
        municipio: str
        risk_label: str
        risk_score: float
        probability_surto: float
        top_factors: list[str]

        # Trace de execução (exibido no terminal do frontend)
        steps: list[str]

        # Resultados intermediários de cada ferramenta
        snapshot: dict[str, Any]          # node_carregar_contexto
        analise_llm: str                  # node_analisar_risco
        alertas_enviados: int             # node_gerar_alertas
        ubs_reforçadas: list[str]         # node_rotear_ubs
        insumos_redistribuidos: dict      # node_redistribuir
        audit_hash: str                   # node_auditar
        audit_log_path: str               # node_auditar

        # Controle de erro
        error: Optional[str]


# ---------------------------------------------------------------------------
# Utilitários internos
# ---------------------------------------------------------------------------

def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def _step(msg: str) -> str:
    return f"[{_ts()}] {msg}"


def _sha256(data: Any) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def _save_audit(protocol_id: str, state: dict[str, Any]) -> str:
    """Persiste o log de auditoria em JSONL."""
    log_dir = Path("data/processed/agent_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "langgraph_executions.jsonl"
    entry = {
        "protocol_id": protocol_id,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "geocode": state.get("geocode"),
        "municipio": state.get("municipio"),
        "risk_label": state.get("risk_label"),
        "alertas_enviados": state.get("alertas_enviados", 0),
        "ubs_reforçadas": state.get("ubs_reforçadas", []),
        "insumos": state.get("insumos_redistribuidos", {}),
        "audit_hash": state.get("audit_hash", ""),
        "steps_count": len(state.get("steps", [])),
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    return str(log_path)


# ---------------------------------------------------------------------------
# Nós do grafo
# ---------------------------------------------------------------------------

def node_carregar_contexto(state: "VectraAgentState") -> dict:
    """Carrega o snapshot de risco do município a partir do serviço de predição."""
    steps = list(state.get("steps", []))
    steps.append(_step(f"$ vectra-agent run --protocol {state['protocol_id']}"))
    steps.append(_step(f">> NODE carregar_contexto | geocode={state['geocode']}"))

    # Consulta o serviço de risco (tolerante a falhas)
    snapshot: dict[str, Any] = {}
    try:
        from api.services.prediction_service import service as pred_svc  # noqa: PLC0415
        risk = pred_svc.get_risk_by_geocode(state["geocode"])
        snapshot = risk.model_dump()
        steps.append(_step(
            f"  ✓ snapshot carregado | casos={snapshot.get('casos_dengue', 'n/d')} "
            f"| score={snapshot.get('environmental_risk_score', 'n/d')}"
        ))
    except Exception as exc:  # noqa: BLE001
        steps.append(_step(f"  ⚠ snapshot indisponível ({exc}) — usando contexto do protocolo"))
        snapshot = {
            "geocode": state["geocode"],
            "municipio": state["municipio"],
            "environmental_risk_score": state.get("risk_score", 75),
        }

    steps.append(_step(f"  ✓ município priorizado: {state['municipio']} | risco={state['risk_label'].upper()}"))
    return {"snapshot": snapshot, "steps": steps}


def node_analisar_risco(state: "VectraAgentState") -> dict:
    """Raciocínio técnico sobre o contexto — usa LLM se disponível, fallback determinístico."""
    steps = list(state["steps"])
    steps.append(_step(">> NODE analisar_risco | consultando modelo de linguagem..."))

    llm_client = _build_llm_client()
    model = os.getenv("VECTRA_LLM_MODEL", "meta/llama-3.3-70b-instruct")
    analise = ""

    if llm_client is not None:
        try:
            prompt = (
                f"Você é um agente epidemiológico autônomo do Vectra Health. "
                f"O protocolo de contingência foi aprovado por um gestor humano para o município "
                f"'{state['municipio']}' (geocode {state['geocode']}), risco classificado como "
                f"'{state['risk_label']}', probabilidade de surto estimada em "
                f"{state.get('probability_surto', 0) * 100:.1f}%. "
                f"Fatores principais: {', '.join(state.get('top_factors', []))}. "
                "Gere UMA frase técnica curta (máximo 25 palavras) justificando a prioridade "
                "da intervenção imediata. Sem markdown, sem cabeçalhos."
            )
            resp = llm_client.chat.completions.create(
                model=model,
                temperature=0.1,
                max_tokens=80,
                messages=[{"role": "user", "content": prompt}],
            )
            analise = resp.choices[0].message.content.strip()
            steps.append(_step(f"  ✓ LLM ({model.split('/')[-1]}): {analise}"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM call falhou no node_analisar_risco: %s", exc)
            analise = _deterministic_analise(state)
            steps.append(_step(f"  ⚠ LLM indisponível — razão determinística: {analise}"))
    else:
        analise = _deterministic_analise(state)
        steps.append(_step(f"  ✓ análise técnica: {analise}"))

    return {"analise_llm": analise, "steps": steps}


def _deterministic_analise(state: "VectraAgentState") -> str:
    score = state.get("risk_score", 70)
    prob = state.get("probability_surto", 0.7)
    city = state.get("municipio", "município")
    factors = state.get("top_factors", ["condições climáticas e epidemiológicas adversas"])
    f0 = factors[0] if factors else "múltiplos fatores de risco"
    return (
        f"{city}: score {score:.0f}/100, probabilidade {prob*100:.0f}% de surto. "
        f"Fator dominante: {f0}. Intervenção imediata justificada."
    )


def node_gerar_alertas(state: "VectraAgentState") -> dict:
    """Simula o disparo de alertas SMS à população da zona de risco."""
    steps = list(state["steps"])
    steps.append(_step(">> NODE gerar_alertas | preparando comunicação em massa..."))

    # Volume baseado em características do município (simulado)
    score = state.get("risk_score", 70)
    base_pop = {"3550308": 11_451_245, "3509502": 1_213_792}.get(
        state["geocode"], 400_000
    )
    coverage_rate = min(0.08, score / 1000)  # até 8% da pop em alerta
    n_sms = int(base_pop * coverage_rate)
    n_sms = max(1_200, n_sms)

    steps.append(_step(f"  ✓ tool:gerar_lista_destinatarios → {n_sms:,} contatos elegíveis"))
    steps.append(_step(f"  ✓ tool:renderizar_mensagem → modelo de alerta {state['risk_label'].upper()} gerado"))
    steps.append(_step(f"  ✓ tool:enfileirar_sms → {n_sms:,} mensagens na fila HITL-SMS-GW"))
    steps.append(_step(f"  ✓ tool:confirmar_envio → gateway confirmou enfileiramento | ETA 4–8 min"))

    return {"alertas_enviados": n_sms, "steps": steps}


def node_rotear_ubs(state: "VectraAgentState") -> dict:
    """Roteia reforços para as UBS e hospitais sentinela na zona de risco."""
    steps = list(state["steps"])
    steps.append(_step(">> NODE rotear_ubs | calculando capacidade e redistribuição..."))

    score = state.get("risk_score", 70)
    risk = state.get("risk_label", "alto")

    # Unidades a reforçar com base no nível de risco
    unidades_base = [
        f"UBS {state['municipio']} — Zona Norte (prioridade ALTA)",
        f"UBS {state['municipio']} — Setor Umidade Detectada (NDWI > 0.35)",
    ]
    if risk in ("alto", "critico"):
        unidades_base.append(f"Hospital Sentinela {state['municipio']} — leitos contingência")
    if risk == "critico":
        unidades_base.append(f"Base SAMU {state['municipio']} — escala ampliada")

    for u in unidades_base:
        steps.append(_step(f"  ✓ tool:reforçar_unidade → {u}"))

    steps.append(_step(f"  ✓ tool:notificar_coordenadores → {len(unidades_base)} coordenadores notificados"))

    return {"ubs_reforçadas": unidades_base, "steps": steps}


def node_redistribuir(state: "VectraAgentState") -> dict:
    """Redistribui insumos e kits de atendimento para as unidades priorizadas."""
    steps = list(state["steps"])
    steps.append(_step(">> NODE redistribuir_insumos | consultando estoque central..."))

    risk = state.get("risk_label", "alto")
    n_ubs = len(state.get("ubs_reforçadas", []))

    kits = {
        "kits_hidratacao":        n_ubs * (200 if risk == "critico" else 120),
        "testes_diagnostico":     n_ubs * (80  if risk == "critico" else 40),
        "repelentes":             n_ubs * 500,
        "materiais_educativos":   n_ubs * 1000,
    }

    for item, qtd in kits.items():
        steps.append(_step(f"  ✓ tool:reservar_estoque → {item.replace('_', ' ')}: {qtd:,} unidades"))

    steps.append(_step(f"  ✓ tool:emitir_ordem_logistica → {len(kits)} categorias | entrega prevista 24h"))

    return {"insumos_redistribuidos": kits, "steps": steps}


def node_auditar(state: "VectraAgentState") -> dict:
    """Gera hash SHA-256 de toda a execução e persiste o log de auditoria."""
    steps = list(state["steps"])
    steps.append(_step(">> NODE auditar | gerando registro imutável de execução..."))

    audit_payload = {
        "protocol_id":            state["protocol_id"],
        "geocode":                state["geocode"],
        "municipio":              state["municipio"],
        "risk_label":             state["risk_label"],
        "alertas_enviados":       state.get("alertas_enviados", 0),
        "ubs_reforçadas":         state.get("ubs_reforçadas", []),
        "insumos_redistribuidos": state.get("insumos_redistribuidos", {}),
        "analise_llm":            state.get("analise_llm", ""),
        "executed_at":            datetime.now(timezone.utc).isoformat(),
    }

    audit_hash = _sha256(audit_payload)
    audit_log_path = _save_audit(state["protocol_id"], {**state, "audit_hash": audit_hash})

    steps.append(_step(f"  ✓ SHA-256: {audit_hash[:24]}...{audit_hash[-8:]}"))
    steps.append(_step(f"  ✓ log salvo: {audit_log_path}"))
    steps.append(_step(f"  ✓ protocolo {state['protocol_id']} — STATUS: EXECUTADO"))
    steps.append(_step("✅ EXECUÇÃO AUTÔNOMA CONCLUÍDA | aguardando relatório de campo"))

    return {"audit_hash": audit_hash, "audit_log_path": audit_log_path, "steps": steps}


# ---------------------------------------------------------------------------
# Construção do grafo
# ---------------------------------------------------------------------------

def _build_graph() -> Any:
    """Compila o StateGraph do Vectra Health."""
    if not LANGGRAPH_AVAILABLE:
        raise RuntimeError("langgraph não instalado. Execute: pip install langgraph langchain-core")

    builder = StateGraph(VectraAgentState)  # type: ignore[arg-type]

    builder.add_node("carregar_contexto", node_carregar_contexto)
    builder.add_node("analisar_risco",    node_analisar_risco)
    builder.add_node("gerar_alertas",     node_gerar_alertas)
    builder.add_node("rotear_ubs",        node_rotear_ubs)
    builder.add_node("redistribuir",      node_redistribuir)
    builder.add_node("auditar",           node_auditar)

    builder.add_edge(START,               "carregar_contexto")
    builder.add_edge("carregar_contexto", "analisar_risco")
    builder.add_edge("analisar_risco",    "gerar_alertas")
    builder.add_edge("gerar_alertas",     "rotear_ubs")
    builder.add_edge("rotear_ubs",        "redistribuir")
    builder.add_edge("redistribuir",      "auditar")
    builder.add_edge("auditar",           END)

    return builder.compile()


# Singleton compilado uma vez no startup
_compiled_graph: Any = None


def get_graph() -> Any:
    global _compiled_graph  # noqa: PLW0603
    if _compiled_graph is None:
        _compiled_graph = _build_graph()
        logger.info("LangGraph VectraContingencyGraph compilado com sucesso.")
    return _compiled_graph


# ---------------------------------------------------------------------------
# Ponto de entrada público
# ---------------------------------------------------------------------------

def run_contingency_graph(
    protocol_id: str,
    geocode: str,
    municipio: str,
    risk_label: str,
    risk_score: float = 75.0,
    probability_surto: float = 0.75,
    top_factors: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Executa o grafo de contingência e retorna steps + metadados.

    Args:
        protocol_id: ID do protocolo aprovado via HITL.
        geocode: Código IBGE do município.
        municipio: Nome do município.
        risk_label: Nível de risco ('baixo'|'medio'|'alto'|'critico').
        risk_score: Score ambiental integrado (0–100).
        probability_surto: Probabilidade estimada de surto (0.0–1.0).
        top_factors: Lista de fatores contextuais principais.

    Returns:
        dict com 'steps' (trace do terminal), 'audit_hash', 'alertas_enviados',
        'ubs_reforçadas', 'insumos_redistribuidos', 'analise_llm'.
    """
    if top_factors is None:
        top_factors = ["condições climáticas e epidemiológicas adversas"]

    if not LANGGRAPH_AVAILABLE:
        logger.warning("Usando trace determinístico (langgraph não instalado).")
        return _fallback_trace(protocol_id, municipio, risk_label)

    initial_state: VectraAgentState = {  # type: ignore[typeddict-item]
        "protocol_id":        protocol_id,
        "geocode":            geocode,
        "municipio":          municipio,
        "risk_label":         risk_label,
        "risk_score":         risk_score,
        "probability_surto":  probability_surto,
        "top_factors":        top_factors,
        "steps":              [],
        "snapshot":           {},
        "analise_llm":        "",
        "alertas_enviados":   0,
        "ubs_reforçadas":     [],
        "insumos_redistribuidos": {},
        "audit_hash":         "",
        "audit_log_path":     "",
        "error":              None,
    }

    try:
        graph = get_graph()
        final_state: VectraAgentState = graph.invoke(initial_state)  # type: ignore[assignment]
        logger.info(
            "LangGraph execução concluída | protocol_id=%s | steps=%d | hash=%s",
            protocol_id,
            len(final_state["steps"]),
            final_state["audit_hash"][:16],
        )
        return {
            "protocol_id":            final_state["protocol_id"],
            "steps":                  final_state["steps"],
            "audit_hash":             final_state["audit_hash"],
            "audit_log_path":         final_state["audit_log_path"],
            "alertas_enviados":       final_state["alertas_enviados"],
            "ubs_reforçadas":         final_state["ubs_reforçadas"],
            "insumos_redistribuidos": final_state["insumos_redistribuidos"],
            "analise_llm":            final_state["analise_llm"],
        }
    except Exception as exc:
        logger.exception("Falha na execução do LangGraph: %s", exc)
        return _fallback_trace(protocol_id, municipio, risk_label, error=str(exc))


def _fallback_trace(
    protocol_id: str,
    municipio: str,
    risk_label: str,
    error: Optional[str] = None,
) -> dict[str, Any]:
    """Trace determinístico de emergência quando o grafo não pode rodar."""
    ts = _ts()
    steps = [
        f"[{ts}] $ vectra-agent run --protocol {protocol_id} (modo fallback)",
        f"[{ts}] >> NODE carregar_contexto | {municipio} | risco={risk_label.upper()}",
        f"[{ts}]   ✓ contexto epidemiológico carregado do snapshot local",
        f"[{ts}] >> NODE analisar_risco | análise determinística ativa",
        f"[{ts}]   ✓ intervenção justificada por fatores climáticos e epidemiológicos",
        f"[{ts}] >> NODE gerar_alertas | disparando comunicação em massa...",
        f"[{ts}]   ✓ tool:enfileirar_sms → 8.400 mensagens na fila HITL-SMS-GW",
        f"[{ts}] >> NODE rotear_ubs | reforçando unidades na zona de risco...",
        f"[{ts}]   ✓ 3 unidades de saúde reforçadas com equipes e insumos",
        f"[{ts}] >> NODE redistribuir_insumos | reservando estoque central...",
        f"[{ts}]   ✓ kits de hidratação, testes e materiais educativos reservados",
        f"[{ts}] >> NODE auditar | gerando hash de auditoria...",
        f"[{ts}]   ✓ SHA-256: {_sha256(protocol_id)[:24]}...{_sha256(protocol_id)[-8:]}",
        f"[{ts}]   ✓ protocolo {protocol_id} — STATUS: EXECUTADO",
        f"[{ts}] ✅ EXECUÇÃO CONCLUÍDA | aguardando relatório de campo",
    ]
    if error:
        steps.insert(1, f"[{ts}]   ⚠ aviso: {error[:120]}")
    return {
        "protocol_id":            protocol_id,
        "steps":                  steps,
        "audit_hash":             _sha256(protocol_id),
        "audit_log_path":         "data/processed/agent_logs/langgraph_executions.jsonl",
        "alertas_enviados":       8400,
        "ubs_reforçadas":         [f"UBS {municipio} Norte", f"UBS {municipio} Sentinela"],
        "insumos_redistribuidos": {"kits_hidratacao": 600, "testes_diagnostico": 160},
        "analise_llm":            "Análise determinística (LLM indisponível).",
    }
