import { useState } from 'react'
import { ShieldCheck } from 'lucide-react'
import TransactionForm from './components/TransactionForm.jsx'
import RiskDashboard from './dashboard/RiskDashboard.jsx'
import TrustFlowSystem from './trustflow/TrustFlowSystem.jsx'
import PhoneWrapper from './components/PhoneWrapper.jsx'

export default function App() {
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [showTrustFlow, setShowTrustFlow] = useState(false)

    const handleResult = (data) => {
        setResult(data)
        // After receiving analysis results, transition to Trust Flow
        setShowTrustFlow(true)
    }

    const handleBack = () => {
        setShowTrustFlow(false)
        setResult(null)
    }

    return (
        <div className="min-h-screen flex flex-col bg-slate-100 font-['Inter',system-ui,sans-serif]">
            <header className="bg-white border-b border-slate-200 px-6 py-4 shadow-sm">
                <div className="max-w-6xl mx-auto">
                    <h1 className="text-2xl font-bold text-slate-900">🛡️ Anti-Fraud Agent</h1>
                    <p className="text-blue-600 text-sm font-medium mt-0.5">SUNDAI LATAM · Hackathon 2026</p>
                </div>
            </header>

            {showTrustFlow ? (
                <main style={{ flex: 1, padding: '0' }}>
                    <TrustFlowSystem result={result} onBack={handleBack} />
                </main>
            ) : (
                <main className="flex-1 bg-slate-100 p-4 md:p-8 flex items-start justify-center">
                    <div className="max-w-6xl w-full flex flex-col lg:flex-row gap-8 items-center lg:items-start justify-center mt-4">
                        {/* Phone simulator with form */}
                        <div className="flex flex-col items-center">
                            <div className="mb-4 text-center">
                                <h2 className="text-lg font-bold text-slate-800">Simulador de Transacción</h2>
                                <p className="text-sm text-slate-500">Ingresa los datos para analizar</p>
                            </div>
                            <PhoneWrapper>
                                <div className="flex flex-col h-full p-4 bg-slate-50 overflow-y-auto">
                                    <TransactionForm onResult={handleResult} onLoading={setLoading} />
                                    {loading && (
                                        <div className="flex flex-col items-center gap-3 mt-4">
                                            <div className="w-10 h-10 border-4 border-slate-200 border-t-blue-600 rounded-full animate-spin"></div>
                                            <p className="text-slate-400 text-sm font-medium">Analizando...</p>
                                        </div>
                                    )}
                                </div>
                            </PhoneWrapper>
                        </div>

                        {/* Right panel - info card */}
                        <div className="flex-1 w-full max-w-2xl">
                            <div className="bg-white rounded-3xl p-6 md:p-8 shadow-xl border border-slate-200">
                                <div className="flex items-center gap-3 mb-6">
                                    <ShieldCheck className="w-7 h-7 text-blue-600" />
                                    <div>
                                        <h2 className="text-xl font-bold text-slate-900">Motor de Detección de Fraude</h2>
                                        <p className="text-slate-500 text-sm">Sistema de análisis en tiempo real</p>
                                    </div>
                                </div>
                                <div className="space-y-4">
                                    <div className="bg-slate-50 rounded-2xl p-5 border border-slate-200">
                                        <h3 className="text-sm font-bold text-slate-700 mb-3">¿Cómo funciona?</h3>
                                        <ul className="text-sm text-slate-600 space-y-2.5">
                                            <li className="flex items-start gap-2">
                                                <span className="text-blue-500 mt-0.5">①</span>
                                                <span>Ingresa los datos de transacción en el simulador</span>
                                            </li>
                                            <li className="flex items-start gap-2">
                                                <span className="text-blue-500 mt-0.5">②</span>
                                                <span>El agente analiza señales de riesgo (IP, dispositivo, red de mulas)</span>
                                            </li>
                                            <li className="flex items-start gap-2">
                                                <span className="text-blue-500 mt-0.5">③</span>
                                                <span>Si detecta anomalías, activa el flujo Trust Flow & HITL</span>
                                            </li>
                                        </ul>
                                    </div>
                                    <div className="grid grid-cols-3 gap-3">
                                        <div className="bg-green-50 border border-green-200 rounded-xl p-3 text-center">
                                            <p className="text-2xl mb-1">✅</p>
                                            <p className="text-xs font-semibold text-green-700">Sin Fraude</p>
                                        </div>
                                        <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 text-center">
                                            <p className="text-2xl mb-1">⚠️</p>
                                            <p className="text-xs font-semibold text-amber-700">Posible</p>
                                        </div>
                                        <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-center">
                                            <p className="text-2xl mb-1">🚨</p>
                                            <p className="text-xs font-semibold text-red-700">Fraude</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </main>
            )}

            <footer className="bg-white border-t border-slate-200 text-center py-4 px-6">
                <p className="text-slate-400 text-sm">Anti-Fraud Agent · SUNDAI LATAM 2026 · Powered by FastAPI + React</p>
            </footer>
        </div>
    )
}
