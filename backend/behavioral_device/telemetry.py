"""
ROL 3 — Behavioral & Device Intelligence
Genera señales de dispositivo y comportamiento del usuario.
"""
import hashlib
import random

# ─── IPs y User-Agents considerados anómalos ─────────────────────────────────
ANOMALOUS_IPS: set[str] = {
    "10.0.0.1", "192.168.1.1",       # IPs privadas usadas externamente
    "185.220.101.1",                  # Nodo Tor conocido (simulado)
    "45.33.32.156",                   # IP de VPN conocida (simulado)
}

EMULATOR_UA_KEYWORDS: list[str] = [
    "emulator", "android sdk", "genymotion", "bluestacks", "nox",
]


def get_device_signals(
    device_id: str | None,
    ip_address: str | None,
    user_agent: str | None,
) -> dict:
    """
    Analiza los datos del dispositivo y retorna señales de riesgo.

    Returns:
        dict con claves:
            - is_emulator (bool)
            - anomalous_ip (bool)
            - suspicious_typing_speed (bool)
            - device_fingerprint (str)
    """
    ua_lower = (user_agent or "").lower()
    ip = ip_address or ""

    is_emulator = any(kw in ua_lower for kw in EMULATOR_UA_KEYWORDS)
    anomalous_ip = ip in ANOMALOUS_IPS

    # Simular velocidad de tipeo — en producción vendría del frontend
    suspicious_typing_speed = _simulate_typing_anomaly(device_id)

    # Fingerprint derivado del device_id
    fingerprint = _generate_fingerprint(device_id or "unknown")

    return {
        "is_emulator": is_emulator,
        "anomalous_ip": anomalous_ip,
        "suspicious_typing_speed": suspicious_typing_speed,
        "device_fingerprint": fingerprint,
    }


# ─── Helpers privados ─────────────────────────────────────────────────────────

def _simulate_typing_anomaly(device_id: str | None) -> bool:
    """Simula detección de velocidad de tipeo robótica con seed determinístico."""
    if not device_id:
        return False
    seed = int(hashlib.md5(device_id.encode()).hexdigest(), 16) % 100
    return seed < 15  # ~15% de probabilidad de tipeo sospechoso


def _generate_fingerprint(device_id: str) -> str:
    return hashlib.sha256(device_id.encode()).hexdigest()[:16]


# ─── LangGraph Node Wrapper ───────────────────────────────────────────────────

def device_signals_node(state: dict) -> dict:
    """Nodo LangGraph: extrae señales de dispositivo de la transacción."""
    tx = state.get("transaction", {})
    signals = get_device_signals(
        device_id=tx.get("device_id"),
        ip_address=tx.get("ip_address"),
        user_agent=tx.get("user_agent"),
    )
    return {"device_signals": signals}
