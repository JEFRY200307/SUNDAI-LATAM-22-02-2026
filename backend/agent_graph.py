"""
Grafo LangGraph — Pipeline de Detección de Fraude (3 Nodos)

       ┌──────────────────────────────────────────────────────────┐
       │                                                          │
   START → enrichment_node (A) → reasoning_node (B/LLM)         │
              │                       │                           │
              │             ┌─────────┼────────────┐              │
              │             │         │            │              │
              │           BAJO      MEDIO        ALTO             │
              │             │         │            │              │
              │        approve    facial_rec    action (C)        │
              │                      │                            │
              │               ┌──────┴──────┐                    │
              │               │             │                    │
              │          no pasa          pasa                   │
              │               │             │                    │
              │           action(C)     voice_bot                │
              │                        ┌────┴────┐               │
              │                        │         │               │
              │                   no confirma  confirma           │
              │                        │         │               │
              │                    action(C)  approve             │
              └──────────────────────────────────────────────────┘
                                     ↓ END
"""
import json
import os
import datetime

from langgraph.graph import StateGraph, START, END

from backend.schemas import AgentState

# ─── Importar nodos ───────────────────────────────────────────────────────────
from backend.behavioral_device.telemetry import device_signals_node
from backend.graph_intelligence.mule_scorer import mule_scoring_node
from backend.risk_decision.classifier import reasoning_node
from backend.hitl_trust.facial_recognition import facial_recognition_node
from backend.hitl_trust.verification import voice_bot_node
from backend.risk_decision.report_generator import action_node, approve_node


# ─── Nodo A: Enriquecimiento ─────────────────────────────────────────────────

def enrichment_node(state: dict) -> dict:
    """
    Nodo A: Recolecta TODAS las señales de identidad y comportamiento.
    Ejecuta device_signals + mule_scoring en un solo nodo.
    """
    # Device + behavioral signals
    device_result = device_signals_node(state)
    mule_result = mule_scoring_node(state)

    # Consolidar
    return {
        "device_signals": device_result["device_signals"],
        "mule_score": mule_result["mule_score"],
        "enrichment_summary": {
            "device_signals": device_result["device_signals"],
            "mule_score": mule_result["mule_score"],
        },
    }


# ─── Nodo terminal: escritura en log ─────────────────────────────────────────

def memory_write_node(state: dict) -> dict:
    """Persiste el resultado en el log de aprendizaje continuo."""
    log_path = os.getenv("LEARNING_LOG_PATH", "data/learning_log.json")
    timestamp = state.get("timestamp", datetime.datetime.utcnow().isoformat())

    event = {
        "transaction_id": state.get("transaction", {}).get("transaction_id"),
        "risk_level": state.get("risk_level", "UNKNOWN"),
        "risk_score": round(state.get("risk_score", 0.0), 4),
        "confidence": round(state.get("confidence", 0.0), 4),
        "risk_factors": state.get("risk_factors", []),
        "reasoning": state.get("reasoning", ""),
        "signals": {
            "device": state.get("device_signals", {}),
            "mule_score": state.get("mule_score", 0.0),
        },
        "hitl_required": state.get("hitl_required", False),
        "facial_score": state.get("facial_score"),
        "facial_passed": state.get("facial_passed"),
        "voice_verified": state.get("voice_verified"),
        "blocked": state.get("blocked", False),
        "report": state.get("report"),
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
        print(f"[MemoryWriter] Error: {e}")

    return {}


# ─── Routing condicional ─────────────────────────────────────────────────────

def _route_by_risk(state: dict) -> str:
    """Después del LLM: ruta según risk_level."""
    risk_level = state.get("risk_level", "BAJO")
    if risk_level == "ALTO":
        return "action"
    elif risk_level == "MEDIO":
        return "facial_recognition"
    return "approve"


def _route_after_facial(state: dict) -> str:
    """Después del reconocimiento facial: pasa o no pasa."""
    if state.get("facial_passed", False):
        return "voice_bot"
    return "action"


def _route_after_voice(state: dict) -> str:
    """Después del voice bot: confirma o no confirma."""
    if state.get("voice_verified", False):
        return "approve"
    return "action"


# ─── Construcción del grafo ──────────────────────────────────────────────────

def build_fraud_graph() -> StateGraph:
    """Construye y compila el grafo LangGraph de 3 nodos + HITL."""
    graph = StateGraph(AgentState)

    # Registrar nodos
    graph.add_node("enrichment", enrichment_node)              # Nodo A
    graph.add_node("reasoning", reasoning_node)                # Nodo B (LLM)
    graph.add_node("facial_recognition", facial_recognition_node)  # HITL
    graph.add_node("voice_bot", voice_bot_node)                # HITL
    graph.add_node("action", action_node)                      # Nodo C
    graph.add_node("approve", approve_node)                    # Terminal OK
    graph.add_node("memory_write", memory_write_node)          # Persistencia

    # Flujo principal
    graph.add_edge(START, "enrichment")
    graph.add_edge("enrichment", "reasoning")

    # Condicional después del LLM
    graph.add_conditional_edges(
        "reasoning",
        _route_by_risk,
        {
            "approve": "approve",
            "action": "action",
            "facial_recognition": "facial_recognition",
        },
    )

    # Condicional después de facial recognition
    graph.add_conditional_edges(
        "facial_recognition",
        _route_after_facial,
        {
            "voice_bot": "voice_bot",
            "action": "action",
        },
    )

    # Condicional después de voice bot
    graph.add_conditional_edges(
        "voice_bot",
        _route_after_voice,
        {
            "approve": "approve",
            "action": "action",
        },
    )

    # Todos los terminales → memory_write → END
    graph.add_edge("action", "memory_write")
    graph.add_edge("approve", "memory_write")
    graph.add_edge("memory_write", END)

    return graph.compile()


# Instancia global compilada
fraud_graph = build_fraud_graph()
