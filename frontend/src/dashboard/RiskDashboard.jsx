const DECISION_CONFIG = {
    NO_FRAUD: { emoji: '✅', label: 'SIN FRAUDE', color: '#22c55e' },
    POSSIBLE_FRAUD: { emoji: '⚠️', label: 'POSIBLE FRAUDE', color: '#f59e0b' },
    FRAUD: { emoji: '🚨', label: 'FRAUDE DETECTADO', color: '#ef4444' },
}

export default function RiskDashboard({ result }) {
    if (!result) return null
    if (result.error) return <div className="dashboard error">❌ Error: {result.error}</div>

    const config = DECISION_CONFIG[result.decision] || {}
    const signals = result.signals?.device || {}
    const scorePercent = Math.round((result.risk_score || 0) * 100)

    return (
        <div className="dashboard" style={{ borderColor: config.color }}>
            {/* ─── Decisión ────────────────────────────────────────────── */}
            <div className="decision" style={{ color: config.color }}>
                <span className="decision-emoji">{config.emoji}</span>
                <span className="decision-label">{config.label}</span>
            </div>

            {/* ─── Risk Score ──────────────────────────────────────────── */}
            <div className="score-section">
                <p className="score-value">{scorePercent}<span>%</span></p>
                <div className="score-bar-track">
                    <div
                        className="score-bar-fill"
                        style={{ width: `${scorePercent}%`, background: config.color }}
                    />
                </div>
                <p className="score-label">Risk Score</p>
            </div>

            {/* ─── Señales activadas ───────────────────────────────────── */}
            <div className="signals">
                <h3>Señales Detectadas</h3>
                <ul>
                    <Signal label="Emulador detectado" active={signals.is_emulator} />
                    <Signal label="IP anómala" active={signals.anomalous_ip} />
                    <Signal label="Tipeo sospechoso" active={signals.suspicious_typing_speed} />
                    <Signal label="Red de mulas" active={(result.signals?.mule_score || 0) > 0} score={result.signals?.mule_score} />
                </ul>
            </div>

            {/* ─── HITL ────────────────────────────────────────────────── */}
            {result.hitl_triggered && (
                <div className="hitl-badge">
                    🔐 Verificación adicional activada: <strong>{result.hitl_action}</strong>
                </div>
            )}

            {/* ─── Metadata ────────────────────────────────────────────── */}
            <p className="meta">ID: {result.transaction_id} · {new Date(result.timestamp).toLocaleTimeString()}</p>
        </div>
    )
}

function Signal({ label, active, score }) {
    return (
        <li className={`signal-item ${active ? 'active' : 'inactive'}`}>
            {active ? '🔴' : '🟢'} {label}
            {score !== undefined && active && <span className="signal-score"> ({Math.round(score * 100)}%)</span>}
        </li>
    )
}
