"""
ROL 4 — Reconocimiento Facial (Simulado)
Simula un sistema de reconocimiento facial que retorna un similarity_score.
En producción, aquí se integraría con AWS Rekognition, Azure Face, etc.
"""
import hashlib
import random


# Umbral de similitud para aprobar
SIMILARITY_THRESHOLD = 0.70


def simulate_facial_recognition(user_id: str, transaction_id: str = "") -> dict:
    """
    Simula reconocimiento facial con un score de similitud.

    Usa un seed determinístico basado en user_id + transaction_id para
    generar resultados reproducibles en demo.

    Args:
        user_id: Identificador del usuario.
        transaction_id: ID de la transacción (para seed).

    Returns:
        dict con similarity_score, passed, y metadata.
    """
    # Seed determinístico para demo reproducible
    seed_str = f"{user_id}:{transaction_id}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % 10000
    rng = random.Random(seed)

    # Simular similarity score (tendencia a pasar: media 0.75)
    similarity_score = round(rng.gauss(0.75, 0.15), 4)
    similarity_score = max(0.0, min(1.0, similarity_score))

    passed = similarity_score >= SIMILARITY_THRESHOLD

    print(f"[FacialRecognition] User={user_id} Score={similarity_score:.4f} Passed={passed}")

    return {
        "similarity_score": similarity_score,
        "passed": passed,
        "threshold": SIMILARITY_THRESHOLD,
        "method": "simulated_facial_recognition",
    }


# ─── LangGraph Node Wrapper ──────────────────────────────────────────────────

def facial_recognition_node(state: dict) -> dict:
    """Nodo LangGraph: ejecuta reconocimiento facial simulado."""
    tx = state.get("transaction", {})
    user_id = tx.get("sender_account", "unknown")
    transaction_id = tx.get("transaction_id", "")

    result = simulate_facial_recognition(user_id, transaction_id)

    return {
        "facial_score": result["similarity_score"],
        "facial_passed": result["passed"],
    }
