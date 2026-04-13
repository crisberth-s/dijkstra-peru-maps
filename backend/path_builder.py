# backend/path_builder.py
# Convierte la lista de nodos de Dijkstra en coordenadas [lat, lon] reales,
# usando la geometría real de las calles cuando está disponible en OSMnx.

from shapely.geometry import LineString


def build_route_coordinates(G, node_list):
    """
    Dado el grafo G y la lista de nodos del camino Dijkstra,
    devuelve una lista de [lat, lon] siguiendo la geometría real de las calles.

    Si una arista tiene atributo 'geometry' (LineString de Shapely),
    se usan esos puntos intermedios reales.
    Si no, se usa interpolación directa entre nodos.
    """
    if not node_list:
        return []

    coords = []

    for i in range(len(node_list) - 1):
        u = node_list[i]
        v = node_list[i + 1]

        # Obtener datos del nodo u para el punto de inicio
        if i == 0:
            u_data = G.nodes[u]
            coords.append([u_data["y"], u_data["x"]])  # lat=y, lon=x en OSMnx

        # Buscar la arista u→v con menor longitud
        edge_geom = _get_edge_geometry(G, u, v)

        if edge_geom is not None:
            # Usar puntos intermedios reales de la geometría
            edge_coords = list(edge_geom.coords)
            # edge_geom va de u a v en coordenadas (lon, lat)
            # Saltamos el primer punto (ya fue añadido como nodo u)
            for lon, lat in edge_coords[1:]:
                coords.append([lat, lon])
        else:
            # Sin geometría: línea recta al nodo siguiente
            v_data = G.nodes[v]
            coords.append([v_data["y"], v_data["x"]])

    return coords


def _get_edge_geometry(G, u, v):
    """
    Retorna el objeto LineString de la arista u→v con menor longitud,
    o None si no existe geometría.
    """
    if u not in G or v not in G[u]:
        return None

    best_geom = None
    best_len = float("inf")

    for key, data in G[u][v].items():
        length = data.get("length", float("inf"))
        geom = data.get("geometry", None)
        if length < best_len:
            best_len = length
            best_geom = geom

    return best_geom  # puede ser None si el edge no tiene geometría guardada
