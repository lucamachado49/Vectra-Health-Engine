# Human-in-the-Loop — Vectra Health

## Princípio Fundamental

> **Nenhuma ação operacional de saúde pública é executada sem aprovação humana explícita.**

O Vectra Health incorpora o padrão **Human-in-the-Loop (HITL)** em toda a cadeia de decisão que envolve alocação de recursos, comunicação de alertas e ativação de protocolos de contingência.

---

## Fluxo de Decisão

```
Modelo ML → Score de risco
     ↓
LLM Agent gera protocolo
     ↓
Status: pending_review (bloqueado)
     ↓
Gestor de saúde revisa protocolo
     ↓
Decisão humana obrigatória
   ├─ approved → protocolo liberado
   ├─ revision_requested → agente reformula
   └─ rejected → protocolo arquivado
```

---

## Por que HITL é obrigatório?

### 1. Responsabilidade legal
Protocolos de saúde pública envolvem alocação de recursos públicos, comunicação com a população e mobilização de equipes. A responsabilidade legal dessas decisões recai sobre o gestor humano, não sobre o sistema.

### 2. Contexto local
O modelo não tem acesso a eventos locais não estruturados:
- Eventos especiais (shows, manifestações)
- Obras de infraestrutura
- Focos de infestação já conhecidos pela equipe local
- Disputas de competência entre órgãos

### 3. Falibilidade do modelo
O modelo é uma **ferramenta de apoio**, não uma verdade absoluta. Falsos positivos e falsos negativos existem. O especialista humano deve avaliar a plausibilidade da previsão.

### 4. Ética em IA
Decisões com impacto direto em vidas humanas devem sempre ter um ser humano responsável identificado. O modelo amplia a capacidade do gestor, mas não o substitui.

---

## Implementação Técnica

### Schema de revisão

```python
class HumanReviewRequest(BaseModel):
    protocol_id: str
    decision: Literal["approved", "rejected", "revision_requested"]
    reviewer_name: Optional[str]
    reviewer_role: Optional[str]
    comments: Optional[str]
```

### Ciclo de vida do protocolo

| Status | Descrição |
|--------|-----------|
| `pending_review` | Gerado pelo agente, aguardando revisão humana |
| `approved` | Aprovado pelo gestor, pode ser executado |
| `revision_requested` | Gestor solicitou revisão — agente pode reformular |
| `rejected` | Rejeitado pelo gestor, arquivado sem execução |

### Endpoints

```
POST /llm-agent/protocol  → gera protocolo (status: pending_review)
POST /llm-agent/review    → gestor registra decisão (muda status)
GET  /llm-agent/protocols → lista protocolos (auditoria)
GET  /llm-agent/reviews   → lista revisões (rastreabilidade)
```

---

## Interface do Gestor

O dashboard React apresenta o protocolo gerado com:

1. **Resumo executivo** — texto claro para o gestor
2. **Ações recomendadas** — lista ordenada por prioridade
3. **Mensagem para UBS** — rascunho pronto para edição
4. **Botões de decisão** — Aprovar / Solicitar revisão / Rejeitar

---

## Rastreabilidade e Auditoria

Todas as revisões humanas são gravadas em:
- `data/processed/agent_logs/reviews/` — registros em JSON
- `data/processed/agent_logs/protocols/` — protocolos gerados

Cada registro inclui:
- `protocol_id` — identificador único
- `reviewer_name` e `reviewer_role` — quem decidiu
- `comments` — justificativa da decisão
- `reviewed_at` — timestamp da decisão

---

## Recomendações para Implantação

1. **Defina papéis e permissões**: Apenas gestores autorizados devem ter acesso ao botão de aprovação.

2. **Estabeleça SLAs de revisão**: Defina em quanto tempo um protocolo `pending_review` deve ser avaliado (sugestão: 24h).

3. **Comunique as limitações**: Treine os gestores para entender que o modelo é probabilístico — recall alto significa menos surtos perdidos, não zero.

4. **Revise periodicamente**: Audite as decisões de revisão/rejeição para calibrar o modelo com feedback real.

5. **Mantenha fallback humano**: Se o sistema ficar indisponível, o gestor deve ter acesso ao protocolo de ação manual baseado nos dados do InfoDengue diretamente.
