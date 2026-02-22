"""
Nodo C — Bloqueo & Reporte
Genera un reporte de fraude usando el LLM y bloquea la transacción.
"""
import os
import json
import datetime


REPORT_PROMPT = """Eres un analista de fraude bancario. Genera un REPORTE DE FRAUDE formal y conciso en español
para la siguiente transacción bloqueada por suplantación de identidad.

## Datos de la transacción:
- ID: {transaction_id}
- Monto: {amount} {currency}
- Cuenta origen: {sender_account}
- Cuenta destino: {receiver_account}

## Resultado del análisis:
- Nivel de riesgo: {risk_level}
- Score de riesgo: {risk_score}
- Factores de riesgo: {risk_factors}
- Razonamiento: {reasoning}

## Señales detectadas:
- Señales de dispositivo: {device_signals}
- Mule Score: {mule_score}

## Resultado de HITL (si aplica):
- Reconocimiento facial: score={facial_score}, pasó={facial_passed}
- Voice bot: verificado={voice_verified}

Genera un reporte de máximo 4 párrafos que incluya:
1. Resumen del incidente
2. Evidencia detectada
3. Acciones tomadas (bloqueo)
4. Recomendaciones

Responde solo con el reporte, sin encabezados ni formato markdown."""


def generate_report_with_llm(state: dict) -> str:
    """Genera reporte de fraude usando el LLM."""
    try:
        from langchain_groq import ChatGroq

        api_key = os.getenv("GROQ_API_KEY", "")
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        if not api_key:
            return _generate_template_report(state)

        llm = ChatGroq(api_key=api_key, model=model, temperature=0.3, max_tokens=512)

        tx = state.get("transaction", {})
        prompt = REPORT_PROMPT.format(
            transaction_id=tx.get("transaction_id", "N/A"),
            amount=tx.get("amount", 0),
            currency=tx.get("currency", "USD"),
            sender_account=tx.get("sender_account", "N/A"),
            receiver_account=tx.get("receiver_account", "N/A"),
            risk_level=state.get("risk_level", "ALTO"),
            risk_score=state.get("risk_score", 0.0),
            risk_factors=state.get("risk_factors", []),
            reasoning=state.get("reasoning", ""),
            device_signals=state.get("device_signals", {}),
            mule_score=state.get("mule_score", 0.0),
            facial_score=state.get("facial_score", "N/A"),
            facial_passed=state.get("facial_passed", "N/A"),
            voice_verified=state.get("voice_verified", "N/A"),
        )

        response = llm.invoke(prompt)
        return response.content

    except Exception as e:
        print(f"[ReportGenerator] LLM error: {e}")
        return _generate_template_report(state)


def _generate_template_report(state: dict) -> str:
    """Fallback: reporte basado en template."""
    tx = state.get("transaction", {})
    return (
        f"REPORTE DE FRAUDE — {tx.get('transaction_id', 'N/A')}\n"
        f"Nivel de riesgo: {state.get('risk_level', 'ALTO')}\n"
        f"Score: {state.get('risk_score', 0.0):.4f}\n"
        f"Factores: {', '.join(state.get('risk_factors', []))}\n"
        f"Acción: Transacción BLOQUEADA.\n"
        f"Motivo: {state.get('reasoning', 'Múltiples indicadores de suplantación de identidad.')}\n"
    )


# ─── LangGraph Node Wrapper ──────────────────────────────────────────────────

def action_node(state: dict) -> dict:
    """Nodo C LangGraph: bloquea la transacción y genera reporte."""
    fallback = os.getenv("LLM_FALLBACK_MODE", "false").lower() == "true"
    timestamp = datetime.datetime.utcnow().isoformat()

    if fallback:
        report = _generate_template_report(state)
    else:
        report = generate_report_with_llm(state)

    print(f"[ActionNode] Transacción {state.get('transaction', {}).get('transaction_id')} BLOQUEADA")

    return {
        "blocked": True,
        "report": report,
        "timestamp": timestamp,
    }


def approve_node(state: dict) -> dict:
    """Nodo terminal: aprueba la transacción."""
    timestamp = datetime.datetime.utcnow().isoformat()

    return {
        "blocked": False,
        "report": None,
        "timestamp": timestamp,
    }
