"""
ROL 3 — DeviceRisk Module
Evalúa riesgo a nivel de dispositivo: emulador, root/jailbreak, IP anómala, fingerprint.
Retorna score + reasons para explainability.
"""
import hashlib

# ─── Pesos explícitos por señal ───────────────────────────────────────────────
DEVICE_WEIGHTS: dict[str, float] = {
    "emulator":    0.30,
    "rooted":      0.30,
    "anomalous_ip": 0.25,
}


def evaluate_device_risk(
    device_id: str | None = None,
    is_emulator: bool = False,
    is_rooted: bool = False,
    anomalous_ip: bool = False,
) -> dict:
    """
    Evalúa riesgo del dispositivo a partir de flags enviados por el frontend.

    Args:
        device_id:    Identificador del dispositivo (para fingerprint).
        is_emulator:  True si el frontend detecta un emulador.
        is_rooted:    True si el dispositivo tiene root/jailbreak.
        anomalous_ip: True si la IP es anómala (VPN, Tor, proxy).

    Returns:
        dict con device_risk_score (0–1), reasons, y señales individuales.
    """
    score = 0.0
    reasons: list[str] = []

    if is_emulator:
        score += DEVICE_WEIGHTS["emulator"]
        reasons.append("emulator_detected")

    if is_rooted:
        score += DEVICE_WEIGHTS["rooted"]
        reasons.append("rooted_device")

    if anomalous_ip:
        score += DEVICE_WEIGHTS["anomalous_ip"]
        reasons.append("anomalous_ip")

    # Fingerprint derivado del device_id
    fingerprint = _generate_fingerprint(device_id or "unknown")

    return {
        "is_emulator": is_emulator,
        "is_rooted": is_rooted,
        "anomalous_ip": anomalous_ip,
        "device_fingerprint": fingerprint,
        "device_risk_score": min(score, 1.0),
        "device_reasons": reasons,
    }


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _generate_fingerprint(device_id: str) -> str:
    """Genera fingerprint SHA-256 truncado del device_id."""
    return hashlib.sha256(device_id.encode()).hexdigest()[:16]
