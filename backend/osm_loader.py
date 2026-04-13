# backend/osm_loader.py
# Sistema de caché por TILES fijos — reutiliza grafos entre rutas distintas.
# El país se divide en celdas de ~50x50 km. Cualquier ruta que pase por
# la misma celda reutiliza el mismo archivo .pkl sin re-descargar nada.

import os
import pickle
import math
import osmnx as ox
from config import GRAPH_NETWORK_TYPE, CACHE_ENABLED

ox.settings.use_cache = CACHE_ENABLED
ox.settings.log_console = False

# Tamaño de cada tile en grados (~0.5° ≈ 55 km)
TILE_SIZE = 0.5

_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "cache_graphs"
)
os.makedirs(_CACHE_DIR, exist_ok=True)

# Caché en memoria para la sesión actual (evita leer pickle repetidamente)
_memory_cache = {}


def _tile_id(lat, lon):
    """Convierte lat/lon al tile fijo que lo contiene."""
    tile_lat = math.floor(lat / TILE_SIZE) * TILE_SIZE
    tile_lon = math.floor(lon / TILE_SIZE) * TILE_SIZE
    return tile_lat, tile_lon


def _tiles_for_bbox(south, west, north, east):
    """Devuelve todos los tile_ids que cubren el bbox dado."""
    tiles = set()
    lat = math.floor(south / TILE_SIZE) * TILE_SIZE
    while lat < north:
        lon = math.floor(west / TILE_SIZE) * TILE_SIZE
        while lon < east:
            tiles.add((round(lat, 6), round(lon, 6)))
            lon += TILE_SIZE
        lat += TILE_SIZE
    return tiles


def _tile_cache_path(tile_lat, tile_lon):
    name = f"tile_{tile_lat:+.1f}_{tile_lon:+.1f}.pkl"
    return os.path.join(_CACHE_DIR, name)


def _load_tile(tile_lat, tile_lon):
    """Carga un tile desde memoria > disco > descarga OSM."""
    key = (tile_lat, tile_lon)

    # 1. Caché en memoria (instantáneo)
    if key in _memory_cache:
        print(f"[Cache] ✓ Tile {key} desde memoria")
        return _memory_cache[key]

    # 2. Caché en disco (rápido, <1 seg)
    path = _tile_cache_path(tile_lat, tile_lon)
    if CACHE_ENABLED and os.path.exists(path):
        size_mb = os.path.getsize(path) / 1024 / 1024
        print(f"[Cache] ✓ Tile {key} desde disco ({size_mb:.1f} MB)")
        with open(path, "rb") as f:
            G = pickle.load(f)
        _memory_cache[key] = G
        return G

    # 3. Descargar desde OpenStreetMap
    north = tile_lat + TILE_SIZE + 0.02   # pequeño margen para solapamiento
    south = tile_lat          - 0.02
    east  = tile_lon + TILE_SIZE + 0.02
    west  = tile_lon          - 0.02

    print(f"[OSMnx] Descargando tile {key} ...")

    try:
        ver = tuple(int(x) for x in ox.__version__.split(".")[:2])
    except Exception:
        ver = (0, 0)

    if ver >= (2, 0):
        G = ox.graph_from_bbox(
            bbox=(west, south, east, north),
            network_type=GRAPH_NETWORK_TYPE,
            simplify=True,
        )
    else:
        G = ox.graph_from_bbox(
            north, south, east, west,
            network_type=GRAPH_NETWORK_TYPE,
            simplify=True,
        )

    print(f"[OSMnx] Tile {key}: {len(G.nodes)} nodos, {len(G.edges)} aristas")

    # Guardar en disco y memoria
    if CACHE_ENABLED:
        with open(path, "wb") as f:
            pickle.dump(G, f, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"[Cache] Guardado: {os.path.basename(path)}")

    _memory_cache[key] = G
    return G


def _merge_graphs(graphs):
    """Une múltiples grafos OSMnx en uno solo con networkx compose_all."""
    import networkx as nx
    if len(graphs) == 1:
        return graphs[0]
    print(f"[OSMnx] Uniendo {len(graphs)} tiles...")
    G = nx.compose_all(graphs)
    # Copiar atributos del primer grafo (crs, etc.)
    G.graph.update(graphs[0].graph)
    return G


def load_graph_between(origin_lat, origin_lon, dest_lat, dest_lon):
    """
    Devuelve el grafo que cubre la ruta origen→destino.
    Usa tiles fijos reutilizables: si el tile ya existe en disco
    no se descarga nada nuevo, independientemente del par origen/destino.
    """
    # Bbox de la ruta con margen mínimo
    min_lat = min(origin_lat, dest_lat)
    max_lat = max(origin_lat, dest_lat)
    min_lon = min(origin_lon, dest_lon)
    max_lon = max(origin_lon, dest_lon)

    lat_span = max_lat - min_lat
    lon_span = max_lon - min_lon
    margin_lat = max(lat_span * 0.05, 0.05)
    margin_lon = max(lon_span * 0.05, 0.05)

    south = min_lat - margin_lat
    north = max_lat + margin_lat
    west  = min_lon - margin_lon
    east  = max_lon + margin_lon

    tiles_needed = _tiles_for_bbox(south, west, north, east)
    print(f"[Cache] Ruta necesita {len(tiles_needed)} tile(s): {tiles_needed}")

    graphs = []
    for tile in sorted(tiles_needed):
        G = _load_tile(*tile)
        graphs.append(G)

    return _merge_graphs(graphs)


def nearest_node(G, lat, lon):
    """Nodo más cercano, con fallback si falta scikit-learn."""
    try:
        return ox.nearest_nodes(G, lon, lat)
    except ImportError:
        print("[OSMnx] Usando proyección (instala scikit-learn para mayor velocidad)")
        import pyproj
        G_proj = ox.project_graph(G)
        crs = G_proj.graph["crs"]
        transformer = pyproj.Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        x, y = transformer.transform(lon, lat)
        return ox.nearest_nodes(G_proj, x, y)