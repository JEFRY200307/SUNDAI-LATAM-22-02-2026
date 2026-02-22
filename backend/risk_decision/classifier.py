"""
ROL 1 — Risk & Decision Engine
Clasificador de riesgo en tres niveles: NO_FRAUD, POSSIBLE_FRAUD, FRAUD
"""
import os
from backend.risk_decision.rules import RISK_WEIGHTS, THRESHOLDS


def classify_risk(
    amount: float,
    device_signals: dict,
    mule_score: float,
) -> tuple[float, str]:
    """
    Consolida todas las señales y calcula el risk score final.

    Args:
        amount: Monto de la transacción.
        device_signals: Dict con señales de dispositivo (Rol 3).
        mule_score: Score de riesgo del destinatario (Rol 2).

    Returns:
        Tuple (risk_score: float 0‒1, decision: str)
    """
    score = 0.0

    # ── Señal 1: Monto elevado ────────────────────────────────────────────────
    if amount > 10_000:
        score += RISK_WEIGHTS["high_amount"]
    elif amount > 3_000:
        score += RISK_WEIGHTS["medium_amount"]

    # ── Señal 2: Riesgo de mula del destinatario ──────────────────────────────
    score += mule_score * RISK_WEIGHTS["mule_score"]

    # ── Señal 3: Emulador detectado ───────────────────────────────────────────
    if device_signals.get("is_emulator"):
        score += RISK_WEIGHTS["emulator"]

    # ── Señal 4: IP anómala ───────────────────────────────────────────────────
    if device_signals.get("anomalous_ip"):
        score += RISK_WEIGHTS["anomalous_ip"]

    # ── Señal 5: Velocidad de tipeo sospechosa ────────────────────────────────
    if device_signals.get("suspicious_typing_speed"):
        score += RISK_WEIGHTS["suspicious_typing"]

    # Normalizar score a [0, 1]
    risk_score = min(score, 1.0)

    # ── Clasificación final ───────────────────────────────────────────────────
    if risk_score >= THRESHOLDS["fraud"]:
        decision = "FRAUD"
    elif risk_score >= THRESHOLDS["possible_fraud"]:
        decision = "POSSIBLE_FRAUD"
    else:
        decision = "NO_FRAUD"

    return risk_score, decision


# ─── LangGraph Node Wrapper ───────────────────────────────────────────────────

def risk_engine_node(state: dict) -> dict:
    """Nodo LangGraph: consolida señales y calcula risk score + factores."""
    tx = state.get("transaction", {})
    device_signals = state.get("device_signals", {})
    mule_score = state.get("mule_score", 0.0)

    risk_score, _ = classify_risk(
        amount=tx.get("amount", 0.0),
        device_signals=device_signals,
        mule_score=mule_score,
    )

    # Recopilar factores de riesgo activos
    risk_factors = []
    amount = tx.get("amount", 0.0)
    if amount > 10_000:
        risk_factors.append("high_amount")
    elif amount > 3_000:
        risk_factors.append("medium_amount")
    if mule_score > 0.5:
        risk_factors.append("mule_score")
    if device_signals.get("is_emulator"):
        risk_factors.append("emulator")
    if device_signals.get("anomalous_ip"):
        risk_factors.append("anomalous_ip")
    if device_signals.get("suspicious_typing_speed"):
        risk_factors.append("suspicious_typing")

    return {
        "risk_score": min(risk_score, 1.0),
        "risk_factors": risk_factors,
    }
