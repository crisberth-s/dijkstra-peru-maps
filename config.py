# =============================================================
# config.py — Configuración central del proyecto
# =============================================================
# Reemplaza el valor de GOOGLE_MAPS_API_KEY con tu clave real.
# Obtén una en: https://console.cloud.google.com/
# Activa: Maps JavaScript API + Places API
# =============================================================

GOOGLE_MAPS_API_KEY = "tu_api_key"

# Radio (km) alrededor del origen para construir el grafo OSMnx
# Valores mayores = más detalle pero más lento en la primera carga
GRAPH_DIST_KM = 50          # distancia desde origen
GRAPH_NETWORK_TYPE = "drive"  # solo carreteras para autos

# Cache de grafos descargados (evita re-descargar en la misma sesión)
CACHE_ENABLED = True
