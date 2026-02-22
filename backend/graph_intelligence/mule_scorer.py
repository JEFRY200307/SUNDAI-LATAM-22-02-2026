"""
ROL 2 — Graph Fraud & Intelligence
Calcula el Mule Risk Score usando análisis real de grafo.
Mantiene compatibilidad: score_mule_risk() → float (legacy),
score_mule_risk_details() → dict (nuevo, con métricas + reasons).
"""
from backend.graph_intelligence.graph_model import (
    get_transaction_graph,
    add_transaction,
)
from backend.graph_intelligence.graph_detector import GraphFraudDetector
from backend.graph_intelligence.suspicious_memory import (
    is_known_suspicious,
    mark_suspicious,
)

# Umbral para persistir en memoria de sospechosos
SUSPICION_THRESHOLD = 0.3


def score_mule_risk(receiver_account: str) -> float:
    """
    API legacy — retorna solo el float del MuleScore.
    Compatible con classifier.py (Rol 1) sin cambios.
    """
    details = score_mule_risk_details(
        receiver_account=receiver_account,
    )
    return details["mule_score"]


def score_mule_risk_details(
    receiver_account: str,
    sender_account: str = "",
    amount: float = 0.0,
) -> dict:
    """
    Calcula MuleScore con análisis real de grafo + memoria de sospechosos.

    Pipeline:
      1. Obtener grafo singleton
      2. Agregar transacción actual al grafo (si hay sender)
      3. Analizar con GraphFraudDetector
      4. Consultar memoria de sospechosos (boost anti-bajada)
      5. Persistir si es sospechoso

    Returns:
        dict con mule_score, reasons, graph_metrics.
    """
    # 1. Grafo singleton
    graph = get_transaction_graph()

<<<<<<< HEAD
    return KNOWN_MULE_NETWORK.get(receiver_account, 0.0)


# ─── LangGraph Node Wrapper ───────────────────────────────────────────────────

def mule_scoring_node(state: dict) -> dict:
    """Nodo LangGraph: calcula el mule risk score de la cuenta destino."""
    tx = state.get("transaction", {})
    score = score_mule_risk(receiver_account=tx.get("receiver_account", ""))
    return {"mule_score": score}
=======
    # 2. Agregar transacción actual (solo si tenemos sender)
    if sender_account and receiver_account and amount > 0:
        add_transaction(graph, sender_account, receiver_account, amount)

    # 3. Análisis del grafo
    detector = GraphFraudDetector(graph)
    result = detector.analyze(receiver_account)

    # 4. Memoria de sospechosos → boost anti-bajada
    prev_score = is_known_suspicious(receiver_account)
    if prev_score is not None:
        boosted = max(result["mule_score"], prev_score * 0.7)
        if boosted > result["mule_score"]:
            result["mule_score"] = round(boosted, 4)
            if "memory_boost" not in result["reasons"]:
                result["reasons"].append("memory_boost")

    # 5. Persistir si sospechoso
    if result["mule_score"] >= SUSPICION_THRESHOLD:
        final = mark_suspicious(
            account=receiver_account,
            current_score=result["mule_score"],
            reasons=result["reasons"],
        )
        result["mule_score"] = round(final, 4)

    return result
>>>>>>> behavioral-device
