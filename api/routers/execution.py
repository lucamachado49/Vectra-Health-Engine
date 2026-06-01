"""api/routers/execution.py — Endpoint de execução autônoma pós-HITL.

Expõe dois endpoints:
    GET /execution/{protocol_id}         — retorna todos os steps de uma vez (JSON)
    GET /execution/{protocol_id}/stream  — Server-Sent Events: envia steps linha a linha

O frontend usa o endpoint JSON por padrão. O SSE é opcional para quem
quiser streaming real em vez da animação typewriter do cliente.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.services.llm_agent_service import VectraLLMAgentService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/execution", tags=["execution"])

_svc: VectraLLMAgentService | None = None


def _get_svc() -> VectraLLMAgentService:
    global _svc  # noqa: PLW0603
    if _svc is None:
        _svc = VectraLLMAgentService()
    return _svc


@router.get("/{protocol_id}", summary="Executa grafo LangGraph e retorna trace completo")
def run_execution(protocol_id: str) -> dict[str, Any]:
    """Invoca o grafo LangGraph real e devolve todos os steps de uma vez."""
    return _get_svc().simulate_autonomous_execution(protocol_id)


@router.get("/{protocol_id}/stream", summary="Streaming SSE dos steps do grafo")
async def stream_execution(protocol_id: str) -> StreamingResponse:
    """Executa o grafo em thread separada e transmite steps via Server-Sent Events."""

    async def event_generator():
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            _get_svc().simulate_autonomous_execution,
            protocol_id,
        )
        steps: list[str] = result.get("steps", [])
        for step in steps:
            data = json.dumps({"step": step}, ensure_ascii=False)
            yield f"data: {data}\n\n"
            await asyncio.sleep(0.35)  # cadência do streaming

        # Evento de encerramento com metadados
        meta = json.dumps({
            "done":        True,
            "audit_hash":  result.get("audit_hash", ""),
            "alertas":     result.get("alertas", 0),
            "engine":      result.get("engine", "langgraph_real_runtime"),
        }, ensure_ascii=False)
        yield f"data: {meta}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":               "no-cache",
            "X-Accel-Buffering":           "no",
            "Access-Control-Allow-Origin": "*",
        },
    )
