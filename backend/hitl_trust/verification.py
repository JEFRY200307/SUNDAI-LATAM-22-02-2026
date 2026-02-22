"""
ROL 4 — HITL & Trust Flow — Verificación Voice Bot
Simula el voice bot de verificación: preguntas sí/no al usuario.
En producción se integraría con Twilio, AWS Connect, etc.
"""
import hashlib
import random

from backend.hitl_trust.voice_bot import VOICE_BOT_SCRIPT


def simulate_voice_verification(user_id: str, transaction_id: str = "") -> dict:
    """
    Simula la verificación por voice bot.

    El voice bot hace preguntas de seguridad y el usuario confirma o rechaza.
    Usa seed determinístico para resultados reproducibles.

    Args:
        user_id: Identificador del usuario.
        transaction_id: ID de la transacción.

    Returns:
        dict con verified, confidence, y metadata.
    """
    # Seed determinístico
    seed_str = f"voice:{user_id}:{transaction_id}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % 10000
    rng = random.Random(seed)

    # Simular respuesta del usuario (tendencia a confirmar: 65%)
    verified = rng.random() < 0.65
    confidence = round(rng.uniform(0.6, 0.95) if verified else rng.uniform(0.3, 0.6), 4)

    print(f"[VoiceBot] User={user_id} Verified={verified} Confidence={confidence}")
    print(VOICE_BOT_SCRIPT)

    return {
        "verified": verified,
        "confidence": confidence,
        "method": "simulated_voice_bot",
        "questions_asked": 3,
    }


# ─── LangGraph Node Wrapper ──────────────────────────────────────────────────

def voice_bot_node(state: dict) -> dict:
    """Nodo LangGraph: ejecuta verificación por voice bot."""
    tx = state.get("transaction", {})
    user_id = tx.get("sender_account", "unknown")
    transaction_id = tx.get("transaction_id", "")

    result = simulate_voice_verification(user_id, transaction_id)

    return {
        "voice_verified": result["verified"],
    }
