# 🗺️ Dijkstra Perú — Rutas sobre OpenStreetMap

Aplicación de escritorio en **PyQt5** que calcula rutas entre ciudades del Perú
usando el **algoritmo de Dijkstra implementado manualmente** sobre el grafo vial de **OpenStreetMap**, visualizado con **Google Maps**.

---

## 🚀 Instalación

```bash
git clone <repo>
cd dijkstra-peru-maps

python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt

# =============================================================
# config.py — Configuración central del proyecto
# =============================================================
# Reemplaza el valor de GOOGLE_MAPS_API_KEY con tu clave real.
# Obtén una en: https://console.cloud.google.com/
# Activa: Maps JavaScript API + Places API
# =============================================================

