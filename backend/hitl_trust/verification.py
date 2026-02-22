"""
ROL 4 — HITL & Trust Flow
Dispara acciones de verificación adicional según el nivel de riesgo.
"""


def trigger_verification(decision: str) -> str:
    """
    Determina y simula la acción de autenticación reforzada.

    Args:
        decision: "POSSIBLE_FRAUD" o "FRAUD"

    Returns:
        str: Descripción de la acción de verificación tomada.
    """
    if decision == "FRAUD":
        return _block_and_notify()
    elif decision == "POSSIBLE_FRAUD":
        return _step_up_auth()
    return "NO_ACTION"


def _step_up_auth() -> str:
    """Simula un Step-Up Authentication (OTP / biometría)."""
    # TODO: Integrar con proveedor real de OTP o biometría
    print("[HITL] Step-up auth activado — Enviando OTP al usuario.")
    return "STEP_UP_AUTH_OTP"


def _block_and_notify() -> str:
    """Bloquea la transacción y activa el voice bot."""
    print("[HITL] Transacción BLOQUEADA — Activando voice bot.")
    _trigger_voice_bot()
    return "TRANSACTION_BLOCKED_VOICE_BOT"


def _trigger_voice_bot():
    """Importa y ejecuta el voice bot de forma inline."""
    from backend.hitl_trust.voice_bot import run_voice_bot
    run_voice_bot()
