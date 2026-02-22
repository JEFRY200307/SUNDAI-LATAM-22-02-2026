"""
ROL 2 — Graph Fraud & Intelligence
Calcula el Mule Risk Score de la cuenta destino.
"""

# ─── Base de datos simulada de redes sospechosas ──────────────────────────────
# Formato: { cuenta_destino: mule_score (0.0 – 1.0) }
KNOWN_MULE_NETWORK: dict[str, float] = {
    "ACC-MULE-001": 0.95,
    "ACC-MULE-002": 0.88,
    "ACC-MULE-003": 0.72,
    "ACC-MULE-004": 0.60,
    "ACC-SUSPICIOUS-01": 0.50,
}

# Cuentas en lista negra directa → score máximo
BLACKLIST: set[str] = {
    "ACC-BLOCKED-001",
    "ACC-BLOCKED-002",
}


def score_mule_risk(receiver_account: str) -> float:
    """
    Retorna un Mule Risk Score entre 0.0 y 1.0 para la cuenta destino.

    - 1.0 = cuenta en lista negra confirmada
    - 0.0 = cuenta sin antecedentes sospechosos

    Args:
        receiver_account: Identificador de la cuenta destino.

    Returns:
        float: Mule risk score entre 0.0 y 1.0.
    """
    if receiver_account in BLACKLIST:
        return 1.0

    return KNOWN_MULE_NETWORK.get(receiver_account, 0.0)


# ─── LangGraph Node Wrapper ───────────────────────────────────────────────────

def mule_scoring_node(state: dict) -> dict:
    """Nodo LangGraph: calcula el mule risk score de la cuenta destino."""
    tx = state.get("transaction", {})
    score = score_mule_risk(receiver_account=tx.get("receiver_account", ""))
    return {"mule_score": score}
