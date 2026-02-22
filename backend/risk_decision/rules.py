"""
ROL 1 — Risk & Decision Engine
Reglas de clasificación, pesos de señales y umbrales de decisión.
Modifica este archivo para ajustar la sensibilidad del agente.
"""
import os

# ─── Pesos de señales (suman como máximo ~1.0) ────────────────────────────────
RISK_WEIGHTS: dict[str, float] = {
    "high_amount":        0.30,   # Monto > $10,000
    "medium_amount":      0.10,   # Monto $3,000–$10,000
    "mule_score":         0.35,   # Peso del Mule Risk Score (0–1) × este peso
    "emulator":           0.20,   # Dispositivo emulado detectado
    "anomalous_ip":       0.15,   # IP en lista negra o de VPN
    "suspicious_typing":  0.10,   # Velocidad de tipeo robótica
}

# ─── Umbrales de decisión ─────────────────────────────────────────────────────
THRESHOLDS: dict[str, float] = {
    "fraud":          float(os.getenv("RISK_THRESHOLD_FRAUD",    "0.75")),
    "possible_fraud": float(os.getenv("RISK_THRESHOLD_POSSIBLE", "0.45")),
}

# ─── Descripciones humanas de cada factor de riesgo (para XAI) ────────────────
RISK_FACTOR_DESCRIPTIONS: dict[str, str] = {
    "high_amount":        "Monto de la transacción superior a $10,000",
    "medium_amount":      "Monto de la transacción entre $3,000 y $10,000",
    "mule_score":         "Cuenta destino asociada a red de mulas",
    "emulator":           "Dispositivo emulado (no físico) detectado",
    "anomalous_ip":       "Dirección IP en lista negra o de VPN/Tor",
    "suspicious_typing":  "Velocidad de tipeo robótica o sospechosa",
    "blacklisted_account": "Cuenta destino en lista negra directa",
}
