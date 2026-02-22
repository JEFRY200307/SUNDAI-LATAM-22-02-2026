"""
Modelos Pydantic y AgentState para el pipeline LangGraph de 3 nodos.
"""
from typing import Optional
from typing_extensions import TypedDict
from pydantic import BaseModel


# ─── Pydantic: request / response ────────────────────────────────────────────

class TransactionIntent(BaseModel):
    transaction_id: str
    sender_account: str
    receiver_account: str
    amount: float
    currency: str = "USD"
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    interaction_time_ms: Optional[int] = None
    navigation_steps: Optional[int] = None
    historical_amounts: Optional[list[float]] = None


class TransactionResult(BaseModel):
    transaction_id: str
    risk_level: str                    # BAJO | MEDIO | ALTO
    risk_score: float = 0.0
    confidence: float = 0.0
    risk_factors: list[str] = []
    reasoning: str = ""
    signals: dict = {}
    hitl_required: bool = False
    facial_result: Optional[dict] = None
    voice_result: Optional[dict] = None
    blocked: bool = False
    report: Optional[str] = None
    timestamp: str = ""


class FeedbackPayload(BaseModel):
    transaction_id: str
    correct_decision: str            # BAJO | MEDIO | ALTO
    comments: Optional[str] = None


class HITLFacialRequest(BaseModel):
    transaction_id: str
    user_id: str


class HITLVoiceRequest(BaseModel):
    transaction_id: str
    user_id: str
    confirmed: bool


# ─── LangGraph: AgentState ────────────────────────────────────────────────────

class AgentState(TypedDict, total=False):
    # Input
    transaction: dict

    # Nodo A — Enriquecimiento
    device_signals: dict
    mule_score: float
    enrichment_summary: dict       # resumen consolidado para el LLM

    # Nodo B — Razonamiento LLM
    risk_level: str                # BAJO | MEDIO | ALTO
    risk_score: float
    confidence: float
    risk_factors: list
    reasoning: str
    llm_analysis: dict             # respuesta completa del LLM en JSON

    # HITL — Reconocimiento facial + Voice bot
    hitl_required: bool
    facial_score: float
    facial_passed: bool
    voice_verified: bool

    # Nodo C — Acción
    blocked: bool
    report: str

    # Meta
    timestamp: str
