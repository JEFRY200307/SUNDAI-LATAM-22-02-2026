"""
Backend principal — Orquestador del Agente Anti-Fraude
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Anti-Fraud Agent API",
    description="Orquestador del agente inteligente de deteccion de fraude — SUNDAI LATAM 2026",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/test-inline")
async def test_inline():
    return {"msg": "inline works"}


# Now try including routers one by one to find which one breaks
from backend.routes.health import router as health_router
app.include_router(health_router, tags=["Utilities"])

from backend.routes.graph import router as graph_router
app.include_router(graph_router, tags=["Graph"])

from backend.routes.modules import router as modules_router
app.include_router(modules_router, tags=["Modules"])

from backend.routes.analyze import router as analyze_router
app.include_router(analyze_router, tags=["Analyze"])
