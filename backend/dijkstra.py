# backend/dijkstra.py
# Implementación MANUAL de Dijkstra con heapq sobre el grafo OSMnx.
# NO usa networkx.shortest_path ni ningún método de NetworkX para el cálculo.

import heapq
import math


def dijkstra(G, source, target):
    """
    Algoritmo de Dijkstra manual.

    Parámetros:
        G       : grafo MultiDiGraph de OSMnx
        source  : nodo de origen (int)
        target  : nodo de destino (int)

    Retorna:
        (distancia_total_metros, lista_de_nodos_en_orden)
        o (inf, []) si no hay ruta posible.
    """

    # dist[node] = distancia mínima conocida desde source
    dist = {source: 0.0}

    # prev[node] = nodo anterior en la ruta óptima
    prev = {}

    # Heap: (costo_acumulado, nodo)
    heap = [(0.0, source)]

    # Nodos ya procesados definitivamente
    visited = set()

    while heap:
        cost, u = heapq.heappop(heap)

        if u in visited:
            continue
        visited.add(u)

        # Llegamos al destino — reconstruir ruta
        if u == target:
            return cost, _reconstruct_path(prev, source, target)

        # Explorar vecinos
        if u not in G:
            continue

        for v, edge_data_dict in G[u].items():
            if v in visited:
                continue

            # OSMnx puede tener múltiples aristas entre u-v (MultiDiGraph)
            # Tomamos la de menor longitud
            edge_length = _min_edge_length(edge_data_dict)

            new_cost = cost + edge_length

            if new_cost < dist.get(v, math.inf):
                dist[v] = new_cost
                prev[v] = u
                heapq.heappush(heap, (new_cost, v))

    # No se encontró ruta
    return math.inf, []


def _min_edge_length(edge_data_dict):
    """
    Dado el dict de aristas paralelas {0: {data}, 1: {data}, ...},
    devuelve la longitud mínima en metros.
    """
    min_len = math.inf
    for key, data in edge_data_dict.items():
        length = data.get("length", math.inf)
        if isinstance(length, (int, float)) and length < min_len:
            min_len = length
    return min_len if min_len != math.inf else 1.0  # fallback 1m


def _reconstruct_path(prev, source, target):
    """Reconstruye la lista de nodos desde target hasta source usando prev."""
    path = []
    node = target
    while node != source:
        path.append(node)
        if node not in prev:
            return []  # ruta rota
        node = prev[node]
    path.append(source)
    path.reverse()
    return path
