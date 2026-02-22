import { useState } from 'react'
import { analyzeTransaction } from '../api_client.js'

const DEMO_ACCOUNTS = [
    { label: 'Cuenta normal', value: 'ACC-NORMAL-001' },
    { label: 'Red de mulas (baja)', value: 'ACC-MULE-004' },
    { label: 'Red de mulas (alta)', value: 'ACC-MULE-001' },
    { label: 'Lista negra', value: 'ACC-BLOCKED-001' },
]

export default function TransactionForm({ onResult, onLoading }) {
    const [form, setForm] = useState({
        sender_account: 'ACC-SENDER-001',
        receiver_account: 'ACC-NORMAL-001',
        amount: 500,
        currency: 'USD',
        ip_address: '',
        user_agent: navigator.userAgent,
    })

    const handleSubmit = async (e) => {
        e.preventDefault()
        onLoading(true)
        try {
            const payload = {
                ...form,
                amount: parseFloat(form.amount),
                transaction_id: `TXN-${Date.now()}`,
                device_id: `DEV-${navigator.userAgent.length}-${Date.now()}`,
            }
            const result = await analyzeTransaction(payload)
            onResult(result)
        } catch (err) {
            console.error('Error al analizar transacción:', err)
            onResult({ error: err.message })
        } finally {
            onLoading(false)
        }
    }

    const set = (field) => (e) => setForm({ ...form, [field]: e.target.value })

    return (
        <form className="transaction-form" onSubmit={handleSubmit}>
            <h2>🏦 Simulador de Transacción</h2>

            <label>Cuenta Origen</label>
            <input value={form.sender_account} onChange={set('sender_account')} required />

            <label>Cuenta Destino</label>
            <select value={form.receiver_account} onChange={set('receiver_account')}>
                {DEMO_ACCOUNTS.map((a) => (
                    <option key={a.value} value={a.value}>{a.label} — {a.value}</option>
                ))}
            </select>

            <label>Monto ({form.currency})</label>
            <input type="number" min="1" value={form.amount} onChange={set('amount')} required />

            <label>IP de Origen (dejar vacío = normal)</label>
            <input
                placeholder="ej. 185.220.101.1 para simular IP anómala"
                value={form.ip_address}
                onChange={set('ip_address')}
            />

            <button type="submit">🔍 Analizar Transacción</button>
        </form>
    )
}
