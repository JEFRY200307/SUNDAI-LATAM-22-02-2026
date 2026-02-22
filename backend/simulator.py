"""
Simulador de transacciones para el endpoint /simulate/batch.
Genera transacciones aleatorias con distintos perfiles de riesgo.
"""
import random
import uuid


# ─── Pools de datos simulados ────────────────────────────────────────────────

CLEAN_ACCOUNTS = [
    "ACC-CLEAN-001", "ACC-CLEAN-002", "ACC-CLEAN-003",
    "ACC-CLEAN-004", "ACC-CLEAN-005",
]

MULE_ACCOUNTS = [
    "ACC-MULE-001", "ACC-MULE-002", "ACC-MULE-003", "ACC-MULE-004",
    "ACC-SUSPICIOUS-01",
]

BLOCKED_ACCOUNTS = ["ACC-BLOCKED-001", "ACC-BLOCKED-002"]

SENDER_ACCOUNTS = [
    "USER-001", "USER-002", "USER-003", "USER-004", "USER-005",
    "USER-006", "USER-007", "USER-008",
]

NORMAL_IPS = ["203.0.113.10", "198.51.100.22", "172.217.14.100", None]
ANOMALOUS_IPS = ["10.0.0.1", "185.220.101.1", "45.33.32.156"]

NORMAL_UAS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120",
    None,
]
EMULATOR_UAS = [
    "Mozilla/5.0 (Linux; Android SDK Emulator)",
    "BlueStacks/5.0",
]

DEVICE_IDS = ["DEV-A1", "DEV-B2", "DEV-C3", "DEV-D4", "DEV-E5", None]


def generate_random_transaction() -> dict:
    """
    Genera una transacción aleatoria con perfil de riesgo variado.

    Returns:
        dict compatible con TransactionIntent.
    """
    # Elegir perfil: 40% limpio, 35% sospechoso, 25% fraude
    profile = random.choices(
        ["clean", "suspicious", "fraud"],
        weights=[40, 35, 25],
        k=1,
    )[0]

    tx_id = f"SIM-{uuid.uuid4().hex[:8].upper()}"
    sender = random.choice(SENDER_ACCOUNTS)

    if profile == "clean":
        receiver = random.choice(CLEAN_ACCOUNTS)
        amount = round(random.uniform(10, 2500), 2)
        ip = random.choice(NORMAL_IPS)
        ua = random.choice(NORMAL_UAS)
    elif profile == "suspicious":
        receiver = random.choice(MULE_ACCOUNTS)
        amount = round(random.uniform(1000, 8000), 2)
        ip = random.choice(NORMAL_IPS + ANOMALOUS_IPS)
        ua = random.choice(NORMAL_UAS + EMULATOR_UAS)
    else:  # fraud
        receiver = random.choice(MULE_ACCOUNTS + BLOCKED_ACCOUNTS)
        amount = round(random.uniform(5000, 50000), 2)
        ip = random.choice(ANOMALOUS_IPS)
        ua = random.choice(EMULATOR_UAS + NORMAL_UAS[:1])

    device_id = random.choice(DEVICE_IDS)

    return {
        "transaction_id": tx_id,
        "sender_account": sender,
        "receiver_account": receiver,
        "amount": amount,
        "currency": "USD",
        "device_id": device_id,
        "ip_address": ip,
        "user_agent": ua,
    }
