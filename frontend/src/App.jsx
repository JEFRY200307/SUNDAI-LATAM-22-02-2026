import { useState } from 'react'
import TransactionForm from './components/TransactionForm.jsx'
import RiskDashboard from './dashboard/RiskDashboard.jsx'

export default function App() {
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)

    return (
        <div className="app-container">
            <header className="app-header">
                <div className="header-content">
                    <h1>🛡️ Anti-Fraud Agent</h1>
                    <p className="header-subtitle">SUNDAI LATAM · Hackathon 2026</p>
                </div>
            </header>

            <main className="app-main">
                <section className="form-section">
                    <TransactionForm onResult={setResult} onLoading={setLoading} />
                </section>

                <section className="result-section">
                    {loading ? (
                        <div className="loading">
                            <div className="spinner" />
                            <p>Analizando transacción...</p>
                        </div>
                    ) : (
                        <RiskDashboard result={result} />
                    )}
                </section>
            </main>

            <footer className="app-footer">
                <p>Anti-Fraud Agent · SUNDAI LATAM 2026 · Powered by FastAPI + React</p>
            </footer>
        </div>
    )
}
