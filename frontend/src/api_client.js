import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
    baseURL: BASE_URL,
    headers: { 'Content-Type': 'application/json' },
})

/** Analiza una transacción via el pipeline completo LangGraph */
export async function analyzeTransaction(transactionData) {
    const response = await api.post('/analyze', transactionData)
    return response.data
}

/** Health check del backend */
export async function checkHealth() {
    const response = await api.get('/health')
    return response.data
}

/** Obtiene estadísticas del log */
export async function getStats() {
    const response = await api.get('/stats')
    return response.data
}

/** Simula reconocimiento facial */
export async function simulateFacialRecognition(transactionId, userId) {
    const response = await api.post('/hitl/facial', {
        transaction_id: transactionId,
        user_id: userId,
    })
    return response.data
}

/** Simula voice bot */
export async function simulateVoiceBot(transactionId, userId, confirmed) {
    const response = await api.post('/hitl/voice', {
        transaction_id: transactionId,
        user_id: userId,
        confirmed,
    })
    return response.data
}

/** Obtiene el info del grafo */
export async function getGraphInfo() {
    const response = await api.get('/graph/info')
    return response.data
}

/** Obtiene reporte de fraude */
export async function getReport(transactionId) {
    const response = await api.get(`/report/${transactionId}`)
    return response.data
}

/** Simula batch de transacciones */
export async function simulateBatch(count = 5) {
    const response = await api.post(`/simulate/batch?count=${count}`)
    return response.data
}
