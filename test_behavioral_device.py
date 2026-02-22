"""
Tests para Rol 3 — Behavioral & Device Intelligence
Verifica DeviceRisk, BehavioralRisk y la integración en telemetry.
"""
from backend.behavioral_device.device_risk import evaluate_device_risk
from backend.behavioral_device.behavioral_risk import evaluate_behavioral_risk
from backend.behavioral_device.telemetry import get_device_signals


# ═══════════════════════════════════════════════════════════════════════
# DeviceRisk tests
# ═══════════════════════════════════════════════════════════════════════

def test_device_clean():
    """Todo normal → score 0, sin reasons."""
    result = evaluate_device_risk(device_id="DEV-001")
    assert result["device_risk_score"] == 0.0
    assert result["device_reasons"] == []
    assert result["is_emulator"] is False
    assert result["is_rooted"] is False
    assert result["anomalous_ip"] is False
    assert len(result["device_fingerprint"]) == 16


def test_device_rooted_and_anomalous_ip():
    """Root + IP anómala → score 0.55, 2 reasons."""
    result = evaluate_device_risk(
        device_id="DEV-002",
        is_rooted=True,
        anomalous_ip=True,
    )
    assert result["device_risk_score"] == 0.55
    assert "rooted_device" in result["device_reasons"]
    assert "anomalous_ip" in result["device_reasons"]


def test_device_all_flags():
    """Emulador + root + IP → score 0.85 (clamped)."""
    result = evaluate_device_risk(
        device_id="DEV-003",
        is_emulator=True,
        is_rooted=True,
        anomalous_ip=True,
    )
    assert result["device_risk_score"] == 0.85
    assert len(result["device_reasons"]) == 3


# ═══════════════════════════════════════════════════════════════════════
# BehavioralRisk tests
# ═══════════════════════════════════════════════════════════════════════

def test_behavioral_clean():
    """Comportamiento normal → score 0."""
    result = evaluate_behavioral_risk(
        amount=500,
        interaction_time_ms=5000,
        navigation_steps=3,
        historical_amounts=[400, 500, 600],
    )
    assert result["behavioral_risk_score"] == 0.0
    assert result["behavioral_reasons"] == []


def test_behavioral_bot_speed():
    """< 1200ms → fast_interaction alto (0.35)."""
    result = evaluate_behavioral_risk(
        amount=100,
        interaction_time_ms=800,
        navigation_steps=3,
    )
    assert result["suspicious_interaction_speed"] is True
    assert result["behavioral_risk_score"] == 0.35


def test_behavioral_medium_speed():
    """1200–2500ms → fast_interaction medio (0.175)."""
    result = evaluate_behavioral_risk(
        amount=100,
        interaction_time_ms=1500,
        navigation_steps=3,
    )
    assert result["suspicious_interaction_speed"] is True
    assert result["behavioral_risk_score"] == 0.175


def test_behavioral_zero_navigation():
    """0 navigation_steps → sospechoso alto (0.20)."""
    result = evaluate_behavioral_risk(
        amount=100,
        interaction_time_ms=5000,
        navigation_steps=0,
    )
    assert result["suspicious_navigation"] is True
    assert result["behavioral_risk_score"] == 0.20


def test_behavioral_anomalous_amount():
    """Monto desvía > 3x promedio histórico."""
    result = evaluate_behavioral_risk(
        amount=50000,
        interaction_time_ms=5000,
        navigation_steps=3,
        historical_amounts=[100, 200, 150],
    )
    assert result["suspicious_amount_pattern"] is True
    assert result["behavioral_risk_score"] == 0.45


def test_behavioral_no_history():
    """Sin historial → no penaliza monto."""
    result = evaluate_behavioral_risk(
        amount=50000,
        interaction_time_ms=5000,
        navigation_steps=3,
        historical_amounts=[],
    )
    assert result["suspicious_amount_pattern"] is False


def test_behavioral_all_suspicious():
    """Todas las señales activas → score clamped a 1.0."""
    result = evaluate_behavioral_risk(
        amount=50000,
        interaction_time_ms=500,
        navigation_steps=0,
        historical_amounts=[100, 200, 150],
    )
    assert result["behavioral_risk_score"] == 1.0
    assert len(result["behavioral_reasons"]) == 3


# ═══════════════════════════════════════════════════════════════════════
# Integración: telemetry.get_device_signals
# ═══════════════════════════════════════════════════════════════════════

def test_integration_clean():
    """Escenario limpio → scores bajos, claves compatibles con classifier.py."""
    result = get_device_signals(
        device_id="DEV-CLEAN",
        amount=500,
        interaction_time_ms=5000,
        navigation_steps=3,
        historical_amounts=[400, 500, 600],
    )
    # Claves que classifier.py ya consume
    assert "is_emulator" in result
    assert "anomalous_ip" in result
    assert "suspicious_typing_speed" in result
    # Nuevas señales
    assert "device_risk_score" in result
    assert "behavioral_risk_score" in result
    assert "reasons" in result
    # Valores esperados
    assert result["device_risk_score"] == 0.0
    assert result["behavioral_risk_score"] == 0.0


def test_integration_high_risk():
    """Escenario extremo: rooted + bot + monto anómalo."""
    result = get_device_signals(
        device_id="DEV-RISK",
        is_rooted=True,
        anomalous_ip=True,
        interaction_time_ms=500,
        navigation_steps=0,
        amount=50000,
        historical_amounts=[100, 200],
    )
    assert result["device_risk_score"] == 0.55
    assert result["behavioral_risk_score"] == 1.0
    assert result["is_rooted"] is True
    assert result["suspicious_typing_speed"] is True
    assert result["suspicious_amount_pattern"] is True
    assert len(result["reasons"]) >= 4
