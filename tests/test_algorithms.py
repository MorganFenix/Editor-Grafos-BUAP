import pytest
from fastapi.testclient import TestClient
from main import app, graph_instance
from backend.models.graph import Graph, AlgorithmStep
from backend.algorithms import kruskal, prim, dijkstra, floyd_warshall


@pytest.fixture
def sample_graph():
    """
    Creates a sample undirected weighted graph:
    Nodes: 0 (A), 1 (B), 2 (C), 3 (D)
    Edges:
      (0, 1) = 1
      (1, 2) = 2
      (0, 2) = 4  (forms cycle in Kruskal if 0-1 and 1-2 selected)
      (2, 3) = 1
    """
    g = Graph(is_directed=False, is_weighted=True)
    g.add_node()  # 0: A
    g.add_node()  # 1: B
    g.add_node()  # 2: C
    g.add_node()  # 3: D

    g.add_edge(0, 1, 1.0)
    g.add_edge(1, 2, 2.0)
    g.add_edge(0, 2, 4.0)
    g.add_edge(2, 3, 1.0)
    return g


class TestKruskalAlgorithm:
    def test_kruskal_empty_graph(self):
        g = Graph()
        steps = kruskal(g)
        assert len(steps) == 1
        assert "no contiene nodos" in steps[0].description

    def test_kruskal_execution(self, sample_graph):
        steps = sample_graph.kruskal()
        assert len(steps) > 0

        # Check initial step
        assert steps[0].step_number == 1
        assert "Kruskal" in steps[0].description

        # Check cycle detection flag
        cycle_steps = [s for s in steps if s.cycle_detected]
        assert len(cycle_steps) == 1
        assert cycle_steps[0].evaluated_edge == {"source": 0, "target": 2}
        assert "forma un ciclo" in cycle_steps[0].description

        # Final step MST edge count
        final_step = steps[-1]
        assert len(final_step.mst_edges) == 3  # (0,1), (2,3), (1,2)


class TestPrimAlgorithm:
    def test_prim_invalid_start_node(self, sample_graph):
        with pytest.raises(ValueError, match="no existe"):
            sample_graph.prim(99)

    def test_prim_execution(self, sample_graph):
        steps = sample_graph.prim(start_node=0)
        assert len(steps) > 0

        # Initial step
        assert steps[0].current_node == 0
        assert 0 in steps[0].visited_nodes

        # Check MST completion
        final_step = steps[-1]
        assert len(final_step.mst_edges) == 3
        assert set(final_step.visited_nodes) == {0, 1, 2, 3}


class TestDijkstraAlgorithm:
    def test_dijkstra_invalid_start_node(self, sample_graph):
        with pytest.raises(ValueError, match="no existe"):
            sample_graph.dijkstra(99)

    def test_dijkstra_distances(self, sample_graph):
        steps = sample_graph.dijkstra(start_node=0)
        assert len(steps) > 0

        final_step = steps[-1]
        distances = final_step.updated_distances
        assert distances[0] == 0.0
        assert distances[1] == 1.0
        assert distances[2] == 3.0  # via 0->1->2
        assert distances[3] == 4.0  # via 0->1->2->3


class TestFloydWarshallAlgorithm:
    def test_floyd_warshall_execution(self, sample_graph):
        steps = sample_graph.floyd_warshall()
        assert len(steps) > 0

        final_step = steps[-1]
        matrix = final_step.matrix_state

        # Distance from 0 to 3 should be 4.0
        assert matrix[0][3] == 4.0
        assert matrix[3][0] == 4.0
        assert matrix[0][0] == 0.0


class TestAPIEndpoints:
    client = TestClient(app)

    def test_kruskal_endpoint(self):
        # Reset global graph and setup
        graph_instance.nodes.clear()
        graph_instance.edges.clear()
        graph_instance.add_node()
        graph_instance.add_node()
        graph_instance.add_edge(0, 1, 5.0)

        response = self.client.get("/graph/algorithm/kruskal")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_prim_endpoint(self):
        response = self.client.get("/graph/algorithm/prim?start_node=0")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Invalid node
        err_response = self.client.get("/graph/algorithm/prim?start_node=99")
        assert err_response.status_code == 400

    def test_dijkstra_endpoint(self):
        response = self.client.get("/graph/algorithm/dijkstra?start_node=0")
        assert response.status_code == 200
        data = response.json()

        # Invalid node
        err_response = self.client.get("/graph/algorithm/dijkstra?start_node=99")
        assert err_response.status_code == 400

    def test_floyd_warshall_endpoint(self):
        response = self.client.get("/graph/algorithm/floyd-warshall")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
