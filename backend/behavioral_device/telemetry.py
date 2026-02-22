"""
ROL 3 — Behavioral & Device Intelligence
Orquesta DeviceRisk + BehavioralRisk y genera las señales agregadas
que consume el Risk Engine (Rol 1).

Mantiene la interfaz `get_device_signals()` por compatibilidad con
classifier.py — ahora internamente agrega señales de comportamiento.
"""
from backend.behavioral_device.device_risk import evaluate_device_risk
from backend.behavioral_device.behavioral_risk import evaluate_behavioral_risk


def get_device_signals(
    device_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    is_emulator: bool = False,
    is_rooted: bool = False,
    anomalous_ip: bool = False,
    interaction_time_ms: int | None = None,
    navigation_steps: int | None = None,
    amount: float = 0.0,
    historical_amounts: list[float] | None = None,
) -> dict:
    """
    Recolecta TODAS las señales de dispositivo y comportamiento.

    Retorna un dict compatible con classifier.py (Rol 1) que incluye:
      - Claves originales: is_emulator, anomalous_ip, suspicious_typing_speed
      - Claves nuevas: is_rooted, device_risk_score, behavioral_risk_score,
        suspicious_navigation, suspicious_amount_pattern, reasons
    """
    # ── 1. Riesgo de dispositivo ──────────────────────────────────────────────
    device = evaluate_device_risk(
        device_id=device_id,
        is_emulator=is_emulator,
        is_rooted=is_rooted,
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

        # Señales expandidas (Rol 1 puede incorporarlas a futuro)
        "is_rooted": device["is_rooted"],
        "device_fingerprint": device["device_fingerprint"],
        "device_risk_score": device["device_risk_score"],
        "behavioral_risk_score": behavioral["behavioral_risk_score"],
        "suspicious_navigation": behavioral["suspicious_navigation"],
        "suspicious_amount_pattern": behavioral["suspicious_amount_pattern"],

        # Explainability
        "reasons": all_reasons,
    }
