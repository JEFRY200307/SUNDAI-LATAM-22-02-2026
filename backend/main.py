"""
Backend principal — Orquestador del Agente Anti-Fraude (3 Nodos)
Rol 5: UI Dashboard & Orchestration

10 endpoints orquestados via LangGraph.
Nodo A (Enriquecimiento) → Nodo B (Razonamiento LLM) → Nodo C (Acción)
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import json, os, datetime

from backend.schemas import (
    TransactionIntent, TransactionResult,
    FeedbackPayload, HITLFacialRequest, HITLVoiceRequest,
)
from backend.agent_graph import fraud_graph
from backend.simulator import generate_random_transaction
from backend.hitl_trust.facial_recognition import simulate_facial_recognition
from backend.hitl_trust.verification import simulate_voice_verification

# Cargar variables de entorno
load_dotenv()

app = FastAPI(
    title="Anti-Fraud Agent API",
    description="Agente inteligente de detección de fraude con 3 nodos LangGraph — SUNDAI LATAM 2026",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOG_PATH = os.getenv("LEARNING_LOG_PATH", "data/learning_log.json")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _read_log() -> list[dict]:
    try:
        with open(LOG_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _run_pipeline(intent: TransactionIntent) -> TransactionResult:
    """Ejecuta el grafo LangGraph completo y devuelve TransactionResult."""
    initial_state = {
        "transaction": intent.model_dump(),
    }

    result_state = fraud_graph.invoke(initial_state)

    return TransactionResult(
        transaction_id=intent.transaction_id,
        risk_level=result_state.get("risk_level", "BAJO"),
        risk_score=round(result_state.get("risk_score", 0.0), 4),
        confidence=round(result_state.get("confidence", 0.0), 4),
        risk_factors=result_state.get("risk_factors", []),
        reasoning=result_state.get("reasoning", ""),
        signals={
            "device": result_state.get("device_signals", {}),
            "mule_score": result_state.get("mule_score", 0.0),
        },
        hitl_required=result_state.get("hitl_required", False),
        facial_result={
            "score": result_state.get("facial_score"),
            "passed": result_state.get("facial_passed"),
        } if result_state.get("facial_score") is not None else None,
        voice_result={
            "verified": result_state.get("voice_verified"),
        } if result_state.get("voice_verified") is not None else None,
        blocked=result_state.get("blocked", False),
        report=result_state.get("report"),
        timestamp=result_state.get("timestamp", datetime.datetime.utcnow().isoformat()),
    )


# ─── 1. POST /analyze ────────────────────────────────────────────────────────

@app.post("/analyze", response_model=TransactionResult)
async def analyze_transaction(intent: TransactionIntent):
    """
    Pipeline completo de análisis de fraude via LangGraph (3 nodos).
    Nodo A (Enriquecimiento) → Nodo B (LLM Razonamiento) → Routing → Nodo C (Acción)
    """
    return _run_pipeline(intent)


# ─── 2. GET /health ───────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "anti-fraud-agent", "version": "3.0.0"}


# ─── 3. GET /transactions ────────────────────────────────────────────────────

@app.get("/transactions")
async def list_transactions():
    logs = _read_log()
    return {"count": len(logs), "transactions": logs}


# ─── 4. GET /transactions/{id} ───────────────────────────────────────────────

@app.get("/transactions/{transaction_id}")
async def get_transaction(transaction_id: str):
    logs = _read_log()
    for entry in logs:
        if entry.get("transaction_id") == transaction_id:
            return entry
    return {"error": "Transaction not found", "transaction_id": transaction_id}


# ─── 5. POST /simulate/batch ─────────────────────────────────────────────────

@app.post("/simulate/batch")
async def simulate_batch(count: int = Query(default=5, ge=1, le=50)):
    results = []
    for _ in range(count):
        tx_data = generate_random_transaction()
        intent = TransactionIntent(**tx_data)
        result = _run_pipeline(intent)
        results.append(result.model_dump())
    return {"count": len(results), "results": results}


# ─── 6. GET /stats ────────────────────────────────────────────────────────────

@app.get("/stats")
async def get_stats():
    logs = _read_log()
    total = len(logs)
    if total == 0:
        return {"total": 0, "alto": 0, "medio": 0, "bajo": 0, "avg_risk_score": 0, "blocked": 0}

    alto = sum(1 for l in logs if l.get("risk_level") == "ALTO")
    medio = sum(1 for l in logs if l.get("risk_level") == "MEDIO")
    bajo = sum(1 for l in logs if l.get("risk_level") == "BAJO")
    blocked = sum(1 for l in logs if l.get("blocked"))
    avg_score = sum(l.get("risk_score", 0) for l in logs) / total

    return {
        "total": total,
        "alto": alto,
        "medio": medio,
        "bajo": bajo,
        "blocked": blocked,
        "avg_risk_score": round(avg_score, 4),
        "hitl_triggered_count": sum(1 for l in logs if l.get("hitl_required")),
    }


# ─── 7. GET /graph/info ──────────────────────────────────────────────────────

@app.get("/graph/info")
async def graph_info():
    return {
        "nodes": [
            {"id": "enrichment", "label": "Nodo A: Enriquecimiento", "role": "Recolecta señales de dispositivo, comportamiento y mule score"},
            {"id": "reasoning", "label": "Nodo B: Razonamiento LLM", "role": "El LLM clasifica riesgo de suplantación como BAJO/MEDIO/ALTO"},
            {"id": "facial_recognition", "label": "HITL: Reconocimiento Facial", "role": "Verifica identidad con similarity score"},
            {"id": "voice_bot", "label": "HITL: Voice Bot", "role": "Preguntas sí/no de verificación"},
            {"id": "action", "label": "Nodo C: Bloqueo & Reporte", "role": "Bloquea transacción y genera reporte"},
            {"id": "approve", "label": "Aprobación", "role": "Aprueba la transacción"},
        ],
        "edges": [
            {"from": "START", "to": "enrichment"},
            {"from": "enrichment", "to": "reasoning"},
            {"from": "reasoning", "to": "approve", "condition": "BAJO"},
            {"from": "reasoning", "to": "action", "condition": "ALTO"},
            {"from": "reasoning", "to": "facial_recognition", "condition": "MEDIO"},
            {"from": "facial_recognition", "to": "voice_bot", "condition": "pasa"},
            {"from": "facial_recognition", "to": "action", "condition": "no pasa"},
            {"from": "voice_bot", "to": "approve", "condition": "confirma"},
            {"from": "voice_bot", "to": "action", "condition": "no confirma"},
            {"from": "action", "to": "END"},
            {"from": "approve", "to": "END"},
        ],
        "description": "Pipeline LangGraph de 3 nodos con HITL condicional (reconocimiento facial + voice bot).",
    }


# ─── 8. GET /config ──────────────────────────────────────────────────────────

@app.get("/config")
async def get_config():
    return {
        "risk_threshold_fraud": float(os.getenv("RISK_THRESHOLD_FRAUD", "0.75")),
        "risk_threshold_possible": float(os.getenv("RISK_THRESHOLD_POSSIBLE", "0.45")),
        "groq_model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "llm_fallback_mode": os.getenv("LLM_FALLBACK_MODE", "false"),
        "learning_log_path": LOG_PATH,
    }


# ─── 9. POST /hitl/facial ────────────────────────────────────────────────────

@app.post("/hitl/facial")
async def hitl_facial(request: HITLFacialRequest):
    """Simula reconocimiento facial para una transacción."""
    result = simulate_facial_recognition(request.user_id, request.transaction_id)
    return {
        "transaction_id": request.transaction_id,
        "user_id": request.user_id,
        **result,
    }


# ─── 10. POST /hitl/voice ────────────────────────────────────────────────────

@app.post("/hitl/voice")
async def hitl_voice(request: HITLVoiceRequest):
    """Simula verificación por voice bot."""
    result = simulate_voice_verification(request.user_id, request.transaction_id)
    return {
        "transaction_id": request.transaction_id,
        "user_id": request.user_id,
        "user_confirmed": request.confirmed,
        **result,
    }


# ─── 11. GET /report/{id} ────────────────────────────────────────────────────

@app.get("/report/{transaction_id}")
async def get_report(transaction_id: str):
    """Obtiene el reporte de fraude de una transacción bloqueada."""
    logs = _read_log()
    for entry in logs:
        if entry.get("transaction_id") == transaction_id:
            if entry.get("report"):
                return {
                    "transaction_id": transaction_id,
                    "blocked": entry.get("blocked", False),
                    "risk_level": entry.get("risk_level"),
                    "report": entry.get("report"),
                }
            return {"error": "No report available", "transaction_id": transaction_id}
    return {"error": "Transaction not found", "transaction_id": transaction_id}


# ─── 12. POST /feedback ──────────────────────────────────────────────────────

@app.post("/feedback")
async def submit_feedback(payload: FeedbackPayload):
    logs = _read_log()
    found = False
    for entry in logs:
        if entry.get("transaction_id") == payload.transaction_id:
            entry["human_feedback"] = {
                "correct_decision": payload.correct_decision,
                "comments": payload.comments,
                "feedback_timestamp": datetime.datetime.utcnow().isoformat(),
            }
            found = True
            break

    if not found:
        return {"error": "Transaction not found", "transaction_id": payload.transaction_id}

    os.makedirs(os.path.dirname(LOG_PATH) or ".", exist_ok=True)
    with open(LOG_PATH, "w") as f:
        json.dump(logs, f, indent=2)

    return {
        "status": "feedback_recorded",
        "transaction_id": payload.transaction_id,
        "correct_decision": payload.correct_decision,
    }
