from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from backend.models.graph import Graph, GraphState, Node, Edge, AlgorithmStep

app = FastAPI(
    title="API Editor de Grafos BUAP",
    description="Backend para la materia Estructuras de Datos y sus Aplicaciones",
    version="1.0.0"
)

# Permitir CORS para conexión fluida con el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancia global del grafo en memoria
graph_instance = Graph(is_directed=False, is_weighted=True)


class ConfigRequest(BaseModel):
    is_directed: bool
    is_weighted: bool


class NodeRequest(BaseModel):
    x: Optional[float] = 0.0
    y: Optional[float] = 0.0


class EdgeRequest(BaseModel):
    source: int
    target: int
    weight: Optional[float] = 1.0


class MatrixRequest(BaseModel):
    matrix: List[List[Optional[float]]]


@app.get("/graph", response_model=GraphState)
def get_graph():
    """Obtiene el estado actual del grafo (nodos y aristas)."""
    return graph_instance.export_state()


@app.post("/graph/config", response_model=GraphState)
def configure_graph(req: ConfigRequest):
    """Configura si el grafo es dirigido y/o ponderado."""
    graph_instance.is_directed = req.is_directed
    graph_instance.is_weighted = req.is_weighted
    return graph_instance.export_state()


@app.post("/graph/node", response_model=Node)
def add_node(req: NodeRequest):
    """Agrega un nuevo nodo respetando el límite de 20."""
    try:
        return graph_instance.add_node(x=req.x, y=req.y)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/graph/node/{node_id}")
def delete_node(node_id: int):
    """Elimina un nodo y sus aristas asociadas."""
    success = graph_instance.remove_node(node_id)
    if not success:
        raise HTTPException(status_code=404, detail="Nodo no encontrado.")
    return {"message": f"Nodo {node_id} eliminado exitosamente."}


@app.post("/graph/edge", response_model=Edge)
def add_edge(req: EdgeRequest):
    """Crea o modifica una arista con peso."""
    try:
        return graph_instance.add_edge(source=req.source, target=req.target, weight=req.weight)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/graph/edge")
def delete_edge(source: int, target: int):
    """Elimina una arista específica."""
    success = graph_instance.remove_edge(source, target)
    if not success:
        raise HTTPException(status_code=404, detail="Arista no encontrada.")
    return {"message": f"Arista entre {source} y {target} eliminada."}


@app.get("/graph/matrix")
def get_adjacency_matrix():
    """Exporta la matriz de adyacencia de 20x20."""
    return {"matrix": graph_instance.to_adjacency_matrix()}


@app.post("/graph/matrix")
def update_from_matrix(req: MatrixRequest):
    """Reconstruye el grafo desde la matriz de adyacencia (sincronización)."""
    try:
        graph_instance.from_adjacency_matrix(req.matrix)
        return {"message": "Grafo actualizado exitosamente desde la matriz.", "state": graph_instance.export_state()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/graph/algorithm/kruskal", response_model=List[AlgorithmStep])
def run_kruskal():
    """Ejecuta el algoritmo de Kruskal en el grafo actual."""
    return graph_instance.kruskal()


@app.get("/graph/algorithm/prim", response_model=List[AlgorithmStep])
def run_prim(start_node: int):
    """Ejecuta el algoritmo de Prim iniciando en start_node."""
    try:
        return graph_instance.prim(start_node)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/graph/algorithm/dijkstra", response_model=List[AlgorithmStep])
def run_dijkstra(start_node: int):
    """Ejecuta el algoritmo de Dijkstra iniciando en start_node."""
    try:
        return graph_instance.dijkstra(start_node)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/graph/algorithm/floyd-warshall", response_model=List[AlgorithmStep])
def run_floyd_warshall():
    """Ejecuta el algoritmo de Floyd-Warshall en el grafo actual."""
    return graph_instance.floyd_warshall()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    