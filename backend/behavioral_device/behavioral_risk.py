"""
ROL 3 — BehavioralRisk Module
Simula biometría pasiva: velocidad de interacción, ritmo de navegación,
patrón de montos históricos.  Genera BehavioralRiskScore + reasons.
"""
from statistics import mean

# ─── Pesos explícitos por señal ───────────────────────────────────────────────
BEHAVIORAL_WEIGHTS: dict[str, float] = {
    "fast_interaction":         0.35,
    "suspicious_navigation":    0.20,
    "suspicious_amount_pattern": 0.45,
}

# ─── Umbrales de velocidad de interacción (ms) ───────────────────────────────
INTERACTION_THRESHOLDS = {
    "high":   1200,   # < 1200ms  → riesgo alto  (peso completo)
    "medium": 2500,   # 1200–2500ms → riesgo medio (peso × 0.5)
    # > 2500ms → normal (sin penalización)
}


def evaluate_behavioral_risk(
    amount: float = 0.0,
    interaction_time_ms: int | None = None,
    navigation_steps: int | None = None,
    historical_amounts: list[float] | None = None,
) -> dict:
    """
    Evalúa riesgo de comportamiento del usuario.

    Args:
        amount:              Monto de la transacción actual.
        interaction_time_ms: Tiempo (ms) desde abrir pantalla hasta confirmar.
        navigation_steps:    Número de pasos/clicks antes de la transacción.
        historical_amounts:  Lista de montos anteriores del usuario.

    Returns:
        dict con behavioral_risk_score (0–1), reasons, y señales individuales.
    """
    score = 0.0
    reasons: list[str] = []

    # ── 1. Velocidad de interacción (bandas) ──────────────────────────────────
    suspicious_interaction = False
    if interaction_time_ms is not None:
        if interaction_time_ms < INTERACTION_THRESHOLDS["high"]:
            score += BEHAVIORAL_WEIGHTS["fast_interaction"]
            suspicious_interaction = True
            reasons.append(f"interaction_too_fast_{interaction_time_ms}ms")
        elif interaction_time_ms < INTERACTION_THRESHOLDS["medium"]:
            score += BEHAVIORAL_WEIGHTS["fast_interaction"] * 0.5
            suspicious_interaction = True
            reasons.append(f"interaction_moderately_fast_{interaction_time_ms}ms")

    # ── 2. Ritmo de navegación ────────────────────────────────────────────────
    suspicious_navigation = False
    if navigation_steps is not None:
        if navigation_steps == 0:
            score += BEHAVIORAL_WEIGHTS["suspicious_navigation"]
            suspicious_navigation = True
            reasons.append("zero_navigation_steps_api_automation")
        elif navigation_steps == 1:
            score += BEHAVIORAL_WEIGHTS["suspicious_navigation"] * 0.5
            suspicious_navigation = True
            reasons.append("minimal_navigation_steps")

    # ── 3. Patrón de montos históricos ────────────────────────────────────────
    suspicious_amount = _evaluate_amount_pattern(amount, historical_amounts)
    if suspicious_amount:
        score += BEHAVIORAL_WEIGHTS["suspicious_amount_pattern"]
        reasons.append("amount_deviates_from_history")

    return {
        "suspicious_interaction_speed": suspicious_interaction,
        "suspicious_navigation": suspicious_navigation,
        "suspicious_amount_pattern": suspicious_amount,
        "behavioral_risk_score": min(score, 1.0),
        "behavioral_reasons": reasons,
    }


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _evaluate_amount_pattern(
    amount: float,
    historical_amounts: list[float] | None,
) -> bool:
    """
    Detecta si el monto actual desvía significativamente del historial.

    Reglas:
      - Sin historial → no penalizar
      - amount > max_hist × 2 → sospechoso
      - amount > avg × 3 (si avg > 0) → sospechoso
    """
    if not historical_amounts:
        return False

    avg = mean(historical_amounts)
    max_hist = max(historical_amounts)

    if max_hist > 0 and amount > max_hist * 2:
        return True
    if avg > 0 and amount > avg * 3:
        return True

    return False
