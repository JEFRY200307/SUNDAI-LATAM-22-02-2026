"""
Backend principal — Orquestador del Agente Anti-Fraude
Rol 5: UI Dashboard & Orchestration

9 endpoints orquestados via LangGraph.
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import json, os, datetime

from backend.schemas import TransactionIntent, TransactionResult, FeedbackPayload
from backend.agent_graph import fraud_graph
from backend.simulator import generate_random_transaction

# Cargar variables de entorno
load_dotenv()

app = FastAPI(
    title="Anti-Fraud Agent API",
    description="Orquestador del agente inteligente de detección de fraude — SUNDAI LATAM 2026",
    version="2.0.0",
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
    """Lee el log de aprendizaje."""
    try:
        with open(LOG_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _write_log(logs: list[dict]):
    """Escribe el log de aprendizaje completo."""
    os.makedirs(os.path.dirname(LOG_PATH) or ".", exist_ok=True)
    with open(LOG_PATH, "w") as f:
        json.dump(logs, f, indent=2)


def _run_pipeline(intent: TransactionIntent) -> TransactionResult:
    """Ejecuta el grafo LangGraph y devuelve TransactionResult."""
    initial_state = {
        "transaction": intent.model_dump(),
    }

    result_state = fraud_graph.invoke(initial_state)

    return TransactionResult(
        transaction_id=intent.transaction_id,
        risk_score=round(result_state.get("risk_score", 0.0), 4),
        decision=result_state.get("decision", "UNKNOWN"),
        risk_factors=result_state.get("risk_factors", []),
        signals={
            "device": result_state.get("device_signals", {}),
            "mule_score": result_state.get("mule_score", 0.0),
        },
        hitl_triggered=result_state.get("hitl_triggered", False),
        hitl_action=result_state.get("hitl_action"),
        explanation=result_state.get("explanation"),
        timestamp=result_state.get("timestamp", datetime.datetime.utcnow().isoformat()),
    )


# ─── 1. POST /analyze ────────────────────────────────────────────────────────

@app.post("/analyze", response_model=TransactionResult)
async def analyze_transaction(intent: TransactionIntent):
    """
    Pipeline orquestado de análisis de fraude via LangGraph.
    Ejecuta: Signals → Mule Score → Risk Engine → Decision → HITL → XAI → Memory
    """
    return _run_pipeline(intent)


# ─── 2. GET /health ───────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "anti-fraud-agent", "version": "2.0.0"}


# ─── 3. GET /transactions ────────────────────────────────────────────────────

@app.get("/transactions")
async def list_transactions():
    """Retorna todos los análisis previos del learning log."""
    logs = _read_log()
    return {"count": len(logs), "transactions": logs}


# ─── 4. GET /transactions/{id} ───────────────────────────────────────────────

@app.get("/transactions/{transaction_id}")
async def get_transaction(transaction_id: str):
    """Retorna un análisis específico por ID."""
    logs = _read_log()
    for entry in logs:
        if entry.get("transaction_id") == transaction_id:
            return entry
    return {"error": "Transaction not found", "transaction_id": transaction_id}


# ─── 5. POST /simulate/batch ─────────────────────────────────────────────────

@app.post("/simulate/batch")
async def simulate_batch(count: int = Query(default=5, ge=1, le=50)):
    """Genera y analiza N transacciones aleatorias."""
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
    """Estadísticas resumidas del learning log."""
    logs = _read_log()
    total = len(logs)
    if total == 0:
        return {"total": 0, "fraud": 0, "possible_fraud": 0, "no_fraud": 0, "avg_risk_score": 0}

    fraud = sum(1 for l in logs if l.get("decision") == "FRAUD")
    possible = sum(1 for l in logs if l.get("decision") == "POSSIBLE_FRAUD")
    no_fraud = sum(1 for l in logs if l.get("decision") == "NO_FRAUD")
    avg_score = sum(l.get("risk_score", 0) for l in logs) / total

    return {
        "total": total,
        "fraud": fraud,
        "possible_fraud": possible,
        "no_fraud": no_fraud,
        "avg_risk_score": round(avg_score, 4),
        "hitl_triggered_count": sum(1 for l in logs if l.get("hitl_triggered")),
    }


# ─── 7. GET /graph/info ──────────────────────────────────────────────────────

@app.get("/graph/info")
async def graph_info():
    """Metadata del grafo LangGraph: nodos y flujo."""
    return {
        "nodes": [
            "device_signals",
            "mule_scoring",
            "risk_engine",
            "decision_policy",
            "hitl_verify",
            "xai_explain",
            "memory_write",
        ],
        "edges": [
            {"from": "START", "to": "device_signals"},
            {"from": "START", "to": "mule_scoring"},
            {"from": "device_signals", "to": "risk_engine"},
            {"from": "mule_scoring", "to": "risk_engine"},
            {"from": "risk_engine", "to": "decision_policy"},
            {"from": "decision_policy", "to": "hitl_verify", "condition": "FRAUD | POSSIBLE_FRAUD"},
            {"from": "decision_policy", "to": "xai_explain", "condition": "NO_FRAUD"},
            {"from": "hitl_verify", "to": "xai_explain"},
            {"from": "xai_explain", "to": "memory_write"},
            {"from": "memory_write", "to": "END"},
        ],
        "description": "Pipeline LangGraph de detección de fraude con nodos paralelos y HITL condicional.",
    }


# ─── 8. GET /config ──────────────────────────────────────────────────────────

@app.get("/config")
async def get_config():
    """Configuración actual de umbrales y modelo."""
    return {
        "risk_threshold_fraud": float(os.getenv("RISK_THRESHOLD_FRAUD", "0.75")),
        "risk_threshold_possible": float(os.getenv("RISK_THRESHOLD_POSSIBLE", "0.45")),
        "groq_model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "llm_fallback_mode": os.getenv("LLM_FALLBACK_MODE", "false"),
        "learning_log_path": LOG_PATH,
    }


# ─── 9. POST /feedback ───────────────────────────────────────────────────────

@app.post("/feedback")
async def submit_feedback(payload: FeedbackPayload):
    """
    Recibe feedback humano sobre una decisión pasada.
    Registra la corrección en el learning log para aprendizaje continuo.
    """
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

    _write_log(logs)
    return {
        "status": "feedback_recorded",
        "transaction_id": payload.transaction_id,
        "correct_decision": payload.correct_decision,
    }
