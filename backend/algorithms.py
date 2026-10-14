from typing import List, Dict, Optional, Set
import copy
from backend.models.graph import Graph, AlgorithmStep


def _format_weight(w: float) -> str:
    """Helper to format weight cleanly (e.g. 5 instead of 5.0 if integer)."""
    if w.is_integer():
        return str(int(w))
    return f"{w:.2f}"


def kruskal(graph: Graph) -> List[AlgorithmStep]:
    """
    Computes Minimum Spanning Tree step-by-step using Kruskal's algorithm.
    Flags selected edges and cycle-forming rejected edges.
    """
    steps: List[AlgorithmStep] = []
    step_count = 1

    if not graph.nodes:
        steps.append(
            AlgorithmStep(
                step_number=step_count,
                description="El grafo no contiene nodos."
            )
        )
        return steps

    # Collect unique edges
    unique_edges = []
    if not graph.is_directed:
        seen = set()
        for (u, v), w in graph.edges.items():
            if u in graph.nodes and v in graph.nodes:
                pair = (min(u, v), max(u, v))
                if pair not in seen:
                    seen.add(pair)
                    unique_edges.append((pair[0], pair[1], w))
    else:
        for (u, v), w in graph.edges.items():
            if u in graph.nodes and v in graph.nodes:
                unique_edges.append((u, v, w))

    # Sort edges by weight, then source, then target
    unique_edges.sort(key=lambda x: (x[2], x[0], x[1]))

    # Union-Find data structures
    parent = {node_id: node_id for node_id in graph.nodes}
    rank = {node_id: 0 for node_id in graph.nodes}

    def find(i: int) -> int:
        if parent[i] == i:
            return i
        parent[i] = find(parent[i])
        return parent[i]

    def union(i: int, j: int) -> None:
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            if rank[root_i] < rank[root_j]:
                root_i, root_j = root_j, root_i
            parent[root_j] = root_i
            if rank[root_i] == rank[root_j]:
                rank[root_i] += 1

    visited_nodes = sorted(list(graph.nodes.keys()))
    mst_edges: List[Dict[str, int]] = []

    # Initial Step
    steps.append(
        AlgorithmStep(
            step_number=step_count,
            description="Inicio del algoritmo de Kruskal. Aristas ordenadas por peso.",
            visited_nodes=list(visited_nodes),
            mst_edges=list(mst_edges)
        )
    )

    for u, v, w in unique_edges:
        step_count += 1
        root_u = find(u)
        root_v = find(v)
        label_u = graph.nodes[u].label
        label_v = graph.nodes[v].label
        eval_edge = {"source": u, "target": v}
        w_str = _format_weight(w)

        if root_u == root_v:
            # Cycle detected
            steps.append(
                AlgorithmStep(
                    step_number=step_count,
                    description=f"Arista ({label_u}, {label_v}) con peso {w_str} forma un ciclo. Rechazada.",
                    evaluated_edge=eval_edge,
                    visited_nodes=list(visited_nodes),
                    mst_edges=list(mst_edges),
                    cycle_detected=True
                )
            )
        else:
            union(u, v)
            mst_edges.append(eval_edge)
            steps.append(
                AlgorithmStep(
                    step_number=step_count,
                    description=f"Arista ({label_u}, {label_v}) con peso {w_str} seleccionada para el MST.",
                    evaluated_edge=eval_edge,
                    visited_nodes=list(visited_nodes),
                    mst_edges=list(mst_edges),
                    cycle_detected=False
                )
            )

    step_count += 1
    steps.append(
        AlgorithmStep(
            step_number=step_count,
            description=f"Algoritmo de Kruskal finalizado. MST contiene {len(mst_edges)} aristas.",
            visited_nodes=list(visited_nodes),
            mst_edges=list(mst_edges)
        )
    )

    return steps


def prim(graph: Graph, start_node: int) -> List[AlgorithmStep]:
    """
    Computes Minimum Spanning Tree step-by-step starting from start_node using Prim's algorithm.
    """
    if start_node not in graph.nodes:
        raise ValueError(f"El nodo inicial {start_node} no existe en el grafo.")

    steps: List[AlgorithmStep] = []
    step_count = 1

    visited: Set[int] = {start_node}
    visited_nodes: List[int] = [start_node]
    mst_edges: List[Dict[str, int]] = []

    label_start = graph.nodes[start_node].label

    # Initial step
    steps.append(
        AlgorithmStep(
            step_number=step_count,
            description=f"Inicio del algoritmo de Prim desde el nodo {label_start}.",
            current_node=start_node,
            visited_nodes=list(visited_nodes),
            mst_edges=list(mst_edges)
        )
    )

    while len(visited) < len(graph.nodes):
        # Find candidate edges crossing from visited to unvisited nodes
        candidates = []
        for u in visited:
            for v in graph.nodes:
                if v not in visited:
                    if (u, v) in graph.edges:
                        w = graph.edges[(u, v)]
                        candidates.append((u, v, w))

        if not candidates:
            step_count += 1
            steps.append(
                AlgorithmStep(
                    step_number=step_count,
                    description="No hay más aristas disponibles para conectar nodos restantes (grafo no conexo).",
                    visited_nodes=list(visited_nodes),
                    mst_edges=list(mst_edges)
                )
            )
            break

        # Pick candidate with minimum weight
        candidates.sort(key=lambda x: (x[2], x[0], x[1]))
        best_u, best_v, best_w = candidates[0]

        visited.add(best_v)
        visited_nodes.append(best_v)
        eval_edge = {"source": best_u, "target": best_v}
        mst_edges.append(eval_edge)

        label_u = graph.nodes[best_u].label
        label_v = graph.nodes[best_v].label
        w_str = _format_weight(best_w)

        step_count += 1
        steps.append(
            AlgorithmStep(
                step_number=step_count,
                description=f"Arista ({label_u}, {label_v}) con peso {w_str} seleccionada. Nodo {label_v} añadido al MST.",
                current_node=best_v,
                evaluated_edge=eval_edge,
                visited_nodes=list(visited_nodes),
                mst_edges=list(mst_edges)
            )
        )

    step_count += 1
    steps.append(
        AlgorithmStep(
            step_number=step_count,
            description=f"Algoritmo de Prim finalizado. MST contiene {len(mst_edges)} aristas.",
            visited_nodes=list(visited_nodes),
            mst_edges=list(mst_edges)
        )
    )

    return steps


def dijkstra(graph: Graph, start_node: int) -> List[AlgorithmStep]:
    """
    Computes shortest paths from start_node using Dijkstra's algorithm.
    Logs current node, cumulative distances, visited nodes, and path steps.
    """
    if start_node not in graph.nodes:
        raise ValueError(f"El nodo inicial {start_node} no existe en el grafo.")

    steps: List[AlgorithmStep] = []
    step_count = 1

    distances: Dict[int, float] = {node_id: float('inf') for node_id in graph.nodes}
    distances[start_node] = 0.0

    visited_nodes: List[int] = []
    unvisited = set(graph.nodes.keys())

    label_start = graph.nodes[start_node].label

    # Initial Step
    steps.append(
        AlgorithmStep(
            step_number=step_count,
            description=f"Inicio del algoritmo de Dijkstra desde el nodo {label_start}.",
            current_node=start_node,
            updated_distances=dict(distances),
            visited_nodes=list(visited_nodes)
        )
    )

    while unvisited:
        # Find unvisited node with smallest distance
        curr = min(unvisited, key=lambda node: distances[node])

        if distances[curr] == float('inf'):
            # Remaining nodes are unreachable
            break

        unvisited.remove(curr)
        visited_nodes.append(curr)

        label_curr = graph.nodes[curr].label
        curr_dist_str = _format_weight(distances[curr])

        step_count += 1
        steps.append(
            AlgorithmStep(
                step_number=step_count,
                description=f"Procesando nodo {label_curr} con distancia acumulada {curr_dist_str}.",
                current_node=curr,
                updated_distances=dict(distances),
                visited_nodes=list(visited_nodes)
            )
        )

        # Check neighbors
        for v in sorted(graph.nodes.keys()):
            if (curr, v) in graph.edges:
                weight = graph.edges[(curr, v)]
                eval_edge = {"source": curr, "target": v}
                new_dist = distances[curr] + weight
                label_v = graph.nodes[v].label
                w_str = _format_weight(weight)

                step_count += 1
                if new_dist < distances[v]:
                    old_dist = distances[v]
                    old_dist_str = "∞" if old_dist == float('inf') else _format_weight(old_dist)
                    new_dist_str = _format_weight(new_dist)
                    distances[v] = new_dist

                    steps.append(
                        AlgorithmStep(
                            step_number=step_count,
                            description=f"Actualizando distancia al nodo {label_v}: {old_dist_str} -> {new_dist_str} vía ({label_curr}, {label_v}) [peso {w_str}].",
                            current_node=curr,
                            evaluated_edge=eval_edge,
                            updated_distances=dict(distances),
                            visited_nodes=list(visited_nodes)
                        )
                    )
                else:
                    curr_v_dist_str = _format_weight(distances[v])
                    new_dist_str = _format_weight(new_dist)
                    steps.append(
                        AlgorithmStep(
                            step_number=step_count,
                            description=f"Evaluando arista ({label_curr}, {label_v}): no mejora la distancia a {label_v} ({curr_v_dist_str} <= {new_dist_str}).",
                            current_node=curr,
                            evaluated_edge=eval_edge,
                            updated_distances=dict(distances),
                            visited_nodes=list(visited_nodes)
                        )
                    )

    step_count += 1
    steps.append(
        AlgorithmStep(
            step_number=step_count,
            description="Algoritmo de Dijkstra finalizado.",
            updated_distances=dict(distances),
            visited_nodes=list(visited_nodes)
        )
    )

    return steps


def floyd_warshall(graph: Graph) -> List[AlgorithmStep]:
    """
    Computes all-pairs shortest paths using Floyd-Warshall algorithm.
    Logs matrix distance updates as each intermediate node 'k' is evaluated.
    """
    steps: List[AlgorithmStep] = []
    step_count = 1

    dist_matrix = graph.to_adjacency_matrix()
    active_nodes = sorted(list(graph.nodes.keys()))

    # Initial Step
    steps.append(
        AlgorithmStep(
            step_number=step_count,
            description="Inicio del algoritmo de Floyd-Warshall. Matriz de adyacencia inicializada.",
            matrix_state=[row[:] for row in dist_matrix]
        )
    )

    for k in active_nodes:
        label_k = graph.nodes[k].label
        step_count += 1
        steps.append(
            AlgorithmStep(
                step_number=step_count,
                description=f"Evaluando nodo intermedio k = {label_k} (nodo {k}).",
                current_node=k,
                matrix_state=[row[:] for row in dist_matrix]
            )
        )

        for i in active_nodes:
            for j in active_nodes:
                if i != j and dist_matrix[i][k] is not None and dist_matrix[k][j] is not None:
                    candidate = dist_matrix[i][k] + dist_matrix[k][j]
                    current = dist_matrix[i][j]

                    if current is None or candidate < current:
                        dist_matrix[i][j] = candidate
                        label_i = graph.nodes[i].label
                        label_j = graph.nodes[j].label
                        old_str = "∞" if current is None else _format_weight(current)
                        cand_str = _format_weight(candidate)

                        step_count += 1
                        steps.append(
                            AlgorithmStep(
                                step_number=step_count,
                                description=f"Ruta más corta entre {label_i} y {label_j} actualizada vía {label_k}: distancia {old_str} -> {cand_str}.",
                                current_node=k,
                                evaluated_edge={"source": i, "target": j},
                                matrix_state=[row[:] for row in dist_matrix]
                            )
                        )

    step_count += 1
    steps.append(
        AlgorithmStep(
            step_number=step_count,
            description="Algoritmo de Floyd-Warshall finalizado.",
            matrix_state=[row[:] for row in dist_matrix]
        )
    )

    return steps
