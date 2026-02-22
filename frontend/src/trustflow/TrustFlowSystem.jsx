import { useState, useEffect, useRef, useCallback, Fragment } from 'react'
import { mapResultToStep } from '../api_client.js'
import {
    Shield, ShieldCheck, ShieldAlert,
    PhoneCall, User, TriangleAlert,
    Lock, CircleCheck, CircleX,
    RefreshCw, PhoneForwarded, Fingerprint,
    Info, Mic, Headphones,
} from 'lucide-react'

// =====================================================
//  DESIGNER NOTES
// =====================================================
const designerNotes = {
    transaction: {
        title: "Análisis de Riesgo (Motor de Reglas)",
        trigger: "Transferencia inusual (Monto alto, dispositivo nuevo o IP riesgosa).",
        escalation: "Escala a Step-up Authentication (Nivel 1).",
        uxFocus: "Fricción cero hasta que se detecta la anomalía."
    },
    step_up: {
        title: "Step-up Authentication",
        trigger: "Riesgo Medio/Alto detectado.",
        escalation: "Si falla 2 veces o el riesgo contextual aumenta -> Escala a Biometría.",
        uxFocus: "Transparencia: Explicar *por qué* pedimos un código extra (Proteger sus fondos)."
    },
    biometric: {
        title: "BiometricVerifier (Liveness Activo)",
        trigger: "Riesgo Alto o fallo en Step-up.",
        escalation: "Si la biometría es dudosa (Deepfake score alto, poca luz) -> Escala a Voice Bot.",
        uxFocus: "Instrucciones claras para pruebas de vida (sonreír, girar la cabeza) reduciendo la ansiedad."
    },
    voice_bot: {
        title: "HITL CallAgent (Voice Bot)",
        trigger: "Riesgo Crítico, biometría fallida, o sospecha de fraude en progreso (Scam).",
        escalation: "Si detecta estrés en la voz, input inválido, o el usuario usa la palabra de seguridad -> Escala a Humano.",
        uxFocus: "Tono calmado, opciones claras. Diseño Anti-Coerción integrado."
    },
    human_agent: {
        title: "Escalamiento a Humano (HITL)",
        trigger: "Fallo completo de sistemas automatizados o alerta de coerción/fraude detectada.",
        escalation: "Bloqueo preventivo de la cuenta si el agente no puede verificar al usuario.",
        uxFocus: "Tranquilizar al usuario, el agente tiene todo el contexto (no hacerle repetir información)."
    },
    silent_alarm: {
        title: "Alarma Silenciosa Activada",
        trigger: "El usuario activó el protocolo Anti-Coerción durante la llamada.",
        escalation: "Simular éxito de transferencia para engañar al atacante, pero retener fondos y notificar autoridades/equipo de fraude.",
        uxFocus: "Proteger la integridad física del usuario."
    },
    success: {
        title: "Verificación Exitosa",
        trigger: "El usuario pasó los controles de seguridad.",
        escalation: "Ninguna. Flujo completado.",
        uxFocus: "Refuerzo positivo de seguridad."
    }
}

import PhoneWrapper from '../components/PhoneWrapper.jsx'

// =====================================================
//  STEP COMPONENTS
// =====================================================
function StepTransaction({ result }) {
    const amount = result?.amount || 5000
    const receiver = result?.transaction_id || 'Destinatario'
    return (
        <div className="flex flex-col h-full p-6 bg-slate-50">
            <div className="flex items-center gap-2 mb-8 mt-4 text-blue-600">
                <ShieldCheck className="w-6 h-6" />
                <span className="font-semibold text-lg">SecureBank</span>
            </div>
            <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 mb-6">
                <p className="text-slate-500 text-sm font-medium mb-1">Transferencia</p>
                <p className="text-slate-800 font-bold text-xl mb-4">{receiver}</p>
                <p className="text-slate-500 text-sm font-medium mb-1">Monto</p>
                <p className="text-slate-800 font-bold text-3xl">$ {Number(amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
            </div>
            <div className="mt-auto flex items-center justify-center gap-2 text-slate-400 text-sm">
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Esperando verificación...</span>
            </div>
        </div>
    )
}

function StepUpAuth({ onNext }) {
    return (
        <div className="flex flex-col h-full p-6">
            <div className="bg-blue-50 p-4 rounded-xl mb-6 flex items-start gap-3 mt-4">
                <Info className="w-6 h-6 text-blue-600 shrink-0 mt-0.5" />
                <div>
                    <h3 className="text-sm font-semibold text-blue-900">Protegiendo tu dinero</h3>
                    <p className="text-xs text-blue-700 mt-1">
                        Detectamos una transferencia inusual por el monto. Para tu seguridad, verifiquemos que eres tú.
                    </p>
                </div>
            </div>
            <div className="text-center mb-8">
                <Lock className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                <h2 className="text-xl font-bold text-slate-800">Código de Seguridad</h2>
                <p className="text-slate-500 text-sm mt-2">Enviado a tu dispositivo principal</p>
            </div>
            <div className="flex justify-between gap-2 mb-8">
                {[1, 2, 3, 4, 5, 6].map(i => (
                    <div key={i} className="w-10 h-12 border-2 border-slate-200 rounded-lg flex items-center justify-center text-xl font-bold text-slate-400">
                        •
                    </div>
                ))}
            </div>
            <div className="mt-auto flex flex-col gap-3">
                <button
                    onClick={() => onNext('success')}
                    className="w-full bg-slate-100 text-slate-700 py-3 rounded-xl font-semibold hover:bg-slate-200 transition-colors"
                >
                    Simular: Código Correcto ✅
                </button>
                <button
                    onClick={() => onNext('biometric')}
                    className="w-full bg-orange-100 text-orange-700 py-3 rounded-xl font-semibold hover:bg-orange-200 transition-colors border border-orange-200 flex items-center justify-center gap-2"
                >
                    <TriangleAlert className="w-4 h-4" />
                    Simular: Fallo / Timeout (Escalar)
                </button>
            </div>
        </div>
    )
}

function StepBiometric({ onNext }) {
    const videoRef = useRef(null)
    const streamRef = useRef(null)

    useEffect(() => {
        let mounted = true
        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } })
            .then(stream => {
                if (mounted && videoRef.current) {
                    streamRef.current = stream
                    videoRef.current.srcObject = stream
                }
            })
            .catch(err => console.warn('Camera access denied:', err))

        return () => {
            mounted = false
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(t => t.stop())
            }
        }
    }, [])

    return (
        <div className="flex flex-col h-full relative bg-slate-900 text-white pt-10">
            <div className="flex-1 flex flex-col items-center justify-center relative">
                <div className="w-48 h-64 border-4 border-dashed border-green-500/60 rounded-full flex flex-col items-center justify-center bg-slate-800 mb-8 relative overflow-hidden shadow-[0_0_30px_rgba(34,197,94,0.2)]">
                    <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        muted
                        className="absolute inset-0 w-full h-full object-cover scale-x-[-1]"
                    />
                    {/* Scan line overlay */}
                    <div className="absolute inset-x-0 top-0 h-1 bg-green-500 shadow-[0_0_15px_#22c55e] animate-bounce z-10"></div>
                    {/* Fallback icon if no camera */}
                    <User className="w-24 h-24 text-slate-500 opacity-20 absolute" />
                </div>
                <h2 className="text-xl font-bold text-white mb-2">Biometría Activa</h2>
                <p className="text-green-400 font-medium animate-pulse flex items-center gap-2">
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Por favor, sonríe a la cámara...
                </p>
            </div>
            <div className="p-6 flex flex-col gap-3 bg-slate-900 z-10">
                <button
                    onClick={() => onNext('success')}
                    className="w-full bg-slate-800 text-white py-3 rounded-xl font-semibold hover:bg-slate-700 transition-colors border border-slate-700"
                >
                    Simular: Liveness Exitoso ✅
                </button>
                <button
                    onClick={() => onNext('voice_bot')}
                    className="w-full bg-red-900/40 text-red-400 py-3 rounded-xl font-semibold hover:bg-red-900/60 transition-colors border border-red-800/50 flex items-center justify-center gap-2"
                >
                    <ShieldAlert className="w-4 h-4" />
                    Simular: Duda/Fallo (Escalar a Llamada)
                </button>
            </div>
        </div>
    )
}

function StepVoiceBot() {
    return (
        <div className="flex flex-col h-full bg-slate-900 text-white relative pt-12">
            <div className="flex flex-col items-center justify-center flex-1">
                <div className="w-24 h-24 bg-blue-600/20 rounded-full flex items-center justify-center mb-6 animate-pulse">
                    <PhoneCall className="w-10 h-10 text-blue-400" />
                </div>
                <h2 className="text-2xl font-bold mb-1">SecureBank Bot</h2>
                <p className="text-slate-400 mb-8">Llamada de Seguridad en curso...</p>
                <div className="w-full max-w-[280px] bg-slate-800 p-4 rounded-2xl border border-slate-700 relative">
                    <p className="text-sm text-slate-300 italic">
                        "Hola. Detectamos un intento de transferencia por $5,000. Si fuiste tú, di <strong>'Autorizo'</strong>. Si no, di <strong>'Cancelar'</strong>."
                    </p>
                    <div className="mt-3 pt-3 border-t border-slate-700">
                        <p className="text-xs text-orange-300 flex items-start gap-1">
                            <TriangleAlert className="w-3 h-3 shrink-0 mt-0.5" />
                            "Si te están obligando, di <strong>'Asistencia'</strong> o presiona 9."
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}

function StepHumanAgent() {
    return (
        <div className="flex flex-col h-full bg-slate-50 justify-center items-center p-6 text-center pt-10">
            <div className="relative mb-6">
                <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center">
                    <Headphones className="w-10 h-10 text-blue-600" />
                </div>
                <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-green-500 rounded-full border-2 border-white flex items-center justify-center">
                    <div className="w-2 h-2 bg-white rounded-full animate-ping"></div>
                </div>
            </div>
            <h2 className="text-xl font-bold text-slate-800 mb-2">Transfiriendo a un Especialista</h2>
            <p className="text-slate-500 text-sm mb-8">
                No pudimos verificar tu identidad de forma automática. Un agente especializado en seguridad revisará tu caso en breve.
            </p>
            <div className="w-full bg-white p-4 rounded-xl shadow-sm border border-slate-100 text-left">
                <p className="text-xs text-slate-400 font-semibold uppercase mb-2">Contexto enviado al agente:</p>
                <ul className="text-sm text-slate-700 space-y-2">
                    <li className="flex items-center gap-2"><CircleCheck className="w-4 h-4 text-green-500" /> Transferencia de $5,000 retenida</li>
                    <li className="flex items-center gap-2"><CircleX className="w-4 h-4 text-red-500" /> Biometría dudosa detectada</li>
                    <li className="flex items-center gap-2"><TriangleAlert className="w-4 h-4 text-orange-500" /> Requiere validación de identidad KBA</li>
                </ul>
            </div>
        </div>
    )
}

function StepSuccess({ onReset }) {
    return (
        <div className="flex flex-col h-full bg-green-50 justify-center items-center p-6 text-center pt-10">
            <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mb-6">
                <CircleCheck className="w-12 h-12 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-slate-800 mb-2">Verificación Exitosa</h2>
            <p className="text-slate-600 mb-8">
                Tu identidad ha sido confirmada y la transferencia está en proceso. Gracias por ayudarnos a mantener tu cuenta segura.
            </p>
            <button onClick={onReset} className="mt-auto bg-green-600 text-white w-full py-4 rounded-xl font-semibold hover:bg-green-700 transition-colors">
                Volver al Inicio
            </button>
        </div>
    )
}

function StepSilentAlarm() {
    return (
        <div className="flex flex-col h-full bg-slate-50 justify-center items-center p-6 text-center pt-10">
            <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mb-6">
                <CircleCheck className="w-12 h-12 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-slate-800 mb-2">Transferencia "Aprobada"</h2>
            <p className="text-slate-600 mb-6">
                La operación se ha procesado exitosamente.
            </p>
            <div className="w-full bg-red-50 border-2 border-red-500 border-dashed p-4 rounded-xl relative">
                <div className="absolute -top-3 left-4 bg-red-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
                    Vista Interna (Oculto al usuario)
                </div>
                <div className="flex items-center gap-2 text-red-700 font-bold mb-1">
                    <ShieldAlert className="w-5 h-5" /> Alarma Silenciosa Activa
                </div>
                <p className="text-xs text-red-600 text-left">
                    Los fondos están congelados en una cuenta puente (Escrow). Equipo de fraude y policía notificados. El atacante ve una pantalla de éxito.
                </p>
            </div>
        </div>
    )
}

// =====================================================
//  MAIN COMPONENT
// =====================================================
export default function TrustFlowSystem({ result, onBack }) {
    const initialStep = mapResultToStep(result)
    const [currentStep, setCurrentStep] = useState(initialStep)
    const transactionId = result?.transaction_id || null

    // Expose setCurrentStep for external webhook / backend triggers
    useEffect(() => {
        window.__trustflow = {
            setStep: setCurrentStep,
            getStep: () => currentStep,
            transactionId,
        }
        return () => { delete window.__trustflow }
    }, [currentStep, transactionId])

    const resetFlow = () => {
        if (onBack) onBack()
        else setCurrentStep('step_up')
    }

    const renderPhoneUI = () => {
        switch (currentStep) {
            case 'transaction': return <StepTransaction result={result} />
            case 'step_up': return <StepUpAuth onNext={setCurrentStep} />
            case 'biometric': return <StepBiometric onNext={setCurrentStep} />
            case 'voice_bot': return <StepVoiceBot />
            case 'human_agent': return <StepHumanAgent />
            case 'success': return <StepSuccess onReset={resetFlow} />
            case 'silent_alarm': return <StepSilentAlarm />
            default: return <StepTransaction result={result} />
        }
    }

    const currentNotes = designerNotes[currentStep]
    const riskLevel = (currentStep === 'voice_bot' || currentStep === 'human_agent' || currentStep === 'silent_alarm')
        ? 'Crítico'
        : currentStep === 'biometric' ? 'Alto' : 'Medio'

    const stepsReached = (step) => {
        const order = ['transaction', 'step_up', 'biometric', 'voice_bot', 'human_agent']
        const idx = order.indexOf(step)
        const curIdx = order.indexOf(currentStep)
        return curIdx >= idx
    }

    return (
        <div className="min-h-[80vh] bg-slate-100 font-sans p-4 md:p-8 flex flex-col items-center justify-center rounded-xl">
            {/* Back button */}
            <div className="max-w-6xl w-full mb-4">
                <button
                    onClick={resetFlow}
                    className="flex items-center gap-2 text-slate-600 hover:text-slate-900 font-semibold text-sm transition-colors"
                >
                    ← Volver al Analizador
                </button>
            </div>
            <div className="max-w-6xl w-full flex flex-col lg:flex-row gap-8 items-center lg:items-start justify-center">

                {/* Left Column: Phone Simulator */}
                <div className="flex flex-col items-center">
                    <div className="mb-4 text-center">
                        <h2 className="text-lg font-bold text-slate-800">Experiencia de Usuario (UX)</h2>
                        <p className="text-sm text-slate-500">Prototipo interactivo del flujo</p>
                    </div>
                    <PhoneWrapper>
                        {renderPhoneUI()}
                    </PhoneWrapper>
                </div>

                {/* Right Column: Trust Flow Designer Dashboard */}
                <div className="flex-1 w-full max-w-2xl flex flex-col gap-6">
                    <div className="bg-white rounded-3xl p-6 md:p-8 shadow-xl border border-slate-200">

                        <div className="flex flex-col sm:flex-row items-start justify-between mb-8 pb-6 border-b border-slate-100 gap-4">
                            <div>
                                <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                                    <ShieldCheck className="w-7 h-7 text-blue-600" />
                                    Trust Flow & HITL Designer
                                </h1>
                                <p className="text-slate-500 mt-1">
                                    Panel de control de escalamiento y lógica de seguridad.
                                </p>
                            </div>
                            <div className="bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-sm font-semibold border border-blue-200 flex items-center gap-1 whitespace-nowrap">
                                <Shield className="w-4 h-4" />
                                Nivel Riesgo: {riskLevel}
                            </div>
                        </div>

                        {/* Current Module Details */}
                        <div className="mb-8">
                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Módulo Activo</h3>
                            <div className="bg-slate-50 rounded-2xl p-5 border border-slate-200 shadow-inner">
                                <h2 className="text-xl font-bold text-slate-800 mb-4">{currentNotes.title}</h2>
                                <div className="space-y-4">
                                    <div className="flex items-start gap-3">
                                        <div className="mt-1 bg-white p-1.5 rounded-lg shadow-sm border border-slate-200">
                                            <RefreshCw className="w-4 h-4 text-slate-600" />
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-slate-700">Trigger (Disparador)</p>
                                            <p className="text-sm text-slate-600">{currentNotes.trigger}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-start gap-3">
                                        <div className="mt-1 bg-white p-1.5 rounded-lg shadow-sm border border-slate-200">
                                            <Info className="w-4 h-4 text-blue-600" />
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-slate-700">UX de Transparencia</p>
                                            <p className="text-sm text-slate-600">{currentNotes.uxFocus}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-start gap-3">
                                        <div className="mt-1 bg-white p-1.5 rounded-lg shadow-sm border border-slate-200">
                                            <PhoneForwarded className="w-4 h-4 text-orange-500" />
                                        </div>
                                        <div>
                                            <p className="text-sm font-bold text-slate-700">Regla de Escalamiento</p>
                                            <p className="text-sm text-slate-600">{currentNotes.escalation}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Special Deliverables — Voice Bot */}
                        {currentStep === 'voice_bot' && (
                            <div className="mb-6">
                                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Entregable: Guion Anti-Coerción</h3>
                                <div className="bg-blue-900 text-white rounded-2xl p-5 shadow-lg border border-blue-800">
                                    <div className="flex items-center gap-2 mb-3 text-blue-300">
                                        <Mic className="w-5 h-5" />
                                        <span className="font-semibold text-sm">Script del HITL_CallAgent</span>
                                    </div>
                                    <div className="space-y-3 font-mono text-sm bg-slate-900/50 p-4 rounded-xl border border-slate-700">
                                        <p><span className="text-blue-400">Bot:</span> "Hola [Nombre]. Detectamos un intento de transferencia por $5,000 hacia [Destino]."</p>
                                        <p><span className="text-blue-400">Bot:</span> "Si autorizas esta operación, di 'Autorizo'. Si no la reconoces, di 'Cancelar'."</p>
                                        <p className="text-orange-300 border-l-2 border-orange-500 pl-3 py-1 bg-orange-950/30">
                                            <span className="font-bold">Protocolo Anti-Coerción:</span> "Si te encuentras bajo amenaza o te están obligando a hacer esto, por favor di la palabra 'Asistencia' o presiona la tecla 9 para cancelar de forma segura."
                                        </p>
                                    </div>
                                    <p className="text-xs text-blue-200 mt-4 opacity-80">
                                        *Nota de diseño: El bot debe hablar con cadencia pausada. El sistema de NLP está configurado para detectar estrés en la voz del usuario.
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Special Deliverables — Biometric */}
                        {currentStep === 'biometric' && (
                            <div className="mb-6">
                                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Entregable: BiometricVerifier</h3>
                                <div className="bg-slate-800 text-white rounded-2xl p-5 shadow-lg">
                                    <div className="flex items-center gap-2 mb-3 text-green-400">
                                        <Fingerprint className="w-5 h-5" />
                                        <span className="font-semibold text-sm">Configuración de Liveness Activo</span>
                                    </div>
                                    <ul className="text-sm space-y-2 text-slate-300">
                                        <li>• <strong className="text-white">Desafío:</strong> Aleatorizado (Sonrisa, parpadeo, giro de cabeza).</li>
                                        <li>• <strong className="text-white">Detección de Inyección:</strong> Análisis de bordes de pantalla y reflejos para evitar uso de videos pregrabados.</li>
                                        <li>• <strong className="text-white">Tiempo límite:</strong> 15 segundos para completar el desafío antes de escalar al Voice Bot.</li>
                                    </ul>
                                </div>
                            </div>
                        )}

                        {/* Friction Ladder */}
                        <div>
                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Escalera de Fricción</h3>
                            <div className="flex items-center justify-between text-xs font-bold text-slate-400">
                                {['transaction', 'step_up', 'biometric', 'voice_bot', 'human_agent'].map((step, i, arr) => {
                                    const labels = ['Transacción', 'Step-up', 'Biometría', 'Voice Bot', 'Humano']
                                    const reached = stepsReached(step)
                                    const color = (step === 'voice_bot' || step === 'human_agent')
                                        ? 'text-red-500'
                                        : step === 'biometric' ? 'text-orange-500' : 'text-blue-600'
                                    return (
                                        <Fragment key={step}>
                                            <div className={`flex flex-col items-center gap-1 ${reached ? color : ''}`}>
                                                <div className="w-3 h-3 rounded-full bg-current"></div>
                                                <span>{labels[i]}</span>
                                            </div>
                                            {i < arr.length - 1 && (
                                                <div className={`flex-1 h-0.5 ${stepsReached(arr[i + 1]) ? 'bg-blue-600' : 'bg-slate-200'}`}></div>
                                            )}
                                        </Fragment>
                                    )
                                })}
                            </div>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    )
}
