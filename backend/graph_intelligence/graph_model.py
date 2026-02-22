"""
ROL 2 — Graph Model
Grafo dirigido (DiGraph) de transacciones.
Singleton en memoria: se crea una vez, crece con cada transacción.
Aristas agregadas (count + last_timestamp) en vez de multi-aristas.
"""
import time
import networkx as nx

# ─── Singleton del grafo ──────────────────────────────────────────────────────
_GRAPH: nx.DiGraph | None = None


def get_transaction_graph() -> nx.DiGraph:
    """
    Retorna el grafo singleton. Si no existe, lo inicializa con datos de demo.
    El mismo objeto se reutiliza en todas las llamadas (persistencia en memoria).
    """
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = _build_demo_graph()
    return _GRAPH


def add_transaction(
    graph: nx.DiGraph,
    sender: str,
    receiver: str,
    amount: float,
) -> None:
    """
    Agrega una transacción al grafo en vivo.
    Si la arista ya existe, incrementa count y actualiza last_timestamp y total_amount.
    Si no existe, la crea.
    """
    now = time.time()

    # Asegurar que los nodos existan
    if not graph.has_node(sender):
        graph.add_node(sender, type="user", label=sender)
    if not graph.has_node(receiver):
        graph.add_node(receiver, type="user", label=receiver)

    # Arista agregada: count + total_amount + last_timestamp
    if graph.has_edge(sender, receiver):
        edge = graph[sender][receiver]
        edge["count"] = edge.get("count", 1) + 1
        edge["total_amount"] = edge.get("total_amount", 0) + amount
        edge["last_timestamp"] = now
    else:
        graph.add_edge(
            sender,
            receiver,
            count=1,
            total_amount=amount,
            last_timestamp=now,
        )


# ─── Grafo de demo precargado ────────────────────────────────────────────────

def _build_demo_graph() -> nx.DiGraph:
    """
    Crea un grafo con ~12 cuentas simulando:
    - Cuentas normales con transferencias legítimas
    - Red de mulas en cascada: MULE-001 → 002 → 003 → 004
    - Cuentas blacklisted con alta recepción
    """
    G = nx.DiGraph()
    now = time.time()

    # ── Cuentas normales ──────────────────────────────────────────────────
    normal_accounts = [
        "ACC-NORMAL-001", "ACC-NORMAL-002", "ACC-NORMAL-003",
        "ACC-NORMAL-004", "ACC-NORMAL-005",
    ]
    for acc in normal_accounts:
        G.add_node(acc, type="user", label=acc)

    # Transferencias legítimas (pocas, baja frecuencia)
    _add_demo_edge(G, "ACC-NORMAL-001", "ACC-NORMAL-002", 200, 1, now - 86400)
    _add_demo_edge(G, "ACC-NORMAL-002", "ACC-NORMAL-003", 150, 1, now - 72000)
    _add_demo_edge(G, "ACC-NORMAL-004", "ACC-NORMAL-005", 300, 2, now - 48000)
    _add_demo_edge(G, "ACC-NORMAL-001", "ACC-NORMAL-005", 100, 1, now - 36000)

    # ── Red de mulas (cascada) ────────────────────────────────────────────
    mule_accounts = ["ACC-MULE-001", "ACC-MULE-002", "ACC-MULE-003", "ACC-MULE-004"]
    for acc in mule_accounts:
        G.add_node(acc, type="mule", label=acc)

    # Cascada: 001 → 002 → 003 → 004 (transferencias rápidas)
    _add_demo_edge(G, "ACC-MULE-001", "ACC-MULE-002", 5000, 3, now - 7200)
    _add_demo_edge(G, "ACC-MULE-002", "ACC-MULE-003", 4800, 3, now - 3600)
    _add_demo_edge(G, "ACC-MULE-003", "ACC-MULE-004", 4500, 2, now - 1800)

    # Muchas cuentas normales envían a MULE-001 (alta recepción)
    _add_demo_edge(G, "ACC-NORMAL-001", "ACC-MULE-001", 1000, 2, now - 14400)
    _add_demo_edge(G, "ACC-NORMAL-002", "ACC-MULE-001", 800, 3, now - 10800)
    _add_demo_edge(G, "ACC-NORMAL-003", "ACC-MULE-001", 1200, 1, now - 7200)
    _add_demo_edge(G, "ACC-NORMAL-004", "ACC-MULE-001", 600, 2, now - 5400)
    _add_demo_edge(G, "ACC-NORMAL-005", "ACC-MULE-001", 900, 1, now - 3600)

    # ── Cuentas blacklisted ───────────────────────────────────────────────
    G.add_node("ACC-BLOCKED-001", type="blocked", label="ACC-BLOCKED-001")
    G.add_node("ACC-BLOCKED-002", type="blocked", label="ACC-BLOCKED-002")

    _add_demo_edge(G, "ACC-MULE-004", "ACC-BLOCKED-001", 4000, 2, now - 900)
    _add_demo_edge(G, "ACC-NORMAL-003", "ACC-BLOCKED-002", 500, 1, now - 1800)

    # ── Cuenta sender de demo ─────────────────────────────────────────────
    G.add_node("ACC-SENDER-001", type="user", label="ACC-SENDER-001")
    _add_demo_edge(G, "ACC-SENDER-001", "ACC-NORMAL-001", 250, 1, now - 100000)

    return G


def _add_demo_edge(
    G: nx.DiGraph,
    src: str,
    dst: str,
    total_amount: float,
    count: int,
    last_timestamp: float,
) -> None:
    """Helper para agregar aristas de demo con atributos agregados."""
    G.add_edge(
        src, dst,
        count=count,
        total_amount=total_amount,
        last_timestamp=last_timestamp,
    )
