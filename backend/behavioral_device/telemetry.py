"""
ROL 3 — Behavioral & Device Intelligence
Orquesta DeviceRisk + BehavioralRisk y genera las señales agregadas
que consume el Risk Engine (Rol 1).

Mantiene la interfaz `get_device_signals()` y el wrapper LangGraph
`device_signals_node()` por compatibilidad con agent_graph.py.
"""
from backend.behavioral_device.device_risk import evaluate_device_risk
from backend.behavioral_device.behavioral_risk import evaluate_behavioral_risk

# ─── IPs y User-Agents considerados anómalos ─────────────────────────────────
ANOMALOUS_IPS: set[str] = {
    "10.0.0.1", "192.168.1.1",
    "185.220.101.1",
    "45.33.32.156",
}

EMULATOR_UA_KEYWORDS: list[str] = [
    "emulator", "android sdk", "genymotion", "bluestacks", "nox",
]


def get_device_signals(
    device_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    amount: float = 0.0,
    interaction_time_ms: int | None = None,
    navigation_steps: int | None = None,
    historical_amounts: list[float] | None = None,
) -> dict:
    """
    Recolecta TODAS las señales de dispositivo y comportamiento.

    Detecta automáticamente emuladores e IPs anómalas a partir de
    user_agent e ip_address, luego delega a DeviceRisk y BehavioralRisk.

    Retorna un dict compatible con classifier.py (Rol 1) que incluye:
      - Claves originales: is_emulator, anomalous_ip, suspicious_typing_speed
      - Claves nuevas: is_rooted, device_risk_score, behavioral_risk_score,
        suspicious_navigation, suspicious_amount_pattern, reasons
    """
    # ── Detección automática de flags ─────────────────────────────────────────
    ua_lower = (user_agent or "").lower()
    ip = ip_address or ""

    is_emulator = any(kw in ua_lower for kw in EMULATOR_UA_KEYWORDS)
    anomalous_ip = ip in ANOMALOUS_IPS

    # ── 1. Riesgo de dispositivo ──────────────────────────────────────────────
    device = evaluate_device_risk(
        device_id=device_id,
        is_emulator=is_emulator,
        is_rooted=False,  # En producción vendría del frontend
        anomalous_ip=anomalous_ip,
    )

    # ── 2. Riesgo de comportamiento ──────────────────────────────────────────
    behavioral = evaluate_behavioral_risk(
        amount=amount,
        interaction_time_ms=interaction_time_ms,
        navigation_steps=navigation_steps,
        historical_amounts=historical_amounts,
    )

    # ── 3. Señales agregadas para Risk Engine ────────────────────────────────
    all_reasons = device["device_reasons"] + behavioral["behavioral_reasons"]

    return {
        # Claves que ya consume classifier.py (Rol 1) — NO ROMPER
        "is_emulator": device["is_emulator"],
        "anomalous_ip": device["anomalous_ip"],
        "suspicious_typing_speed": behavioral["suspicious_interaction_speed"],

        # Señales expandidas
        "is_rooted": device["is_rooted"],
        "device_fingerprint": device["device_fingerprint"],
        "device_risk_score": device["device_risk_score"],
        "behavioral_risk_score": behavioral["behavioral_risk_score"],
        "suspicious_navigation": behavioral["suspicious_navigation"],
        "suspicious_amount_pattern": behavioral["suspicious_amount_pattern"],

        # Explainability
        "reasons": all_reasons,
    }


# ─── LangGraph Node Wrapper ───────────────────────────────────────────────────

def device_signals_node(state: dict) -> dict:
    """Nodo LangGraph: extrae señales de dispositivo y comportamiento."""
    tx = state.get("transaction", {})
    signals = get_device_signals(
        device_id=tx.get("device_id"),
        ip_address=tx.get("ip_address"),
        user_agent=tx.get("user_agent"),
        amount=tx.get("amount", 0.0),
        interaction_time_ms=tx.get("interaction_time_ms"),
        navigation_steps=tx.get("navigation_steps"),
        historical_amounts=tx.get("historical_amounts"),
    )
    return {"device_signals": signals}
