import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
    baseURL: BASE_URL,
    headers: { 'Content-Type': 'application/json' },
})

/**
 * Envía un TransactionIntent al backend y retorna el TransactionResult.
 * @param {Object} transactionData
 * @param {string} transactionData.transaction_id
 * @param {string} transactionData.sender_account
 * @param {string} transactionData.receiver_account
 * @param {number} transactionData.amount
 * @param {string} [transactionData.currency]
 * @param {string} [transactionData.device_id]
 * @param {string} [transactionData.ip_address]
 * @param {string} [transactionData.user_agent]
 * @returns {Promise<Object>} TransactionResult
 */
export async function analyzeTransaction(transactionData) {
    const response = await api.post('/analyze', transactionData)
    return response.data
}

/**
 * Health check del backend.
 * @returns {Promise<Object>}
 */
export async function checkHealth() {
    const response = await api.get('/health')
    return response.data
}
