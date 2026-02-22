import { useState } from 'react'
import { analyzeTransaction } from '../api_client.js'
import { ShieldCheck, Send, Wifi, CreditCard, ArrowRightLeft, DollarSign } from 'lucide-react'

const DEMO_ACCOUNTS = [
    { label: 'Cuenta normal', value: 'ACC-NORMAL-001' },
    { label: 'Red de mulas (baja)', value: 'ACC-MULE-004' },
    { label: 'Red de mulas (alta)', value: 'ACC-MULE-001' },
    { label: 'Lista negra', value: 'ACC-BLOCKED-001' },
]

export default function TransactionForm({ onResult, onLoading }) {
    const [form, setForm] = useState({
        sender_account: 'ACC-SENDER-001',
        receiver_account: 'ACC-BLOCKED-001',
        amount: 2000,
        currency: 'USD',
        ip_address: '185.220.101.1',
        user_agent: navigator.userAgent,
    })

    const handleSubmit = async (e) => {
        e.preventDefault()
        onLoading(true)
        try {
            // Generate random historical amounts (5–10 past transactions)
            const historyLen = Math.floor(Math.random() * 6) + 5
            const historical_amounts = Array.from({ length: historyLen }, () =>
                Math.round((Math.random() * 2950 + 50) * 100) / 100
            )

            const payload = {
                ...form,
                amount: parseFloat(form.amount),
                transaction_id: `TXN-${Date.now()}`,
                device_id: `DEV-${navigator.userAgent.length}-${Date.now()}`,
                user_agent: navigator.userAgent,
                // Device signals (Rol 3)
                is_emulator: true,
                is_rooted: true,
                anomalous_ip_flag: true,
                // Behavioral signals (Rol 3)
                interaction_time_ms: Math.floor(Math.random() * 25000) + 3000,
                navigation_steps: Math.floor(Math.random() * 8) + 2,
                historical_amounts,
            }
            console.log('📤 [REQUEST] /analyze payload:', JSON.stringify(payload, null, 2))
            const result = await analyzeTransaction(payload)
            console.log('📥 [RESPONSE] /analyze result:', JSON.stringify(result, null, 2))
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
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                    <CreditCard className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                    <h2 className="text-xl font-bold text-slate-900">Simulador de Transacción</h2>
                    <p className="text-sm text-slate-500">Ingresa los datos para analizar</p>
                </div>
            </div>

            <div className="flex flex-col gap-1.5">
                <label className="text-sm font-semibold text-slate-700 flex items-center gap-1.5">
                    <Send className="w-3.5 h-3.5 text-slate-400" />
                    Cuenta Origen
                </label>
                <input
                    value={form.sender_account}
                    onChange={set('sender_account')}
                    required
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                />
            </div>

            <div className="flex flex-col gap-1.5">
                <label className="text-sm font-semibold text-slate-700 flex items-center gap-1.5">
                    <ArrowRightLeft className="w-3.5 h-3.5 text-slate-400" />
                    Cuenta Destino
                </label>
                <select
                    value={form.receiver_account}
                    onChange={set('receiver_account')}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all appearance-none cursor-pointer"
                >
                    {DEMO_ACCOUNTS.map((a) => (
                        <option key={a.value} value={a.value}>{a.label} — {a.value}</option>
                    ))}
                </select>
            </div>

            <div className="flex flex-col gap-1.5">
                <label className="text-sm font-semibold text-slate-700 flex items-center gap-1.5">
                    <DollarSign className="w-3.5 h-3.5 text-slate-400" />
                    Monto ({form.currency})
                </label>
                <input
                    type="number"
                    min="1"
                    value={form.amount}
                    onChange={set('amount')}
                    required
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                />
            </div>

            <div className="flex flex-col gap-1.5">
                <label className="text-sm font-semibold text-slate-700 flex items-center gap-1.5">
                    <Wifi className="w-3.5 h-3.5 text-slate-400" />
                    IP de Origen
                    <span className="text-slate-400 font-normal">(dejar vacío = normal)</span>
                </label>
                <input
                    placeholder="ej. 185.220.101.1 para simular IP anómala"
                    value={form.ip_address}
                    onChange={set('ip_address')}
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 text-sm font-medium placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                />
            </div>

            <button
                type="submit"
                className="w-full mt-2 bg-blue-600 text-white py-4 rounded-xl font-semibold text-base hover:bg-blue-700 transition-colors shadow-md shadow-blue-200 flex items-center justify-center gap-2"
            >
                <ShieldCheck className="w-5 h-5" />
                Analizar Transacción
            </button>
        </form>
    )
}
