const RISK_CONFIG = {
    BAJO: { emoji: '✅', label: 'RIESGO BAJO', color: '#22c55e', bg: 'rgba(34,197,94,0.08)' },
    MEDIO: { emoji: '⚠️', label: 'RIESGO MEDIO', color: '#f59e0b', bg: 'rgba(245,158,11,0.08)' },
    ALTO: { emoji: '🚨', label: 'RIESGO ALTO', color: '#ef4444', bg: 'rgba(239,68,68,0.08)' },
}

export default function RiskDashboard({ result }) {
    if (!result) return null
    if (result.error) return <div className="dashboard error">❌ Error: {result.error}</div>

    const config = RISK_CONFIG[result.risk_level] || RISK_CONFIG.BAJO
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
                <p className="score-label">Risk Score · Confianza: {Math.round((result.confidence || 0) * 100)}%</p>
            </div>

            {/* ─── Razonamiento del LLM ────────────────────────────────── */}
            {result.reasoning && (
                <div className="reasoning-section">
                    <h3>🧠 Análisis del LLM</h3>
                    <p className="reasoning-text">{result.reasoning}</p>
                </div>
            )}

            {/* ─── Señales activadas ───────────────────────────────────── */}
            <div className="signals">
                <h3>Señales Detectadas</h3>
                <ul>
                    <Signal label="Emulador detectado" active={signals.is_emulator} />
                    <Signal label="IP anómala" active={signals.anomalous_ip} />
                    <Signal label="Velocidad sospechosa" active={signals.suspicious_typing_speed} />
                    <Signal label="Navegación sospechosa" active={signals.suspicious_navigation} />
                    <Signal label="Patrón de monto anómalo" active={signals.suspicious_amount_pattern} />
                    <Signal label="Red de mulas" active={(result.signals?.mule_score || 0) > 0} score={result.signals?.mule_score} />
                </ul>
            </div>

            {/* ─── Risk Factors ─────────────────────────────────────────── */}
            {result.risk_factors?.length > 0 && (
                <div className="risk-factors">
                    <h3>Factores de Riesgo</h3>
                    <div className="factor-tags">
                        {result.risk_factors.map((f, i) => (
                            <span key={i} className="factor-tag" style={{ borderColor: config.color, color: config.color }}>
                                {f}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* ─── HITL Results ─────────────────────────────────────────── */}
            {result.hitl_required && (
                <div className="hitl-section">
                    <h3>🔐 Verificación HITL</h3>
                    {result.facial_result?.score != null && (
                        <div className={`hitl-badge ${result.facial_result.passed ? 'passed' : 'failed'}`}>
                            👤 Reconocimiento Facial: <strong>{Math.round(result.facial_result.score * 100)}%</strong>
                            {result.facial_result.passed ? ' ✅ Aprobado' : ' ❌ No pasó'}
                        </div>
                    )}
                    {result.voice_result?.verified != null && (
                        <div className={`hitl-badge ${result.voice_result.verified ? 'passed' : 'failed'}`}>
                            🎙️ Voice Bot: <strong>{result.voice_result.verified ? 'Confirmado' : 'No confirmado'}</strong>
                        </div>
                    )}
                </div>
            )}

            {/* ─── Resultado Final ──────────────────────────────────────── */}
            <div className={`final-result ${result.blocked ? 'blocked' : 'approved'}`}>
                {result.blocked ? '🚫 TRANSACCIÓN BLOQUEADA' : '✅ TRANSACCIÓN APROBADA'}
            </div>

            {/* ─── Reporte ──────────────────────────────────────────────── */}
            {result.report && (
                <div className="report-section">
                    <h3>📋 Reporte de Fraude</h3>
                    <p className="report-text">{result.report}</p>
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
