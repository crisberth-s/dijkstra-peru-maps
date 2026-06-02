# 🧬 Optimización de Rutas Viales con Algoritmo Genético

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-41CD52?style=flat-square&logo=qt&logoColor=white)
![OSMnx](https://img.shields.io/badge/OSMnx-OpenStreetMap-7EBC6F?style=flat-square&logo=openstreetmap&logoColor=white)
![Google Maps](https://img.shields.io/badge/Google%20Maps-API-4285F4?style=flat-square&logo=googlemaps&logoColor=white)
![License](https://img.shields.io/badge/Licencia-MIT-yellow?style=flat-square)

**Universidad Nacional del Altiplano · Puno**  
Facultad de Ingeniería Mecánica Eléctrica, Electrónica y Sistemas  
Escuela Profesional de Ingeniería de Sistemas  

*Curso: Inteligencia Artificial*  
**Autor: Crisberth**
*** Utilizar su propio API KEY ***
</div>

---

## 📌 Descripción

Sistema de optimización de rutas sobre la red vial real del Perú utilizando un **Algoritmo Genético (AG)**. El usuario selecciona un origen, un destino y ciudades intermedias opcionales; el algoritmo determina el orden óptimo de visita y traza la ruta real sobre calles descargadas de **OpenStreetMap** mediante OSMnx.

La interfaz gráfica está construida con **PyQt5** y un mapa **Google Maps** embebido vía QWebChannel como puente Python ↔ JavaScript.

---

## 🗂️ Estructura del Proyecto

```
dijkstra-peru/
│
├── backend/
│   ├── __init__.py
│   ├── genetic_tsp.py      # Núcleo del Algoritmo Genético
│   ├── graph.py            # Grafo OSMnx + llamada al AG
│   ├── dijkstra.py         # (Versión anterior — referencia)
│   ├── osm_loader.py       # Descarga y caché de grafos
│   └── path_builder.py     # Construcción de rutas reales
│
├── frontend/
│   └── index.html          # Mapa Google Maps + panel de control
│
├── cache_graphs/           # Grafos OSMnx cacheados (.pkl)
│
├── config.py               # API Key y parámetros globales
├── main.py                 # Ventana PyQt5 + QWebChannel
├── requirements.txt
└── README.md
```

---

## ⚙️ Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/crisberth-s/Algoritmo_Genetico.git
cd GENETICOS
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configurar la API Key de Google Maps

Edita `config.py` con tu clave (activa **Maps JavaScript API** y **Places API** en [Google Cloud Console](https://console.cloud.google.com/)):

```python
GOOGLE_MAPS_API_KEY = "TU_API_KEY_AQUÍ"
```

### 4. Ejecutar

```bash
python main.py
```

---

## 🧬 Algoritmo Genético

### Representación

Cada **individuo** es una permutación de los waypoints intermedios. Origen y destino son fijos en los extremos:

```
Ruta = [ Origen | π₁ π₂ … πₖ | Destino ]
```

### Operadores

| Operador | Método | Detalle |
|---|---|---|
| Selección | Torneo | Tamaño configurable (default 5) |
| Cruce | Order Crossover (OX) | Preserva orden relativo de ciudades |
| Mutación | Inversión de subsegmento | Mejor convergencia que swap simple |
| Elitismo | Top-N directo | Los mejores pasan sin modificarse |

### Parámetros (configurables desde la UI)

| Parámetro | Default | Rango |
|---|---|---|
| Generaciones | 200 | 50 – 500 |
| Población | 80 | 20 – 200 |
| Tasa de mutación | 2% | 1% – 20% |
| Élite | 10 | 2 – 20 |
| Parada temprana | 40 gen sin mejora | — |

### Flujo completo

```
1. Descargar grafo vial OSMnx (o cargar desde caché)
2. Mapear coordenadas → nodos OSM más cercanos
3. Construir matriz de distancias n×n (Dijkstra NetworkX)
4. Ejecutar AG → orden óptimo de waypoints
5. Construir ruta real concatenando shortest_paths
6. Enviar coordenadas a Google Maps → dibujar polilínea
```

---

## 🖥️ Interfaz

- **Panel lateral** con inputs de origen, destino y waypoints intermedios dinámicos
- **Sliders** para ajustar parámetros del AG en tiempo real
- **Curva de convergencia** del fitness dibujada en canvas HTML5
- **Estadísticas**: distancia (km), generaciones, tiempo de cómputo, orden óptimo de visita
- **Mapa oscuro** con polilínea azul sobre la red vial real

---

## 📦 Dependencias principales

```
PyQt5
PyQtWebEngine
osmnx
networkx
```

Instálalas todas con:

```bash
pip install -r requirements.txt
```

---
