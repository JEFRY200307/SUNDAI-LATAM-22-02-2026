# 🛡️ Hackathon Anti-Fraud App — SUNDAI LATAM 2026

> **Agente inteligente de detección y prevención de fraude en transacciones financieras en tiempo real.**  
> Construido en el marco del hackathon SUNDAI LATAM · 22 de febrero de 2026

---

## 📌 Descripción del Proyecto

Este proyecto implementa un **agente de IA orquestador** que analiza transacciones bancarias en tiempo real para clasificarlas como `NO_FRAUD`, `POSSIBLE_FRAUD` o `FRAUD`. Combina señales de comportamiento, inteligencia de grafos, biometría pasiva y lógica de decisión híbrida en un pipeline cohesivo, expuesto a través de un dashboard interactivo.

El sistema sigue un enfoque **MVP de 4 horas**, priorizando modularidad y claridad de responsabilidades por rol de ingeniero.

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  Simulador de Transacción  ──►  Dashboard de Riesgo     │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTP / REST
┌───────────────────▼─────────────────────────────────────┐
│               Backend Orquestador (FastAPI)              │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Behavioral & │  │ Graph Fraud  │  │  Risk Engine  │  │
│  │ Device Intel │  │ Intelligence │  │  & Decision   │  │
│  │   (Rol 3)    │  │   (Rol 2)    │  │   (Rol 1)     │  │
│  └──────────────┘  └──────────────┘  └───────┬───────┘  │
│                                              │           │
│                              ┌───────────────▼────────┐  │
│                              │  HITL & Trust Flow     │  │
│                              │       (Rol 4)          │  │
│                              └────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                    │
          ┌─────────▼─────────┐
          │  data/ (JSON log) │
          └───────────────────┘
```

---

## 🚀 Flujo de Ejecución (Pipeline de la Transacción)

El backend orquesta el siguiente pipeline **en orden estricto**:

1. 📥 **TransactionIntent** — Recibe la solicitud de transferencia desde el Frontend.
2. 📡 **Device & Behavioral Signals** — Consulta señales técnicas del dispositivo y comportamiento del usuario.
3. 🕸️ **GraphFraud Detector** — En paralelo, evalúa el riesgo de la cuenta destino mediante grafos de mulas.
4. ⚖️ **Risk Engine** — Consolida todas las señales en un `Risk Score` unificado.
5. 📋 **Decision Policy** — Aplica las reglas de decisión para determinar la acción.
6. 🔐 **HITL / Biometrics** — Si hay fricción, escala a step-up authentication o voice bot.
7. 💾 **MemoryWriter** — Registra el evento en el log de aprendizaje del agente.
8. 📤 **UI Response** — Retorna el resultado al simulador visual del Frontend.

---

## 🧩 Roles y Módulos

| Rol | Nombre | Módulo Backend | Responsabilidad |
|-----|--------|----------------|-----------------|
| 1 | Risk & Decision Engineer | `backend/risk_decision/` | Motor de riesgo, clasificador y política de decisión |
| 2 | Graph Fraud & Intelligence | `backend/graph_intelligence/` | Detección de redes de mulas y scoring de destinatario |
| 3 | Behavioral & Device Intel | `backend/behavioral_device/` | Fingerprinting, velocidad de tipeo, IP anómala |
| 4 | HITL & Trust Flow | `backend/hitl_trust/` | Step-up auth, voz bot y validación de identidad |
| 5 | UI Dashboard & Orchestrator | `frontend/` + `backend/main.py` | Frontend interactivo y orquestador central del agente |

---

## 💻 Stack Tecnológico

### Frontend
| Tecnología | Uso |
|------------|-----|
| **React** (Vite) | Framework UI principal |
| **JavaScript (ES6+)** | Lógica de componentes |
| **CSS Modules / Tailwind** | Estilos del dashboard |
| **Axios / Fetch API** | Comunicación con el backend |
| **D3.js** *(opcional)* | Visualización del grafo de mulas |

### Backend
| Tecnología | Uso |
|------------|-----|
| **Python 3.11+** | Lenguaje principal del backend |
| **FastAPI** | Framework para la API REST del orquestador |
| **Uvicorn** | Servidor ASGI para FastAPI |
| **Pydantic** | Validación de modelos de datos |
| **NetworkX** *(opcional)* | Procesamiento de grafos de fraude |

### Infraestructura & DevOps
| Tecnología | Uso |
|------------|-----|
| **Docker** | Contenerización del backend |
| **JSON** | Almacenamiento ligero del log del agente |

---

## 📁 Estructura de Carpetas

```
hackathon-antifraud-app/
│
├── frontend/                        # 🖥️ ROL 5 — Frontend, Demo & Orchestration
│   ├── public/                      # Archivos estáticos (favicon, index.html)
│   └── src/
│       ├── components/              # Simulador de transferencia y visualización del grafo
│       ├── dashboard/               # UI interactiva que muestra las señales activadas y el risk score
│       └── api_client.js            # Módulo central de conexión con el backend (Axios/Fetch)
│
├── backend/                         # ⚙️ Lógica central del agente
│   ├── main.py                      # Orquestador principal — punto de entrada de la API (FastAPI)
│   │
│   ├── risk_decision/               # 🧠 ROL 1 — Risk & Decision Engine
│   │   ├── classifier.py            # Clasifica el riesgo en: NO_FRAUD / POSSIBLE_FRAUD / FRAUD
│   │   └── rules.py                 # Reglas híbridas de clasificación y Decision Policy
│   │
│   ├── graph_intelligence/          # 🕸️ ROL 2 — Graph Fraud & Intelligence
│   │   └── mule_scorer.py           # Calcula el Mule Risk Score y detecta redes sospechosas
│   │
│   ├── behavioral_device/           # 📡 ROL 3 — Behavioral & Device Intelligence
│   │   └── telemetry.py             # Genera señales: device fingerprint, velocidad, anomalías de IP
│   │
│   └── hitl_trust/                  # 🔐 ROL 4 — HITL & Trust Flow
│       ├── verification.py          # Lógica de Step-up Authentication según nivel de riesgo
│       └── voice_bot.py             # Script y simulación de llamada automatizada de verificación
│
├── data/                            # 💾 Simulación de base de datos / persistencia ligera
│   └── learning_log.json            # Log de eventos para la memoria continua del agente
│
├── Dockerfile                       # Configuración de contenedor para el backend
└── requirements.txt                 # Dependencias Python del proyecto
```

### 📖 Descripción detallada de carpetas clave

| Carpeta / Archivo | Quién la usa | Qué hace |
|---|---|---|
| `frontend/src/components/` | Rol 5 | Componentes React del simulador de transferencia |
| `frontend/src/dashboard/` | Rol 5 | Dashboard que visualiza el resultado del agente |
| `frontend/src/api_client.js` | Rol 5 | Centraliza todas las llamadas HTTP al backend |
| `backend/main.py` | Rol 5 | Orquesta el pipeline completo, expone los endpoints |
| `backend/risk_decision/` | Rol 1 | Motor de riesgo y reglas de decisión final |
| `backend/graph_intelligence/` | Rol 2 | Detección de mulas y scoring de red |
| `backend/behavioral_device/` | Rol 3 | Señales de dispositivo y comportamiento del usuario |
| `backend/hitl_trust/` | Rol 4 | Autenticación reforzada y flujos de confianza |
| `data/learning_log.json` | Todos (escritura via Rol 1) | Memoria del agente para aprendizaje continuo |

---

## ⚡ Inicio Rápido

### Backend
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el servidor
uvicorn backend.main:app --reload --port 8000
```

### Frontend
```bash
# Desde la carpeta frontend/
cd frontend
npm install
npm run dev
```

### Con Docker
```bash
docker build -t antifraud-backend .
docker run -p 8000:8000 antifraud-backend
```

---

## 🤝 Guía de Colaboración en Equipo

- Cada **rol trabaja en su módulo exclusivo** sin modificar código ajeno.
- Toda comunicación entre módulos ocurre a través de **`backend/main.py`** (orquestador).
- Las interfaces entre módulos se definen como **funciones con parámetros claros y tipados** (usa `Pydantic` para los modelos de entrada/salida).
- Si necesitas datos de otro módulo, **habla con el responsable del rol** antes de modificar su código.
- El log `data/learning_log.json` es **solo de escritura** desde `backend/main.py`; no escribir directamente desde los módulos.

---

## 📄 Licencia

Proyecto desarrollado en el marco del Hackathon **SUNDAI LATAM · 22 de febrero de 2026**.
