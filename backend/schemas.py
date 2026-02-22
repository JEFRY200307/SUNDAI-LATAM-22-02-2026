"""
Modelos Pydantic y AgentState para el pipeline LangGraph.
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


class TransactionResult(BaseModel):
    transaction_id: str
    risk_score: float
    decision: str                    # NO_FRAUD | POSSIBLE_FRAUD | FRAUD
    risk_factors: list[str] = []
    signals: dict = {}
    hitl_triggered: bool = False
    hitl_action: Optional[str] = None
    explanation: Optional[str] = None
    timestamp: str = ""


class FeedbackPayload(BaseModel):
    transaction_id: str
    correct_decision: str            # NO_FRAUD | POSSIBLE_FRAUD | FRAUD
    comments: Optional[str] = None


# ─── LangGraph: AgentState ────────────────────────────────────────────────────

class AgentState(TypedDict, total=False):
    # Input
    transaction: dict

    # Nodo: device_signals
    device_signals: dict

    # Nodo: mule_scoring
    mule_score: float

    # Nodo: risk_engine
    risk_score: float
    risk_factors: list

    # Nodo: decision_policy
    decision: str

    # Nodo: hitl_verify
    hitl_triggered: bool
    hitl_action: str

    # Nodo: xai_explain
    explanation: str

    # Nodo: memory_write
    timestamp: str
