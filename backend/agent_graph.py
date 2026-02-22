"""
Grafo LangGraph — Pipeline de Detección de Fraude

START ──┬──► device_signals (Rol 3) ──┐
        └──► mule_scoring  (Rol 2) ──┤
                                      ├──► risk_engine (Rol 1)
                                      │         │
                                      │   decision_policy
                                      │    ╱          ╲
                                   FRAUD/POSSIBLE    NO_FRAUD
                                      │                │
                                   hitl_verify         │
                                      │                │
                                      └───► xai_explain ◄──┘
                                               │
                                          memory_write
                                               │
                                              END
"""
import json
import os
import datetime

from langgraph.graph import StateGraph, START, END

from backend.schemas import AgentState

# ─── Importar nodos ───────────────────────────────────────────────────────────
from backend.behavioral_device.telemetry import device_signals_node
from backend.graph_intelligence.mule_scorer import mule_scoring_node
from backend.risk_decision.classifier import risk_engine_node
from backend.hitl_trust.verification import hitl_node
from backend.risk_decision.xai_explainer import xai_explain_node


# ─── Nodos auxiliares ─────────────────────────────────────────────────────────

def decision_policy_node(state: dict) -> dict:
    """Clasifica la decisión a partir del risk_score y los umbrales."""
    risk_score = state.get("risk_score", 0.0)
    t_fraud = float(os.getenv("RISK_THRESHOLD_FRAUD", "0.75"))
    t_possible = float(os.getenv("RISK_THRESHOLD_POSSIBLE", "0.45"))

    if risk_score >= t_fraud:
        decision = "FRAUD"
    elif risk_score >= t_possible:
        decision = "POSSIBLE_FRAUD"
    else:
        decision = "NO_FRAUD"

    return {"decision": decision}


def memory_write_node(state: dict) -> dict:
    """Persiste el resultado en el log de aprendizaje continuo."""
    log_path = os.getenv("LEARNING_LOG_PATH", "data/learning_log.json")
    timestamp = datetime.datetime.utcnow().isoformat()

    event = {
        "transaction_id": state.get("transaction", {}).get("transaction_id"),
        "risk_score": round(state.get("risk_score", 0.0), 4),
        "decision": state.get("decision", "UNKNOWN"),
        "risk_factors": state.get("risk_factors", []),
        "signals": {
            "device": state.get("device_signals", {}),
            "mule_score": state.get("mule_score", 0.0),
        },
        "hitl_triggered": state.get("hitl_triggered", False),
        "hitl_action": state.get("hitl_action"),
        "explanation": state.get("explanation"),
        "timestamp": timestamp,
    }

    try:
        os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)
        try:
            with open(log_path, "r") as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []
        logs.append(event)
        with open(log_path, "w") as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        print(f"[MemoryWriter] Error escribiendo log: {e}")

    return {"timestamp": timestamp}


# ─── Routing condicional ──────────────────────────────────────────────────────

def _needs_hitl(state: dict) -> str:
    """Decide si se requiere verificación HITL."""
    decision = state.get("decision", "NO_FRAUD")
    if decision in ("FRAUD", "POSSIBLE_FRAUD"):
        return "hitl_verify"
    return "xai_explain"


# ─── Construcción del grafo ───────────────────────────────────────────────────

def build_fraud_graph() -> StateGraph:
    """Construye y compila el grafo LangGraph de detección de fraude."""
    graph = StateGraph(AgentState)

    # Registrar nodos
    graph.add_node("device_signals", device_signals_node)
    graph.add_node("mule_scoring", mule_scoring_node)
    graph.add_node("risk_engine", risk_engine_node)
    graph.add_node("decision_policy", decision_policy_node)
    graph.add_node("hitl_verify", hitl_node)
    graph.add_node("xai_explain", xai_explain_node)
    graph.add_node("memory_write", memory_write_node)

    # Edges desde START — paralelo
    graph.add_edge(START, "device_signals")
    graph.add_edge(START, "mule_scoring")

    # Convergencia en risk_engine
    graph.add_edge("device_signals", "risk_engine")
    graph.add_edge("mule_scoring", "risk_engine")

    # Risk engine → decision
    graph.add_edge("risk_engine", "decision_policy")

    # Condicional: HITL o directamente a XAI
    graph.add_conditional_edges(
        "decision_policy",
        _needs_hitl,
        {
            "hitl_verify": "hitl_verify",
            "xai_explain": "xai_explain",
        },
    )

    # HITL → XAI
    graph.add_edge("hitl_verify", "xai_explain")

    # XAI → Memory → END
    graph.add_edge("xai_explain", "memory_write")
    graph.add_edge("memory_write", END)

    return graph.compile()


# Instancia global compilada
fraud_graph = build_fraud_graph()
