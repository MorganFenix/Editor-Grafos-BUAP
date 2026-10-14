import math
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class Node(BaseModel):
    id: int
    label: str
    x: float = 0.0
    y: float = 0.0


class Edge(BaseModel):
    source: int
    target: int
    weight: float = 1.0


class AlgorithmStep(BaseModel):
    step_number: int
    description: str
    current_node: Optional[int] = None
    evaluated_edge: Optional[Dict[str, int]] = None  # {"source": u, "target": v}
    updated_distances: Optional[Dict[int, float]] = None
    mst_edges: List[Dict[str, int]] = Field(default_factory=list)
    visited_nodes: List[int] = Field(default_factory=list)
    cycle_detected: bool = False
    matrix_state: Optional[List[List[Optional[float]]]] = None


class GraphState(BaseModel):
    is_directed: bool = False
    is_weighted: bool = True
    max_nodes: int = 20
    nodes: List[Node] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)


class Graph:
    MAX_NODES = 20
    LABELS = [chr(65 + i) for i in range(20)]  # ['A', 'B', 'C', ..., 'T']

    def __init__(self, is_directed: bool = False, is_weighted: bool = True):
        self.is_directed = is_directed
        self.is_weighted = is_weighted
        self.nodes: Dict[int, Node] = {}
        self.edges: Dict[tuple, float] = {}  # (u, v) -> weight

    def add_node(self, x: float = 0.0, y: float = 0.0) -> Node:
        if len(self.nodes) >= self.MAX_NODES:
            raise ValueError(f"Límite alcanzado: no se pueden agregar más de {self.MAX_NODES} nodos.")
        
        # Encontrar el menor índice disponible de 0 a 19
        available_ids = set(range(self.MAX_NODES)) - set(self.nodes.keys())
        node_id = min(available_ids)
        label = self.LABELS[node_id]
        
        node = Node(id=node_id, label=label, x=x, y=y)
        self.nodes[node_id] = node
        return node

    def remove_node(self, node_id: int) -> bool:
        if node_id not in self.nodes:
            return False
        
        del self.nodes[node_id]
        # Eliminar todas las aristas conectadas al nodo
        keys_to_delete = [k for k in self.edges.keys() if k[0] == node_id or k[1] == node_id]
        for k in keys_to_delete:
            del self.edges[k]
        return True

    def add_edge(self, source: int, target: int, weight: float = 1.0) -> Edge:
        if source not in self.nodes or target not in self.nodes:
            raise ValueError("Los nodos origen y destino deben existir en el grafo.")
        
        final_weight = weight if self.is_weighted else 1.0
        self.edges[(source, target)] = final_weight
        
        if not self.is_directed and source != target:
            self.edges[(target, source)] = final_weight
            
        return Edge(source=source, target=target, weight=final_weight)

    def remove_edge(self, source: int, target: int) -> bool:
        removed = False
        if (source, target) in self.edges:
            del self.edges[(source, target)]
            removed = True
        if not self.is_directed and (target, source) in self.edges:
            del self.edges[(target, source)]
            removed = True
        return removed

    def to_adjacency_matrix(self) -> List[List[Optional[float]]]:
        """
        Exporta una matriz fija de 20x20.
        Si la conexión no existe, el valor es None (representando infinito/sin arista).
        La diagonal principal contiene 0.0 para nodos existentes.
        """
        matrix: List[List[Optional[float]]] = [[None for _ in range(self.MAX_NODES)] for _ in range(self.MAX_NODES)]
        
        for i in range(self.MAX_NODES):
            if i in self.nodes:
                matrix[i][i] = 0.0
                
        for (u, v), w in self.edges.items():
            if u in self.nodes and v in self.nodes:
                matrix[u][v] = w
                
        return matrix

    def from_adjacency_matrix(self, matrix: List[List[Optional[float]]]) -> None:
        """
        Reconstruye la topología del grafo a partir de una matriz de 20x20.
        """
        if len(matrix) != self.MAX_NODES or any(len(row) != self.MAX_NODES for row in matrix):
            raise ValueError("La matriz debe ser estrictamente de dimensión 20x20.")

        self.nodes.clear()
        self.edges.clear()

        # Identificar nodos presentes (filas donde la diagonal no es None o hay conexiones)
        active_nodes = set()
        for i in range(self.MAX_NODES):
            if matrix[i][i] == 0.0 or any(matrix[i][j] is not None for j in range(self.MAX_NODES)):
                active_nodes.add(i)

        for node_id in sorted(active_nodes):
            self.nodes[node_id] = Node(id=node_id, label=self.LABELS[node_id])

        # Reconstruir aristas
        for i in active_nodes:
            for j in active_nodes:
                val = matrix[i][j]
                if val is not None and i != j:
                    if self.is_directed:
                        self.edges[(i, j)] = float(val) if self.is_weighted else 1.0
                    else:
                        if i <= j:
                            w = float(val) if self.is_weighted else 1.0
                            self.edges[(i, j)] = w
                            self.edges[(j, i)] = w

    def export_state(self) -> GraphState:
        edge_list = []
        visited_pairs = set()
        
        for (u, v), w in self.edges.items():
            if not self.is_directed:
                pair = tuple(sorted([u, v]))
                if pair in visited_pairs:
                    continue
                visited_pairs.add(pair)
            edge_list.append(Edge(source=u, target=v, weight=w))
            
        return GraphState(
            is_directed=self.is_directed,
            is_weighted=self.is_weighted,
            max_nodes=self.MAX_NODES,
            nodes=list(self.nodes.values()),
            edges=edge_list
        )
        