#!/usr/bin/env python3
# main.py — Aplicación principal PyQt5 con mapa Google Maps embebido.

import sys
import os
import json
import threading

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QSizePolicy, QStatusBar
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, QUrl, QTimer
from PyQt5.QtGui import QIcon, QFont
import PyQt5.QtWebEngineWidgets  # noqa

# Necesario antes de crear QApplication en algunos sistemas
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-web-security")

from config import GOOGLE_MAPS_API_KEY
from backend.graph import calculate_route


# ─── Puente Python ↔ JavaScript ────────────────────────────────────────────
class Bridge(QObject):
    """Objeto expuesto a JS via QWebChannel."""

    # Señal que emite la ruta calculada hacia JavaScript
    routeReady = pyqtSignal(str)

    @pyqtSlot(str)
    def calculateRoute(self, payload_json: str):
        """
        Llamado desde JavaScript con el JSON de origen/destino.
        Lanza el cálculo en un hilo separado para no bloquear la UI.
        """
        print(f"[Bridge] Solicitud recibida: {payload_json[:120]}...")
        thread = threading.Thread(
            target=self._run_calculation,
            args=(payload_json,),
            daemon=True,
        )
        thread.start()

    def _run_calculation(self, payload_json: str):
        try:
            data = json.loads(payload_json)
            result = calculate_route(
                origin_lat=data["origin_lat"],
                origin_lon=data["origin_lon"],
                dest_lat=data["dest_lat"],
                dest_lon=data["dest_lon"],
            )
            # Agregar nombres para mostrar
            result["origin_name"] = data.get("origin_name", "")
            result["dest_name"]   = data.get("dest_name",   "")
        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "coordinates": [],
                "distance_km": 0,
                "nodes_count": 0,
            }

        # Emitir de vuelta al hilo principal → JavaScript
        self.routeReady.emit(json.dumps(result))


# ─── Vista web con página personalizada ───────────────────────────────────
class MapPage(QWebEnginePage):
    """Página web que redirige los logs de consola JS a Python."""

    def javaScriptConsoleMessage(self, level, msg, line, source):
        icons = {0: "ℹ", 1: "⚠", 2: "✖", 3: "🐛"}
        print(f"  JS [{icons.get(level,'?')}] {msg}  ({source}:{line})")


# ─── Ventana principal ────────────────────────────────────────────────────
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dijkstra Perú — Rutas Reales sobre OpenStreetMap")
        self.resize(1280, 800)
        self.setMinimumSize(900, 600)

        self._setup_ui()
        self._setup_webchannel()
        self._load_map()

    # ── UI ────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barra de título personalizada
        title_bar = QWidget()
        title_bar.setFixedHeight(36)
        title_bar.setStyleSheet("""
            background: #0f0f14;
            border-bottom: 1px solid #1e2030;
        """)
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(16, 0, 16, 0)

        logo = QLabel("🗺  Dijkstra Perú")
        logo.setFont(QFont("Segoe UI", 11, QFont.Bold))
        logo.setStyleSheet("color: #5090e8; letter-spacing: 0.5px;")

        subtitle = QLabel("Algoritmo de Dijkstra sobre red vial real (OpenStreetMap)")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet("color: #556070;")

        tb_layout.addWidget(logo)
        tb_layout.addWidget(subtitle)
        tb_layout.addStretch()

        layout.addWidget(title_bar)

        # Vista del mapa
        self.web_view = QWebEngineView()
        self.web_page = MapPage(self.web_view)
        self.web_view.setPage(self.web_page)
        self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.web_view)

        # Barra de estado
        status_bar = self.statusBar()
        status_bar.setStyleSheet("background: #0f0f14; color: #556070; font-size: 11px;")
        status_bar.showMessage("  Listo. Escribe origen y destino en el mapa.")

    # ── QWebChannel ───────────────────────────────────────────────────────
    def _setup_webchannel(self):
        self.bridge = Bridge()
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.web_page.setWebChannel(self.channel)

        # Actualizar barra de estado cuando llegue una ruta
        self.bridge.routeReady.connect(self._on_route_ready)

    def _on_route_ready(self, json_str: str):
        try:
            result = json.loads(json_str)
            if result["success"]:
                self.statusBar().showMessage(
                    f"  ✓ Ruta calculada: {result['distance_km']} km  "
                    f"({result['nodes_count']} nodos Dijkstra)  "
                    f"| {result.get('origin_name','')} → {result.get('dest_name','')}"
                )
            else:
                self.statusBar().showMessage(f"  ✖ Error: {result['error']}")
        except Exception:
            pass

    # ── Cargar HTML ───────────────────────────────────────────────────────
    def _load_map(self):
        html_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "frontend", "index.html"
        )

        # Leer el HTML, inyectar la API Key en un meta tag
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        html = html.replace(
            "<head>",
            f'<head>\n  <meta name="gmaps-key" content="{GOOGLE_MAPS_API_KEY}"/>'
        )

        # Usar setHtml con base URL para que qrc:// y rutas relativas funcionen
        base_url = QUrl.fromLocalFile(os.path.dirname(html_path) + os.sep)
        self.web_view.setHtml(html, base_url)


# ─── Entrada ──────────────────────────────────────────────────────────────
def main():
    # Necesario para QtWebEngine en algunos sistemas
    QApplication.setAttribute(__import__("PyQt5.QtCore", fromlist=["Qt"]).Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(__import__("PyQt5.QtCore", fromlist=["Qt"]).Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    app.setApplicationName("Dijkstra Perú")
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
