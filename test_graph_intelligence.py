"""
Tests para Rol 2 — Graph Fraud & Intelligence
Verifica grafo, detector, memoria de sospechosos, scorer, y persistencia.
"""
import os
import json
import time

from backend.graph_intelligence.graph_model import (
    get_transaction_graph,
    add_transaction,
    _GRAPH,
)
from backend.graph_intelligence.graph_detector import GraphFraudDetector
from backend.graph_intelligence.suspicious_memory import (
    load_suspicious_nodes,
    mark_suspicious,
    is_known_suspicious,
    MEMORY_PATH,
)
from backend.graph_intelligence.mule_scorer import score_mule_risk, score_mule_risk_details
import backend.graph_intelligence.graph_model as gm


# ═══════════════════════════════════════════════════════════════════════
# Fixture: reset grafo singleton entre tests
# ═══════════════════════════════════════════════════════════════════════

def _reset_graph():
    """Fuerza recreación del singleton para tests aislados."""
    gm._GRAPH = None


def _cleanup_memory():
    """Limpia archivo de memoria de sospechosos si existe."""
    if os.path.exists(MEMORY_PATH):
        os.remove(MEMORY_PATH)


# ═══════════════════════════════════════════════════════════════════════
# Graph Model tests
# ═══════════════════════════════════════════════════════════════════════

def test_graph_structure():
    """El grafo de demo tiene nodos y aristas esperados."""
    _reset_graph()
    G = get_transaction_graph()
    assert G.number_of_nodes() >= 12
    assert G.number_of_edges() >= 10
    assert G.has_node("ACC-MULE-001")
    assert G.has_node("ACC-BLOCKED-001")
    assert G.has_node("ACC-NORMAL-001")


def test_graph_singleton():
    """get_transaction_graph() retorna siempre el mismo objeto."""
    _reset_graph()
    g1 = get_transaction_graph()
    g2 = get_transaction_graph()
    assert g1 is g2


def test_graph_persistence_across_transactions():
    """add_transaction() modifica el grafo en vivo, no se resetea."""
    _reset_graph()
    G = get_transaction_graph()
    initial_nodes = G.number_of_nodes()
    initial_edges = G.number_of_edges()

    add_transaction(G, "ACC-NEW-SENDER", "ACC-NEW-RECEIVER", 100)
    assert G.number_of_nodes() == initial_nodes + 2
    assert G.number_of_edges() == initial_edges + 1

    add_transaction(G, "ACC-NEW-SENDER2", "ACC-NEW-RECEIVER2", 200)
    assert G.number_of_nodes() == initial_nodes + 4
    assert G.number_of_edges() == initial_edges + 2


def test_edge_count_aggregation():
    """Repetir sender→receiver incrementa count, no crea arista nueva."""
    _reset_graph()
    G = get_transaction_graph()
    initial_edges = G.number_of_edges()

    add_transaction(G, "ACC-REPEAT-A", "ACC-REPEAT-B", 100)
    assert G[" ACC-REPEAT-A".strip()]["ACC-REPEAT-B"]["count"] == 1

    add_transaction(G, "ACC-REPEAT-A", "ACC-REPEAT-B", 200)
    assert G.number_of_edges() == initial_edges + 1  # sigue siendo 1 arista
    assert G["ACC-REPEAT-A"]["ACC-REPEAT-B"]["count"] == 2
    assert G["ACC-REPEAT-A"]["ACC-REPEAT-B"]["total_amount"] == 300


# ═══════════════════════════════════════════════════════════════════════
# GraphFraudDetector tests
# ═══════════════════════════════════════════════════════════════════════

def test_centrality_detection():
    """ACC-MULE-001 tiene alta centralidad por sus muchas conexiones."""
    _reset_graph()
    G = get_transaction_graph()
    detector = GraphFraudDetector(G)
    result = detector.analyze("ACC-MULE-001")
    assert result["graph_metrics"]["in_degree"] >= 5
    assert "high_in_degree" in result["reasons"]


def test_cascade_detection():
    """Cadena MULE-001→002→003→004 detecta cascada."""
    _reset_graph()
    G = get_transaction_graph()
    detector = GraphFraudDetector(G)
    result = detector.analyze("ACC-MULE-002")
    assert result["graph_metrics"]["cascade_depth"] >= 2
    assert "cascade_member" in result["reasons"]


def test_frequency_detection():
    """ACC-MULE-001 tiene in_degree >= 5 → high_in_degree."""
    _reset_graph()
    G = get_transaction_graph()
    detector = GraphFraudDetector(G)
    result = detector.analyze("ACC-MULE-001")
    assert result["graph_metrics"]["in_degree"] >= 5


def test_blacklist_detection():
    """Cuenta blacklisted → score 1.0 directo."""
    _reset_graph()
    G = get_transaction_graph()
    detector = GraphFraudDetector(G)
    result = detector.analyze("ACC-BLOCKED-001")
    assert result["mule_score"] == 1.0
    assert "blacklisted_account" in result["reasons"]


def test_clean_account():
    """Cuenta normal aislada → score bajo."""
    _reset_graph()
    G = get_transaction_graph()
    detector = GraphFraudDetector(G)
    result = detector.analyze("ACC-NORMAL-005")
    assert result["mule_score"] < 0.5


def test_unknown_account():
    """Cuenta inexistente → score 0."""
    _reset_graph()
    G = get_transaction_graph()
    detector = GraphFraudDetector(G)
    result = detector.analyze("ACC-DOES-NOT-EXIST")
    assert result["mule_score"] == 0.0
    assert result["reasons"] == []


# ═══════════════════════════════════════════════════════════════════════
# Suspicious Memory tests
# ═══════════════════════════════════════════════════════════════════════

def test_suspicious_memory_mark_and_read():
    """Marcar y recuperar un nodo sospechoso."""
    _cleanup_memory()
    mark_suspicious("ACC-TEST-MEMORY", 0.75, ["test_reason"])
    score = is_known_suspicious("ACC-TEST-MEMORY")
    assert score is not None
    assert score == 0.75
    _cleanup_memory()


def test_suspicious_memory_anti_drop():
    """Anti-bajada: final = max(current, prev * 0.7)."""
    _cleanup_memory()
    mark_suspicious("ACC-DROP-TEST", 0.90, ["high_risk"])
    # Ahora viene una corrida limpia con score 0.1
    final = mark_suspicious("ACC-DROP-TEST", 0.10, ["clean"])
    assert final >= 0.90 * 0.7  # no cae debajo de 0.63
    assert final > 0.10
    _cleanup_memory()


# ═══════════════════════════════════════════════════════════════════════
# Integration: mule_scorer
# ═══════════════════════════════════════════════════════════════════════

def test_mule_scorer_legacy_float():
    """score_mule_risk() retorna float (compatibilidad Rol 1)."""
    _reset_graph()
    _cleanup_memory()
    result = score_mule_risk("ACC-NORMAL-001")
    assert isinstance(result, float)
    assert 0.0 <= result <= 1.0
    _cleanup_memory()


def test_mule_scorer_details_dict():
    """score_mule_risk_details() retorna dict con todas las señales."""
    _reset_graph()
    _cleanup_memory()
    result = score_mule_risk_details(
        receiver_account="ACC-MULE-001",
        sender_account="ACC-SENDER-001",
        amount=1000,
    )
    assert isinstance(result, dict)
    assert "mule_score" in result
    assert "reasons" in result
    assert "graph_metrics" in result
    assert result["mule_score"] > 0.3
    assert len(result["reasons"]) >= 1
    _cleanup_memory()


def test_mule_scorer_mule_high_score():
    """Cuenta mula conocida → score alto con reasons."""
    _reset_graph()
    _cleanup_memory()
    result = score_mule_risk_details(receiver_account="ACC-MULE-001")
    assert result["mule_score"] >= 0.5
    assert len(result["reasons"]) >= 2
    _cleanup_memory()
