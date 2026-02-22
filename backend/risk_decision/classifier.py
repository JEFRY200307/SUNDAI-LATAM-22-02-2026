"""
ROL 1 — Risk Classifier (Nodo B: Razonamiento)
Usa el LLM (Groq) para clasificar el riesgo de suplantación de identidad.
El LLM responde en JSON con: risk_level, confidence, risk_factors, reasoning.
Incluye fallback a reglas Python si el LLM falla.
"""
import os
import json

from backend.risk_decision.rules import RISK_WEIGHTS, THRESHOLDS, RISK_FACTOR_DESCRIPTIONS


# ─── Prompt para el LLM ──────────────────────────────────────────────────────

CLASSIFICATION_PROMPT = """Eres un analista experto en detección de fraude bancario y suplantación de identidad.
Analiza los siguientes datos de una transacción y clasifica el riesgo de SUPLANTACIÓN DE IDENTIDAD.

## Datos de la transacción:
- ID: {transaction_id}
- Monto: {amount} {currency}
- Cuenta origen: {sender_account}
- Cuenta destino: {receiver_account}

## Indicadores de riesgo del dispositivo (Device Risk Score: {device_risk_score}):
- Emulador detectado: {is_emulator}
- Dispositivo con root/jailbreak: {is_rooted}
- IP anómala (VPN/Tor/proxy): {anomalous_ip}
- Fingerprint del dispositivo: {device_fingerprint}
- Razones de riesgo del dispositivo: {device_reasons}

## Indicadores de riesgo de comportamiento (Behavioral Risk Score: {behavioral_risk_score}):
- Velocidad de interacción sospechosa: {suspicious_typing_speed}
- Navegación sospechosa: {suspicious_navigation}
- Patrón de monto anómalo: {suspicious_amount_pattern}
- Razones de comportamiento: {behavioral_reasons}

## Mule Score (cuenta destino): {mule_score}
(0.0 = cuenta limpia, 1.0 = cuenta mula confirmada)

## Instrucciones:
Clasifica el nivel de riesgo como BAJO, MEDIO o ALTO.
- BAJO: Transacción legítima, sin indicadores significativos de suplantación.
- MEDIO: Hay indicadores sospechosos que requieren verificación adicional del usuario.
- ALTO: Múltiples indicadores confirman alta probabilidad de suplantación de identidad.

Responde ÚNICAMENTE con un JSON válido, sin texto adicional ni markdown:
{{"risk_level": "BAJO|MEDIO|ALTO", "confidence": 0.0-1.0, "risk_score": 0.0-1.0, "risk_factors": ["factor1", "factor2"], "reasoning": "explicación breve en español"}}"""


def classify_with_llm(enrichment: dict) -> dict:
    """
    Usa Groq via langchain-groq para clasificar el riesgo.

    Args:
        enrichment: Dict con todos los datos enriquecidos del Nodo A.

    Returns:
        dict con risk_level, confidence, risk_score, risk_factors, reasoning.
    """
    try:
        from langchain_groq import ChatGroq

        api_key = os.getenv("GROQ_API_KEY", "")
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        if not api_key:
            return classify_with_rules(enrichment)

        llm = ChatGroq(
            api_key=api_key,
            model=model,
            temperature=0.1,
            max_tokens=512,
        )

        tx = enrichment.get("transaction", {})
        signals = enrichment.get("device_signals", {})

        prompt = CLASSIFICATION_PROMPT.format(
            transaction_id=tx.get("transaction_id", "N/A"),
            amount=tx.get("amount", 0),
            currency=tx.get("currency", "USD"),
            sender_account=tx.get("sender_account", "N/A"),
            receiver_account=tx.get("receiver_account", "N/A"),
            device_risk_score=signals.get("device_risk_score", 0.0),
            is_emulator=signals.get("is_emulator", False),
            is_rooted=signals.get("is_rooted", False),
            anomalous_ip=signals.get("anomalous_ip", False),
            device_fingerprint=signals.get("device_fingerprint", "N/A"),
            device_reasons=signals.get("reasons", []),
            behavioral_risk_score=signals.get("behavioral_risk_score", 0.0),
            suspicious_typing_speed=signals.get("suspicious_typing_speed", False),
            suspicious_navigation=signals.get("suspicious_navigation", False),
            suspicious_amount_pattern=signals.get("suspicious_amount_pattern", False),
            behavioral_reasons=signals.get("reasons", []),
            mule_score=enrichment.get("mule_score", 0.0),
        )

        response = llm.invoke(prompt)
        content = response.content.strip()

        # Limpiar posible markdown wrapping
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content
            content = content.rsplit("```", 1)[0].strip()

        result = json.loads(content)

        # Validar campos requeridos
        if "risk_level" not in result:
            return classify_with_rules(enrichment)

        # Normalizar risk_level
        result["risk_level"] = result["risk_level"].upper()
        if result["risk_level"] not in ("BAJO", "MEDIO", "ALTO"):
            return classify_with_rules(enrichment)

        return {
            "risk_level": result["risk_level"],
            "confidence": float(result.get("confidence", 0.8)),
            "risk_score": float(result.get("risk_score", 0.5)),
            "risk_factors": result.get("risk_factors", []),
            "reasoning": result.get("reasoning", ""),
        }

    except Exception as e:
        print(f"[Classifier] LLM error, using rules fallback: {e}")
        return classify_with_rules(enrichment)


def classify_with_rules(enrichment: dict) -> dict:
    """
    Fallback: clasificación basada en reglas Python cuando el LLM no está disponible.
    """
    tx = enrichment.get("transaction", {})
    signals = enrichment.get("device_signals", {})
    mule_score = enrichment.get("mule_score", 0.0)
    amount = tx.get("amount", 0.0)

    score = 0.0
    risk_factors = []

    # Señales de dispositivo
    if signals.get("is_emulator"):
        score += RISK_WEIGHTS["emulator"]
        risk_factors.append("emulator")
    if signals.get("anomalous_ip"):
        score += RISK_WEIGHTS["anomalous_ip"]
        risk_factors.append("anomalous_ip")
    if signals.get("suspicious_typing_speed"):
        score += RISK_WEIGHTS["suspicious_typing"]
        risk_factors.append("suspicious_typing")

    # Monto
    if amount > 10_000:
        score += RISK_WEIGHTS["high_amount"]
        risk_factors.append("high_amount")
    elif amount > 3_000:
        score += RISK_WEIGHTS["medium_amount"]
        risk_factors.append("medium_amount")

    # Mule score
    score += mule_score * RISK_WEIGHTS["mule_score"]
    if mule_score > 0.5:
        risk_factors.append("mule_score")

    risk_score = min(score, 1.0)

    if risk_score >= THRESHOLDS["fraud"]:
        risk_level = "ALTO"
    elif risk_score >= THRESHOLDS["possible_fraud"]:
        risk_level = "MEDIO"
    else:
        risk_level = "BAJO"

    factor_descs = [RISK_FACTOR_DESCRIPTIONS.get(f, f) for f in risk_factors]
    reasoning = f"Clasificación por reglas: score {risk_score:.2f}. Factores: {', '.join(factor_descs) if factor_descs else 'ninguno'}."

    return {
        "risk_level": risk_level,
        "confidence": 0.7,
        "risk_score": risk_score,
        "risk_factors": risk_factors,
        "reasoning": reasoning,
    }


# ─── LangGraph Node Wrapper ──────────────────────────────────────────────────

def reasoning_node(state: dict) -> dict:
    """Nodo B LangGraph: el LLM clasifica el riesgo de suplantación de identidad."""
    fallback = os.getenv("LLM_FALLBACK_MODE", "false").lower() == "true"

    enrichment = {
        "transaction": state.get("transaction", {}),
        "device_signals": state.get("device_signals", {}),
        "mule_score": state.get("mule_score", 0.0),
    }

    if fallback:
        result = classify_with_rules(enrichment)
    else:
        result = classify_with_llm(enrichment)

    return {
        "risk_level": result["risk_level"],
        "risk_score": result["risk_score"],
        "confidence": result["confidence"],
        "risk_factors": result["risk_factors"],
        "reasoning": result["reasoning"],
        "llm_analysis": result,
        "hitl_required": result["risk_level"] == "MEDIO",
    }
