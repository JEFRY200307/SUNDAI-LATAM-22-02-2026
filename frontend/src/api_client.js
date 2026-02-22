import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
    baseURL: BASE_URL,
    headers: { 'Content-Type': 'application/json' },
})

// ─── Trust Flow API ──────────────────────────────────────────────────────────
// Adapted to the existing backend endpoints: POST /analyze and GET /health.
// The Trust Flow logic (step-up, biometric, voice-bot, etc.) is driven
// by the backend's `decision` and `hitl_action` fields in the /analyze response.

/**
 * Envía un TransactionIntent al backend y retorna el TransactionResult.
 * The backend returns: { decision, risk_score, signals, hitl_triggered, hitl_action }
 *
 * Frontend maps hitl_action to Trust Flow steps:
 *   - "STEP_UP_AUTH_OTP"              → step_up
 *   - "TRANSACTION_BLOCKED_VOICE_BOT" → voice_bot
 *   - null (NO_FRAUD)                 → success
 *
 * @param {Object} transactionData
 * @returns {Promise<Object>} TransactionResult
 */
export async function analyzeTransaction(transactionData) {
    const response = await api.post('/analyze', transactionData)
    return response.data
}

/**
 * Maps the backend hitl_action to a Trust Flow step name.
 * @param {Object} result - TransactionResult from /analyze
 * @returns {string} Trust Flow step name
 */
export function mapResultToStep(result) {
    if (!result || result.error) return 'step_up'

    if (result.decision === 'NO_FRAUD') return 'success'

    switch (result.hitl_action) {
        case 'STEP_UP_AUTH_OTP':
            return 'step_up'
        case 'TRANSACTION_BLOCKED_VOICE_BOT':
            return 'voice_bot'
        default:
            return 'step_up'
    }
}

/**
 * Health check del backend.
 * @returns {Promise<Object>}
 */
export async function checkHealth() {
    const response = await api.get('/health')
    return response.data
}
