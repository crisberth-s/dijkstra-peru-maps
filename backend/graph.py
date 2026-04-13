# backend/graph.py
# Capa de orquestación: combina osm_loader + dijkstra + path_builder.
# Aquí también se gestiona el caché de grafos en memoria.

import math
from backend.osm_loader import load_graph_between, nearest_node
from backend.dijkstra import dijkstra
from backend.path_builder import build_route_coordinates

# Caché en memoria: evita re-descargar el grafo para rutas similares
_graph_cache = {}


def _cache_key(olat, olon, dlat, dlon):
    """Clave de caché redondeada a 1 decimal (~10 km de tolerancia)."""
    return (round(olat, 1), round(olon, 1), round(dlat, 1), round(dlon, 1))


def calculate_route(origin_lat, origin_lon, dest_lat, dest_lon):
    """
    Punto de entrada principal.
    Retorna un dict con:
        {
          "success": True/False,
          "coordinates": [[lat, lon], ...],   # ruta completa
          "distance_km": float,
          "nodes_count": int,
          "error": "mensaje de error si aplica"
        }
    """
    try:
        key = _cache_key(origin_lat, origin_lon, dest_lat, dest_lon)

        if key in _graph_cache:
            print("[Graph] Usando grafo en caché")
            G = _graph_cache[key]
        else:
            print("[Graph] Descargando grafo nuevo...")
            G = load_graph_between(origin_lat, origin_lon, dest_lat, dest_lon)
            _graph_cache[key] = G

        # Nodos más cercanos al origen y destino
        origin_node = nearest_node(G, origin_lat, origin_lon)
        dest_node   = nearest_node(G, dest_lat, dest_lon)

        print(f"[Graph] Nodo origen: {origin_node} | Nodo destino: {dest_node}")

        # Ejecutar Dijkstra manual
        print("[Dijkstra] Calculando ruta...")
        total_dist, node_path = dijkstra(G, origin_node, dest_node)

        if not node_path or math.isinf(total_dist):
            return {
                "success": False,
                "error": "No se encontró ruta entre los puntos seleccionados.",
                "coordinates": [],
                "distance_km": 0,
                "nodes_count": 0,
            }

        print(f"[Dijkstra] Ruta encontrada: {len(node_path)} nodos, {total_dist/1000:.1f} km")

        # Construir coordenadas reales con geometría de calles
        coordinates = build_route_coordinates(G, node_path)

        return {
            "success": True,
            "coordinates": coordinates,
            "distance_km": round(total_dist / 1000, 2),
            "nodes_count": len(node_path),
            "error": None,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "coordinates": [],
            "distance_km": 0,
            "nodes_count": 0,
        }
