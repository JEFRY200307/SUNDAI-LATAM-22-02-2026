"""
ROL 2 — Suspicious Node Memory
Persistencia ligera en JSON de cuentas sospechosas.
Implementa boost anti-bajada: final = max(current, prev * 0.7)
"""
import json
import os
import time

MEMORY_PATH = os.getenv("SUSPICIOUS_NODES_PATH", "data/suspicious_nodes.json")


def load_suspicious_nodes() -> dict:
    """Carga el registro de nodos sospechosos desde disco."""
    try:
        with open(MEMORY_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_suspicious_nodes(data: dict) -> None:
    """Persiste el registro en disco."""
    os.makedirs(os.path.dirname(MEMORY_PATH) or ".", exist_ok=True)
    with open(MEMORY_PATH, "w") as f:
        json.dump(data, f, indent=2)


def is_known_suspicious(account: str) -> float | None:
    """
    Retorna el score previo de una cuenta sospechosa, o None si no existe.
    """
    nodes = load_suspicious_nodes()
    entry = nodes.get(account)
    if entry is None:
        return None
    return entry.get("mule_score", 0.0)


def mark_suspicious(
    account: str,
    current_score: float,
    reasons: list[str],
) -> float:
    """
    Registra o actualiza una cuenta sospechosa.
    Aplica boost anti-bajada: final = max(current, prev * 0.7).

    Args:
        account:       Identificador de la cuenta.
        current_score: Score calculado en esta transacción.
        reasons:       Lista de razones detectadas.

    Returns:
        float: Score final después del boost.
    """
    nodes = load_suspicious_nodes()
    prev_score = nodes.get(account, {}).get("mule_score", 0.0)

    # Anti-bajada: la sospecha no desaparece rápido
    final_score = max(current_score, prev_score * 0.7)

    nodes[account] = {
        "mule_score": round(final_score, 4),
        "reasons": reasons,
        "hit_count": nodes.get(account, {}).get("hit_count", 0) + 1,
        "last_seen": time.time(),
    }

    _save_suspicious_nodes(nodes)
    return final_score
