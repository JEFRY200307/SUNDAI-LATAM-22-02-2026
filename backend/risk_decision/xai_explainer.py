"""
ROL 1 — XAI Explainer
Genera explicaciones humanas del resultado de fraude usando Groq (LLM)
con fallback a templates estáticos.
"""
import os
from backend.risk_decision.rules import RISK_FACTOR_DESCRIPTIONS


def _build_template_explanation(state: dict) -> str:
    """Fallback: explicación basada en templates cuando el LLM no está disponible."""
    decision = state.get("decision", "UNKNOWN")
    risk_score = state.get("risk_score", 0.0)
    risk_factors = state.get("risk_factors", [])

    factor_lines = []
    for f in risk_factors:
        desc = RISK_FACTOR_DESCRIPTIONS.get(f, f)
        factor_lines.append(f"  • {desc}")

    factors_text = "\n".join(factor_lines) if factor_lines else "  • Ningún factor de riesgo significativo."

    return (
        f"Decisión: {decision} (score {risk_score:.2f})\n"
        f"Factores de riesgo detectados:\n{factors_text}\n"
        f"Esta evaluación fue generada automáticamente por el motor de riesgo."
    )


def _build_llm_explanation(state: dict) -> str:
    """Usa Groq via langchain-groq para generar la explicación XAI."""
    try:
        from langchain_groq import ChatGroq

        api_key = os.getenv("GROQ_API_KEY", "")
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        if not api_key:
            return _build_template_explanation(state)

        llm = ChatGroq(
            api_key=api_key,
            model=model,
            temperature=0.3,
            max_tokens=512,
        )

        decision = state.get("decision", "UNKNOWN")
        risk_score = state.get("risk_score", 0.0)
        risk_factors = state.get("risk_factors", [])
        device_signals = state.get("device_signals", {})
        mule_score = state.get("mule_score", 0.0)
        tx = state.get("transaction", {})

        prompt = f"""Eres un analista de fraude bancario. Genera una explicación clara y concisa en español
para el siguiente resultado de análisis de una transacción.

Transacción:
- ID: {tx.get('transaction_id', 'N/A')}
- Monto: {tx.get('amount', 0)} {tx.get('currency', 'USD')}
- Cuenta origen: {tx.get('sender_account', 'N/A')}
- Cuenta destino: {tx.get('receiver_account', 'N/A')}

Resultado del análisis:
- Decisión: {decision}
- Score de riesgo: {risk_score:.4f}
- Factores de riesgo: {', '.join(risk_factors) if risk_factors else 'Ninguno'}
- Score de mula: {mule_score:.2f}
- Señales de dispositivo: {device_signals}

Genera una explicación de máximo 3 párrafos que:
1. Resuma la decisión tomada
2. Explique los factores de riesgo principales
3. Sugiera la acción recomendada

Responde solo con la explicación, sin encabezados ni formato markdown."""

        response = llm.invoke(prompt)
        return response.content

    except Exception as e:
        print(f"[XAI] LLM fallback activado — error: {e}")
        return _build_template_explanation(state)


def xai_explain_node(state: dict) -> dict:
    """Nodo LangGraph: genera la explicación XAI."""
    fallback = os.getenv("LLM_FALLBACK_MODE", "false").lower() == "true"

    if fallback:
        explanation = _build_template_explanation(state)
    else:
        explanation = _build_llm_explanation(state)

    return {"explanation": explanation}
