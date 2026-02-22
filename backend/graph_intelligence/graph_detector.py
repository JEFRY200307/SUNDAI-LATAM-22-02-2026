"""
ROL 2 — GraphFraudDetector
Analiza el grafo de transacciones para detectar:
  - Alta centralidad (in-degree como señal primaria)
  - Transferencias en cascada (por estructura)
  - Alta frecuencia de recepción-envío
Genera métricas + reasons para MuleScore y explainability.
"""
import networkx as nx

# ─── Pesos para MuleScore ─────────────────────────────────────────────────────
DETECTOR_WEIGHTS: dict[str, float] = {
    "centrality":  0.35,
    "cascade":     0.35,
    "frequency":   0.30,
}

# ─── Umbrales ─────────────────────────────────────────────────────────────────
IN_DEGREE_HIGH = 5       # in-degree ≥ 5 → alta frecuencia de recepción
CASCADE_MIN_DEPTH = 2    # mínimo 2 hops para considerar cascada


class GraphFraudDetector:
    """Analiza un grafo de transacciones para detectar patrones de mulas."""

    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
        # Precalcular centralidad una vez por análisis
        self._centrality = nx.degree_centrality(graph) if len(graph) > 0 else {}

    def analyze(self, account: str) -> dict:
        """
        Analiza una cuenta y retorna métricas de riesgo + reasons.

        Returns:
            dict con mule_score, graph_metrics, reasons.
        """
        if account not in self.graph:
            return self._empty_result(account)

        # ── Métricas individuales ─────────────────────────────────────────
        centrality = self._centrality.get(account, 0.0)
        in_deg = self.graph.in_degree(account)
        out_deg = self.graph.out_degree(account)
        cascade_depth = self._detect_cascade_depth(account)
        in_cascade = cascade_depth >= CASCADE_MIN_DEPTH
        node_type = self.graph.nodes[account].get("type", "user")

        # ── Blacklist directa ─────────────────────────────────────────────
        if node_type == "blocked":
            return {
                "receiver_account": account,
                "mule_score": 1.0,
                "reasons": ["blacklisted_account"],
                "graph_metrics": {
                    "centrality": round(centrality, 4),
                    "in_degree": in_deg,
                    "out_degree": out_deg,
                    "cascade_depth": cascade_depth,
                    "node_type": node_type,
                },
            }

        # ── Calcular score por señales ────────────────────────────────────
        score = 0.0
        reasons: list[str] = []

        # Señal 1: centralidad (normalizada por umbral dinámico)
        if len(self._centrality) > 1:
            avg_c = sum(self._centrality.values()) / len(self._centrality)
            if centrality > avg_c * 2:
                score += DETECTOR_WEIGHTS["centrality"]
                reasons.append("high_centrality")
            elif centrality > avg_c * 1.5:
                score += DETECTOR_WEIGHTS["centrality"] * 0.5
                reasons.append("moderate_centrality")

        # Señal 2: in-degree alto (señal primaria, más estable)
        if in_deg >= IN_DEGREE_HIGH:
            score += DETECTOR_WEIGHTS["frequency"]
            reasons.append("high_in_degree")
        elif in_deg >= 3:
            score += DETECTOR_WEIGHTS["frequency"] * 0.5
            reasons.append("moderate_in_degree")

        # Señal 3: cascada por estructura
        if in_cascade:
            score += DETECTOR_WEIGHTS["cascade"]
            reasons.append("cascade_member")

        # Señal 4: tipo mula conocido
        if node_type == "mule":
            score += 0.15
            reasons.append("known_mule_type")

        return {
            "receiver_account": account,
            "mule_score": min(score, 1.0),
            "reasons": reasons,
            "graph_metrics": {
                "centrality": round(centrality, 4),
                "in_degree": in_deg,
                "out_degree": out_deg,
                "cascade_depth": cascade_depth,
                "node_type": node_type,
            },
        }

    # ─── Detección de cascada por estructura ──────────────────────────────

    def _detect_cascade_depth(self, account: str, max_depth: int = 5) -> int:
        """
        Busca la cadena más larga hacia atrás (predecessors) o adelante
        (successors) que pasa por esta cuenta.
        Retorna la profundidad máxima de la cadena.
        """
        backward = self._chain_length(account, direction="backward", max_depth=max_depth)
        forward = self._chain_length(account, direction="forward", max_depth=max_depth)
        return backward + forward  # profundidad total de la cadena

    def _chain_length(
        self, account: str, direction: str, max_depth: int, visited: set | None = None
    ) -> int:
        """Recorre la cadena en una dirección contando hops."""
        if visited is None:
            visited = {account}

        neighbors = (
            list(self.graph.predecessors(account))
            if direction == "backward"
            else list(self.graph.successors(account))
        )

        best = 0
        for neighbor in neighbors:
            if neighbor not in visited and len(visited) < max_depth:
                visited.add(neighbor)
                length = 1 + self._chain_length(neighbor, direction, max_depth, visited)
                best = max(best, length)

        return best

    # ─── Helper ───────────────────────────────────────────────────────────

    @staticmethod
    def _empty_result(account: str) -> dict:
        return {
            "receiver_account": account,
            "mule_score": 0.0,
            "reasons": [],
            "graph_metrics": {
                "centrality": 0.0,
                "in_degree": 0,
                "out_degree": 0,
                "cascade_depth": 0,
                "node_type": "unknown",
            },
        }
