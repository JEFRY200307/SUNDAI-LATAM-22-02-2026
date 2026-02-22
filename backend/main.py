"""
Backend principal — Orquestador del Agente Anti-Fraude
Rol 5: UI Dashboard & Orchestration
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json, os, datetime

from backend.behavioral_device.telemetry import get_device_signals
from backend.graph_intelligence.mule_scorer import score_mule_risk
from backend.risk_decision.classifier import classify_risk
from backend.hitl_trust.verification import trigger_verification

app = FastAPI(
    title="Anti-Fraud Agent API",
    description="Orquestador del agente inteligente de detección de fraude — SUNDAI LATAM 2026",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOG_PATH = os.getenv("LEARNING_LOG_PATH", "data/learning_log.json")


# ─── Modelos de datos ─────────────────────────────────────────────────────────

class TransactionIntent(BaseModel):
    transaction_id: str
    sender_account: str
    receiver_account: str
    amount: float
    currency: str = "USD"
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    # ── Señales de dispositivo (Rol 3) ────────────────────────────────────
    is_emulator: bool = False
    is_rooted: bool = False
    anomalous_ip_flag: bool = False
    # ── Señales de comportamiento (Rol 3) ─────────────────────────────────
    interaction_time_ms: Optional[int] = None
    navigation_steps: Optional[int] = None
    historical_amounts: Optional[list[float]] = None


class TransactionResult(BaseModel):
    transaction_id: str
    risk_score: float
    decision: str           # NO_FRAUD | POSSIBLE_FRAUD | FRAUD
    signals: dict
    hitl_triggered: bool
    hitl_action: Optional[str] = None
    timestamp: str


# ─── Endpoint principal ───────────────────────────────────────────────────────

@app.post("/analyze", response_model=TransactionResult)
async def analyze_transaction(intent: TransactionIntent):
    """
    Pipeline orquestado de análisis de fraude.
    Orden: Signals → Mule Score → Risk Engine → Decision Policy → HITL → Log
    """
    # 1. Señales de dispositivo y comportamiento (Rol 3)
    device_signals = get_device_signals(
        device_id=intent.device_id,
        ip_address=intent.ip_address,
        user_agent=intent.user_agent,
        is_emulator=intent.is_emulator,
        is_rooted=intent.is_rooted,
        anomalous_ip=intent.anomalous_ip_flag,
        interaction_time_ms=intent.interaction_time_ms,
        navigation_steps=intent.navigation_steps,
        amount=intent.amount,
        historical_amounts=intent.historical_amounts,
    )

    # 2. Score de mula del destinatario (Rol 2)
    mule_score = score_mule_risk(receiver_account=intent.receiver_account)

    # 3. Motor de riesgo y decisión (Rol 1)
    risk_score, decision = classify_risk(
        amount=intent.amount,
        device_signals=device_signals,
        mule_score=mule_score,
    )

    # 4. HITL / Biometría si hay fricción (Rol 4)
    hitl_triggered = False
    hitl_action = None
    if decision != "NO_FRAUD":
        hitl_triggered = True
        hitl_action = trigger_verification(decision=decision)

    # 5. Registro del evento (MemoryWriter)
    result = TransactionResult(
        transaction_id=intent.transaction_id,
        risk_score=round(risk_score, 4),
        decision=decision,
        signals={
            "device": device_signals,
            "mule_score": mule_score,
        },
        hitl_triggered=hitl_triggered,
        hitl_action=hitl_action,
        timestamp=datetime.datetime.utcnow().isoformat(),
    )
    _write_log(result.model_dump())

    return result


# ─── Health check ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "anti-fraud-agent"}


# ─── MemoryWriter ─────────────────────────────────────────────────────────────

def _write_log(event: dict):
    """Persiste el evento en el log de aprendizaje continuo."""
    try:
        with open(LOG_PATH, "r+") as f:
            logs = json.load(f)
            logs.append(event)
            f.seek(0)
            json.dump(logs, f, indent=2)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(LOG_PATH, "w") as f:
            json.dump([event], f, indent=2)
