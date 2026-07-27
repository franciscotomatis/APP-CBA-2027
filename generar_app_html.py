#!/usr/bin/env python3
"""
GENERADOR DE APLICACIÓN WEB - VERSIÓN PRO
PROGRAMA CÓRDOBA 25/26
Con panel lateral, modo nocturno, filtros múltiples y gráficos
"""

import geopandas as gpd
import pandas as pd
import json
import folium
from folium import GeoJson
from folium.plugins import Fullscreen, MeasureControl, LocateControl
import hashlib
import sys
import os
from datetime import datetime
from owslib.wms import WebMapService
import re
import base64

print("🔐🌽🌱 GENERADOR PRO - PROGRAMA CÓRDOBA 25/26")
print("=" * 80)

# Configuración
USUARIO_CORRECTO = os.environ.get("MULTIRIESGO_USER") or "Sancor"
CONTRASENA_CORRECTA = os.environ.get("MULTIRIESGO_PASS") or "2025Sancor"

def generar_hash_seguro(texto):
    salt = "ProgramaCordoba25/26-SancorSeguro"
    hash_obj = hashlib.sha256(f"{texto}{salt}".encode())
    return hash_obj.hexdigest()[:16]

HASH_USUARIO = generar_hash_seguro(USUARIO_CORRECTO)
HASH_CONTRASENA = generar_hash_seguro(CONTRASENA_CORRECTA)

def cargar_geojson(ruta):
    print(f"📖 Cargando {ruta}...")
    with open(ruta, 'r', encoding='utf-8') as f:
        data = json.load(f)
    gdf = gpd.GeoDataFrame.from_features(data['features'])
    gdf.crs = "EPSG:4326"
    print(f"✅ {len(gdf)} polígonos")
    return data, gdf

def encontrar_campos(gdf):
    campos = {}
    for c in ['CULTIVO', 'cultivo', 'Cultivo']:
        if c in gdf.columns:
            campos['cultivo'] = c
            break
    for c in ['CLIENTE', 'cliente', 'Cliente']:
        if c in gdf.columns:
            campos['cliente'] = c
            break
    for c in ['ZONA_CZ4', 'ZONA', 'Zona']:
        if c in gdf.columns:
            campos['zona'] = c
            break
    for c in ['HECTAREAS_ASEGURADAS', 'HECTAREAS_DECLARADAS', 'hectareas']:
        if c in gdf.columns:
            campos['hectareas'] = c
            break
    return campos

def crear_app_pro(geojson_data, gdf, campos, output_file="index_pro.html"):
    print(f"\n🚀 CREANDO APP PRO: {output_file}")
    
    # Centro
    if not gdf.empty:
        minx, miny, maxx, maxy = gdf.total_bounds
        center = [(miny + maxy) / 2, (minx + maxx) / 2]
    else:
        center = [-31.4201, -64.1888]
    
    # Mapa base
    m = folium.Map(
        location=center,
        zoom_start=11,
        control_scale=True,
        tiles=None,
        zoom_control=True
    )
    
    # Capas base
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='🛰️ Satélite',
        max_zoom=19
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google',
        name='🗺️ Híbrido',
        max_zoom=20
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        attr='Google',
        name='🧭 Calles'
    ).add_to(m)
    
    # Capa principal
    folium.GeoJson(
        geojson_data,
        name='📍 Lotes asegurados',
        style_function=lambda f: {
            'fillColor': '#4CAF50',
            'color': '#2E7D32',
            'weight': 1.5,
            'fillOpacity': 0.5
        },
        popup=folium.GeoJsonPopup(
            fields=['CLIENTE', 'CULTIVO', 'HECTAREAS_ASEGURADAS', 'ZONA_CZ4'],
            aliases=['Cliente', 'Cultivo', 'Ha', 'Zona'],
            localize=True
        )
    ).add_to(m)
    
    # ========== HTML Y JAVASCRIPT COMPLETO ==========
    html_pro = f'''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PROGRAMA CÓRDOBA 25/26</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        :root {{
            --bg: #f0f2f5;
            --sidebar: #1a2332;
            --sidebar-text: #e0e4ea;
            --card: #ffffff;
            --text: #1a2332;
            --border: #e2e8f0;
            --shadow: 0 4px 20px rgba(0,0,0,0.1);
            --accent: #2d7d46;
            --accent-light: #e8f5e9;
            --radius: 12px;
            --transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        [data-theme="dark"] {{
            --bg: #0d1117;
            --sidebar: #161b22;
            --sidebar-text: #c9d1d9;
            --card: #1c2333;
            --text: #e6edf3;
            --border: #30363d;
            --shadow: 0 4px 20px rgba(0,0,0,0.4);
            --accent-light: #1a3a2a;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            transition: background var(--transition), color var(--transition);
            overflow: hidden;
            height: 100vh;
        }}
        
        /* ===== HEADER ===== */
        #header {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 56px;
            background: var(--sidebar);
            color: white;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 16px;
            z-index: 9999;
            box-shadow: 0 2px 12px rgba(0,0,0,0.3);
        }}
        
        #header .logo {{
            font-weight: 800;
            font-size: 18px;
            letter-spacing: -0.5px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        #header .logo span {{
            background: #2d7d46;
            padding: 2px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
        }}
        
        #header .search {{
            flex: 1;
            max-width: 400px;
            margin: 0 20px;
        }}
        
        #header .search input {{
            width: 100%;
            padding: 8px 16px;
            border: none;
            border-radius: 20px;
            background: rgba(255,255,255,0.12);
            color: white;
            font-size: 14px;
            outline: none;
            transition: background 0.3s;
        }}
        
        #header .search input::placeholder {{ color: rgba(255,255,255,0.5); }}
        #header .search input:focus {{ background: rgba(255,255,255,0.2); }}
        
        #header .actions {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        #header .actions button {{
            background: none;
            border: none;
            color: rgba(255,255,255,0.8);
            font-size: 20px;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 8px;
            transition: all 0.2s;
        }}
        
        #header .actions button:hover {{
            background: rgba(255,255,255,0.1);
            color: white;
        }}
        
        #themeToggle {{
            font-size: 22px;
        }}
        
        /* ===== SIDEBAR ===== */
        #sidebar {{
            position: fixed;
            top: 56px;
            left: 0;
            bottom: 0;
            width: 320px;
            background: var(--sidebar);
            color: var(--sidebar-text);
            z-index: 9998;
            overflow-y: auto;
            padding: 16px;
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            scrollbar-width: thin;
            scrollbar-color: rgba(255,255,255,0.2) transparent;
        }}
        
        #sidebar::-webkit-scrollbar {{ width: 4px; }}
        #sidebar::-webkit-scrollbar-track {{ background: transparent; }}
        #sidebar::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.2); border-radius: 4px; }}
        
        #sidebar.collapsed {{
            transform: translateX(-320px);
        }}
        
        #sidebar .section {{
            margin-bottom: 20px;
        }}
        
        #sidebar .section-title {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: rgba(255,255,255,0.4);
            margin-bottom: 8px;
            font-weight: 600;
        }}
        
        #sidebar .stats-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }}
        
        #sidebar .stat-card {{
            background: rgba(255,255,255,0.06);
            border-radius: 8px;
            padding: 12px;
            text-align: center;
        }}
        
        #sidebar .stat-card .num {{
            font-size: 22px;
            font-weight: 700;
            color: white;
        }}
        
        #sidebar .stat-card .label {{
            font-size: 10px;
            color: rgba(255,255,255,0.5);
            margin-top: 2px;
        }}
        
        /* Filtros */
        .filter-group {{
            margin-bottom: 12px;
        }}
        
        .filter-group label {{
            display: block;
            font-size: 12px;
            color: rgba(255,255,255,0.6);
            margin-bottom: 4px;
            font-weight: 500;
        }}
        
        .filter-group select {{
            width: 100%;
            padding: 8px 12px;
            border: none;
            border-radius: 8px;
            background: rgba(255,255,255,0.08);
            color: white;
            font-size: 13px;
            outline: none;
        }}
        
        .filter-group select option {{
            background: #1a2332;
            color: white;
        }}
        
        .filter-group .checkbox-group {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        
        .filter-group .checkbox-group label {{
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 12px;
            background: rgba(255,255,255,0.06);
            padding: 4px 10px;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.2s;
            color: rgba(255,255,255,0.7);
        }}
        
        .filter-group .checkbox-group label:hover {{
            background: rgba(255,255,255,0.12);
        }}
        
        .filter-group .checkbox-group input:checked + span {{
            color: white;
        }}
        
        .filter-group .checkbox-group input {{
            display: none;
        }}
        
        .filter-group .checkbox-group label.active {{
            background: #2d7d46;
            color: white;
        }}
        
        /* Galería de fotos */
        .foto-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 6px;
        }}
        
        .foto-grid .thumb {{
            aspect-ratio: 1;
            background: rgba(255,255,255,0.06);
            border-radius: 6px;
            cursor: pointer;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            color: rgba(255,255,255,0.3);
            transition: all 0.2s;
        }}
        
        .foto-grid .thumb:hover {{
            background: rgba(255,255,255,0.12);
            transform: scale(1.05);
        }}
        
        .foto-grid .thumb img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .foto-grid .thumb .empty {{
            font-size: 28px;
            opacity: 0.3;
        }}
        
        /* ===== MAPA ===== */
        #map-container {{
            position: fixed;
            top: 56px;
            left: 320px;
            right: 0;
            bottom: 0;
            transition: left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        #map-container.expanded {{
            left: 0;
        }}
        
        #map {{
            width: 100%;
            height: 100%;
        }}
        
        /* Toggle sidebar button */
        #toggleSidebar {{
            position: fixed;
            top: 66px;
            left: 330px;
            z-index: 9997;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 50%;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: var(--shadow);
            font-size: 16px;
            transition: all 0.3s;
            color: var(--text);
        }}
        
        #toggleSidebar:hover {{
            transform: scale(1.05);
        }}
        
        #toggleSidebar.shifted {{
            left: 10px;
        }}
        
        /* ===== DASHBOARD OVERLAY ===== */
        #dashboard-overlay {{
            position: fixed;
            top: 56px;
            left: 0;
            right: 0;
            bottom: 0;
            background: var(--bg);
            z-index: 9990;
            display: none;
            padding: 20px;
            overflow-y: auto;
        }}
        
        #dashboard-overlay.active {{
            display: block;
        }}
        
        #dashboard-overlay .close-dash {{
            position: fixed;
            top: 66px;
            right: 20px;
            z-index: 9992;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 20px;
            box-shadow: var(--shadow);
            color: var(--text);
        }}
        
        #dashboard-overlay .dash-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .dash-card {{
            background: var(--card);
            border-radius: var(--radius);
            padding: 20px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
        }}
        
        .dash-card h3 {{
            font-size: 14px;
            color: var(--text);
            margin-bottom: 12px;
            opacity: 0.7;
        }}
        
        .dash-card canvas {{
            width: 100% !important;
            max-height: 250px;
        }}
        
        /* ===== BOTTOM BAR ===== */
        #bottom-bar {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 48px;
            background: var(--sidebar);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 0 16px;
            z-index: 9996;
            border-top: 1px solid rgba(255,255,255,0.05);
        }}
        
        #bottom-bar button {{
            background: none;
            border: none;
            color: rgba(255,255,255,0.6);
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        
        #bottom-bar button:hover {{
            background: rgba(255,255,255,0.08);
            color: white;
        }}
        
        #bottom-bar button.primary {{
            background: #2d7d46;
            color: white;
        }}
        
        #bottom-bar button.primary:hover {{
            background: #3a9a5a;
        }}
        
        /* ===== RESPONSIVE ===== */
        @media (max-width: 768px) {{
            #sidebar {{
                width: 280px;
                transform: translateX(-280px);
            }}
            #sidebar.mobile-open {{
                transform: translateX(0);
            }}
            #map-container {{
                left: 0;
            }}
            #header .search {{
                max-width: 140px;
                margin: 0 8px;
            }}
            #header .logo {{
                font-size: 14px;
            }}
            #dashboard-overlay .dash-grid {{
                grid-template-columns: 1fr;
            }}
            #toggleSidebar {{
                left: 10px;
            }}
            .foto-grid {{
                grid-template-columns: 1fr 1fr;
            }}
        }}
    </style>
</head>
<body>

<!-- ===== HEADER ===== -->
<header id="header">
    <div class="logo">
        🌽 PROGRAMA CÓRDOBA 25/26
        <span>PRO</span>
    </div>
    <div class="search">
        <input type="text" id="searchInput" placeholder="🔍 Buscar cliente, campo, localidad..." oninput="buscarGlobal(this.value)">
    </div>
    <div class="actions">
        <button onclick="toggleTheme()" id="themeToggle" title="Modo nocturno">🌙</button>
        <button onclick="toggleSidebar()" title="Panel lateral">☰</button>
        <button onclick="abrirSubirFoto()" title="Subir foto">📸</button>
        <button onclick="toggleDashboard()" title="Dashboard">📊</button>
    </div>
</header>

<!-- ===== SIDEBAR ===== -->
<div id="sidebar">
    <!-- Estadísticas -->
    <div class="section">
        <div class="section-title">📊 Datos Generales</div>
        <div class="stats-grid">
            <div class="stat-card"><div class="num" id="totalLotes">0</div><div class="label">Lotes</div></div>
            <div class="stat-card"><div class="num" id="totalHectareas">0</div><div class="label">Hectáreas</div></div>
            <div class="stat-card"><div class="num" id="totalFotos">0</div><div class="label">Fotos</div></div>
            <div class="stat-card"><div class="num" id="totalZonas">0</div><div class="label">Zonas</div></div>
        </div>
    </div>
    
    <!-- Filtros -->
    <div class="section">
        <div class="section-title">🔍 Filtros</div>
        
        <div class="filter-group">
            <label>Cultivo</label>
            <div class="checkbox-group" id="cultivoFilters">
                <label class="active"><input type="checkbox" value="SOJA" checked><span>🌱 Soja</span></label>
                <label class="active"><input type="checkbox" value="MAÍZ" checked><span>🌽 Maíz</span></label>
                <label class="active"><input type="checkbox" value="TRIGO" checked><span>🌾 Trigo</span></label>
                <label class="active"><input type="checkbox" value="GIRASOL" checked><span>🌻 Girasol</span></label>
                <label class="active"><input type="checkbox" value="OTROS" checked><span>📦 Otros</span></label>
            </div>
        </div>
        
        <div class="filter-group">
            <label>Zona CZ4</label>
            <select id="zonaFilter" onchange="aplicarFiltros()">
                <option value="">Todas</option>
                <option value="1">Zona 1</option>
                <option value="2">Zona 2</option>
                <option value="3">Zona 3</option>
                <option value="4">Zona 4</option>
            </select>
        </div>
        
        <div class="filter-group">
            <label>Cliente</label>
            <input type="text" id="clienteFilter" placeholder="Escribí el nombre..." style="width:100%;padding:8px 12px;border:none;border-radius:8px;background:rgba(255,255,255,0.08);color:white;font-size:13px;outline:none;" oninput="aplicarFiltros()">
        </div>
        
        <button onclick="aplicarFiltros()" style="width:100%;padding:10px;background:#2d7d46;border:none;border-radius:8px;color:white;font-weight:600;cursor:pointer;font-size:14px;margin-top:8px;">
            🔄 Aplicar filtros
        </button>
        <button onclick="resetearFiltros()" style="width:100%;padding:8px;background:rgba(255,255,255,0.06);border:none;border-radius:8px;color:rgba(255,255,255,0.6);cursor:pointer;font-size:12px;margin-top:4px;">
            Resetear
        </button>
    </div>
    
    <!-- Fotos recientes -->
    <div class="section">
        <div class="section-title">📸 Fotos recientes</div>
        <div class="foto-grid" id="fotoGrid">
            <div class="thumb"><span class="empty">📷</span></div>
            <div class="thumb"><span class="empty">📷</span></div>
            <div class="thumb"><span class="empty">📷</span></div>
            <div class="thumb"><span class="empty">📷</span></div>
            <div class="thumb"><span class="empty">📷</span></div>
            <div class="thumb"><span class="empty">📷</span></div>
        </div>
    </div>
</div>

<!-- ===== MAPA ===== -->
<div id="map-container">
    <div id="map"></div>
</div>

<button id="toggleSidebar" onclick="toggleSidebar()">◀</button>

<!-- ===== BOTTOM BAR ===== -->
<div id="bottom-bar">
    <button onclick="abrirSubirFoto()">📸 Subir foto</button>
    <button onclick="toggleDashboard()">📊 Dashboard</button>
    <button onclick="exportarDatos()">📥 Exportar</button>
    <button onclick="toggleTheme()" id="themeBtn">🌙 Nocturno</button>
</div>

<!-- ===== DASHBOARD ===== -->
<div id="dashboard-overlay">
    <button class="close-dash" onclick="toggleDashboard()">✕</button>
    <div style="padding-top:20px;">
        <h2 style="margin-bottom:20px;color:var(--text);">📊 Dashboard Interactivo</h2>
        <div class="dash-grid">
            <div class="dash-card"><h3>🌱 Hectáreas por Cultivo</h3><canvas id="cultivoChart"></canvas></div>
            <div class="dash-card"><h3>📦 Hectáreas por Zona</h3><canvas id="zonaChart"></canvas></div>
            <div class="dash-card"><h3>📈 Evolución por Zona</h3><canvas id="evolucionChart"></canvas></div>
            <div class="dash-card"><h3>📊 Distribución de Lotes</h3><canvas id="distribucionChart"></canvas></div>
        </div>
    </div>
</div>

<!-- ===== PANEL SUBIR FOTO ===== -->
<div id="panelSubirFoto" style="display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:var(--card);padding:24px;border-radius:16px;z-index:10002;width:90%;max-width:420px;box-shadow:0 20px 60px rgba(0,0,0,0.5);border:1px solid var(--border);">
    <h3 style="margin-bottom:16px;color:var(--text);">📸 Subir foto</h3>
    <div id="previewFoto" style="width:100%;height:200px;background:var(--bg);border-radius:8px;display:flex;align-items:center;justify-content:center;color:var(--text);opacity:0.5;margin-bottom:12px;overflow:hidden;">
        <span>Sin foto seleccionada</span>
    </div>
    <div style="display:flex;gap:8px;margin-bottom:12px;">
        <button onclick="tomarFotoConCamara()" style="flex:1;padding:10px;background:#2d7d46;border:none;border-radius:8px;color:white;cursor:pointer;">📷 Cámara</button>
        <button onclick="seleccionarFotoArchivo()" style="flex:1;padding:10px;background:#1a73e8;border:none;border-radius:8px;color:white;cursor:pointer;">📁 Archivo</button>
    </div>
    <input type="file" id="inputFotoArchivo" accept="image/*" style="display:none;">
    <button onclick="subirFoto()" id="btnSubirFoto" style="width:100%;padding:12px;background:linear-gradient(135deg,#2d7d46,#1a5a33);border:none;border-radius:8px;color:white;font-weight:600;cursor:pointer;font-size:15px;">⬆️ Subir foto</button>
    <div id="infoGPS" style="font-size:12px;color:var(--text);opacity:0.6;margin-top:8px;text-align:center;">📍 Obteniendo ubicación...</div>
    <button onclick="cerrarPanelFoto()" style="width:100%;padding:8px;background:none;border:none;color:var(--text);opacity:0.4;cursor:pointer;margin-top:8px;">Cancelar</button>
</div>

<script>
// ============================================================
// INICIALIZACIÓN
// ============================================================

let map = null;
let sidebarOpen = true;
let darkMode = false;
let dashboardOpen = false;
let fotoActual = null;
let gpsActual = null;
let capaPoligonos = null;
let todasLasFotos = [];
let fotosCargadas = false;
let capaFotosGithub = null;

// Datos del GeoJSON (inyectados desde Python)
const GEOJSON_DATA = {json.dumps(geojson_data['features'])};
const CAMPOS = {json.dumps(campos)};
const TOTAL_LOTES = {len(gdf)};
const TOTAL_HECTAREAS = {gdf[campos.get('hectareas', 'HECTAREAS_ASEGURADAS')].sum() if campos.get('hectareas') else 0};

// Inicializar mapa
document.addEventListener('DOMContentLoaded', function() {{
    initMap();
    cargarEstadisticas();
    cargarFotosDesdeGithub();
}});

function initMap() {{
    map = L.map('map', {{
        center: [{center[0]}, {center[1]}],
        zoom: 11,
        zoomControl: false,
        attributionControl: true
    }});
    
    L.control.zoom({{position: 'topright'}}).addTo(map);
    
    // Capas base
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
        attribution: 'Esri',
        maxZoom: 19
    }}).addTo(map);
    
    L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={{x}}&y={{y}}&z={{z}}', {{
        attribution: 'Google',
        maxZoom: 20
    }}).addTo(map);
    
    // Capa de polígonos
    capaPoligonos = L.geoJSON(GEOJSON_DATA, {{
        style: function(feature) {{
            const cultivo = feature.properties[CAMPOS.cultivo] || 'OTROS';
            const colores = {{
                'SOJA': '#4CAF50',
                'MAÍZ': '#FFC107',
                'TRIGO': '#795548',
                'GIRASOL': '#FF9800',
                'OTROS': '#9E9E9E'
            }};
            return {{
                fillColor: colores[cultivo.toUpperCase()] || '#9C27B0',
                color: '#2E7D32',
                weight: 1.2,
                fillOpacity: 0.6
            }};
        }},
        onEachFeature: function(feature, layer) {{
            const props = feature.properties;
            const cliente = props[CAMPOS.cliente] || 'N/A';
            const cultivo = props[CAMPOS.cultivo] || 'N/A';
            const hectareas = props[CAMPOS.hectareas] || 0;
            const zona = props[CAMPOS.zona] || 'N/A';
            
            layer.bindPopup(`
                <div style="font-family:Arial,sans-serif;font-size:12px;max-width:280px;">
                    <strong style="color:#2d7d46;">${{cliente}}</strong><br>
                    🌱 ${{cultivo}}<br>
                    📏 ${{Number(hectareas).toLocaleString()}} ha<br>
                    📍 Zona ${{zona}}
                </div>
            `);
            
            layer.on('click', function() {{
                map.fitBounds(layer.getBounds(), {{padding: [50,50]}});
            }});
        }}
    }}).addTo(map);
    
    // GPS
    L.control.locate({{
        position: 'topright',
        drawCircle: true,
        follow: true,
        setView: true,
        keepCurrentZoomLevel: true,
        locateOptions: {{
            enableHighAccuracy: true,
            maximumAge: 30000,
            timeout: 27000,
            watch: true
        }}
    }}).addTo(map);
    
    // Ajustar tamaño
    setTimeout(() => map.invalidateSize(), 100);
}}

// ============================================================
// ESTADÍSTICAS
// ============================================================

function cargarEstadisticas() {{
    document.getElementById('totalLotes').textContent = TOTAL_LOTES;
    document.getElementById('totalHectareas').textContent = Number(TOTAL_HECTAREAS).toLocaleString();
    
    // Contar zonas únicas
    const zonas = new Set();
    GEOJSON_DATA.forEach(f => {{
        const z = f.properties[CAMPOS.zona];
        if (z) zonas.add(z);
    }});
    document.getElementById('totalZonas').textContent = zonas.size;
    
    // Fotos (se actualizará cuando se carguen)
    setTimeout(() => {{
        const grid = document.getElementById('fotoGrid');
        if (todasLasFotos.length > 0) {{
            document.getElementById('totalFotos').textContent = todasLasFotos.length;
            actualizarGaleria();
        }}
    }}, 2000);
}}

// ============================================================
// FILTROS
// ============================================================

function aplicarFiltros() {{
    const cultivosSeleccionados = [];
    document.querySelectorAll('#cultivoFilters input:checked').forEach(el => {{
        cultivosSeleccionados.push(el.value);
    }});
    
    const zona = document.getElementById('zonaFilter').value;
    const cliente = document.getElementById('clienteFilter').value.toLowerCase();
    
    // Filtrar en el mapa
    capaPoligonos.eachLayer(function(layer) {{
        const props = layer.feature.properties;
        const cultivo = (props[CAMPOS.cultivo] || 'OTROS').toUpperCase();
        const zonaFeature = props[CAMPOS.zona] || '';
        const clienteFeature = (props[CAMPOS.cliente] || '').toLowerCase();
        
        let visible = true;
        if (cultivosSeleccionados.length > 0 && !cultivosSeleccionados.includes(cultivo)) visible = false;
        if (zona && zonaFeature !== zona) visible = false;
        if (cliente && !clienteFeature.includes(cliente)) visible = false;
        
        if (visible) {{
            layer.setStyle({{ opacity: 1, fillOpacity: 0.6 }});
            layer.options.interactive = true;
        }} else {{
            layer.setStyle({{ opacity: 0, fillOpacity: 0 }});
            layer.options.interactive = false;
        }}
    }});
}}

function resetearFiltros() {{
    document.querySelectorAll('#cultivoFilters input').forEach(el => el.checked = true);
    document.querySelectorAll('#cultivoFilters label').forEach(el => el.classList.add('active'));
    document.getElementById('zonaFilter').value = '';
    document.getElementById('clienteFilter').value = '';
    aplicarFiltros();
}}

// Toggle active en filtros de cultivo
document.querySelectorAll('#cultivoFilters input').forEach(el => {{
    el.addEventListener('change', function() {{
        const label = this.closest('label');
        if (this.checked) label.classList.add('active');
        else label.classList.remove('active');
    }});
}});

// ============================================================
// BÚSQUEDA GLOBAL
// ============================================================

function buscarGlobal(texto) {{
    if (!texto || texto.length < 3) return;
    const palabra = texto.toLowerCase();
    let encontrado = false;
    
    capaPoligonos.eachLayer(function(layer) {{
        const cliente = (layer.feature.properties[CAMPOS.cliente] || '').toLowerCase();
        const campo = (layer.feature.properties['CAMPO'] || '').toLowerCase();
        const localidad = (layer.feature.properties['LOCALIDAD'] || '').toLowerCase();
        
        if (cliente.includes(palabra) || campo.includes(palabra) || localidad.includes(palabra)) {{
            encontrado = true;
            map.fitBounds(layer.getBounds(), {{padding: [80,80]}});
            layer.openPopup();
        }}
    }});
    
    if (!encontrado) {{
        // Mostrar notificación simple
        const el = document.createElement('div');
        el.style.cssText = 'position:fixed;top:70px;left:50%;transform:translateX(-50%);background:#f44336;color:white;padding:10px 24px;border-radius:8px;z-index:99999;font-size:14px;box-shadow:0 4px 12px rgba(0,0,0,0.2);';
        el.textContent = '🔍 No se encontraron resultados';
        document.body.appendChild(el);
        setTimeout(() => el.remove(), 3000);
    }}
}}

// ============================================================
// TOGGLES
// ============================================================

function toggleSidebar() {{
    sidebarOpen = !sidebarOpen;
    document.getElementById('sidebar').classList.toggle('collapsed');
    document.getElementById('map-container').classList.toggle('expanded');
    const btn = document.getElementById('toggleSidebar');
    btn.classList.toggle('shifted');
    btn.textContent = sidebarOpen ? '◀' : '▶';
    setTimeout(() => map.invalidateSize(), 350);
}}

function toggleTheme() {{
    darkMode = !darkMode;
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light');
    document.getElementById('themeToggle').textContent = darkMode ? '☀️' : '🌙';
    document.getElementById('themeBtn').textContent = darkMode ? '☀️ Diurno' : '🌙 Nocturno';
    setTimeout(() => map.invalidateSize(), 100);
}}

function toggleDashboard() {{
    dashboardOpen = !dashboardOpen;
    document.getElementById('dashboard-overlay').classList.toggle('active');
    if (dashboardOpen) {{
        setTimeout(() => generarGraficos(), 300);
    }}
}}

// ============================================================
// GRÁFICOS (Dashboard)
// ============================================================

function generarGraficos() {{
    // Agrupar datos
    const cultivos = {{}};
    const zonas = {{}};
    const zonasCultivos = {{}};
    
    GEOJSON_DATA.forEach(f => {{
        const c = f.properties[CAMPOS.cultivo] || 'OTROS';
        const z = f.properties[CAMPOS.zona] || '0';
        const h = Number(f.properties[CAMPOS.hectareas]) || 0;
        
        cultivos[c] = (cultivos[c] || 0) + h;
        zonas[z] = (zonas[z] || 0) + h;
        const key = z + '_' + c;
        zonasCultivos[key] = (zonasCultivos[key] || 0) + h;
    }});
    
    // Gráfico 1: Cultivos
    const ctx1 = document.getElementById('cultivoChart').getContext('2d');
    new Chart(ctx1, {{
        type: 'bar',
        data: {{
            labels: Object.keys(cultivos),
            datasets: [{{
                label: 'Hectáreas',
                data: Object.values(cultivos),
                backgroundColor: ['#4CAF50','#FFC107','#795548','#FF9800','#9E9E9E'],
                borderRadius: 6
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: true,
            plugins: {{
                legend: {{ display: false }}
            }}
        }}
    }});
    
    // Gráfico 2: Zonas
    const ctx2 = document.getElementById('zonaChart').getContext('2d');
    new Chart(ctx2, {{
        type: 'doughnut',
        data: {{
            labels: Object.keys(zonas),
            datasets: [{{
                data: Object.values(zonas),
                backgroundColor: ['#2d7d46','#4CAF50','#66BB6A','#A5D6A7']
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: true
        }}
    }});
    
    // Gráfico 3: Evolución
    const ctx3 = document.getElementById('evolucionChart').getContext('2d');
    const zonasKeys = Object.keys(zonas).sort();
    new Chart(ctx3, {{
        type: 'line',
        data: {{
            labels: zonasKeys,
            datasets: [{
                label: 'Hectáreas por zona',
                data: zonasKeys.map(z => zonas[z]),
                borderColor: '#2d7d46',
                backgroundColor: 'rgba(45,125,70,0.1)',
                fill: true,
                tension: 0.4
            }]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: true
        }}
    }});
    
    // Gráfico 4: Distribución
    const ctx4 = document.getElementById('distribucionChart').getContext('2d');
    new Chart(ctx4, {{
        type: 'polarArea',
        data: {{
            labels: Object.keys(cultivos),
            datasets: [{{
                data: Object.values(cultivos),
                backgroundColor: ['#4CAF50','#FFC107','#795548','#FF9800','#9E9E9E']
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: true
        }}
    }});
}}

// ============================================================
// FOTOS
// ============================================================

async function cargarFotosDesdeGithub() {{
    try {{
        const response = await fetch('{FOTOS_JSON_URL}');
        if (!response.ok) throw new Error('HTTP ' + response.status);
        const data = await response.json();
        todasLasFotos = data.features || [];
        document.getElementById('totalFotos').textContent = todasLasFotos.length;
        actualizarGaleria();
        
        // Capa de fotos en el mapa
        capaFotosGithub = L.geoJSON(todasLasFotos, {{
            pointToLayer: function(feature, latlng) {{
                return L.circleMarker(latlng, {{
                    radius: 8,
                    fillColor: '#F44336',
                    color: '#FFFFFF',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.9,
                    zIndexOffset: 1000
                }});
            }},
            onEachFeature: function(feature, layer) {{
                const props = feature.properties;
                const nombre = props.NOMBRE_FOTO || 'Foto';
                const imgUrl = props.IMAGEN_URL || '';
                
                layer.bindTooltip('📸 ' + nombre, {{sticky: true, direction: 'top'}});
                layer.bindPopup(`
                    <div style="max-width:400px;font-family:Arial,sans-serif;">
                        <div style="font-weight:bold;font-size:14px;margin-bottom:8px;">📸 ${{nombre}}</div>
                        <img src="${{imgUrl}}" style="max-width:100%;max-height:300px;border-radius:8px;border:2px solid #F44336;">
                        <div style="font-size:10px;color:#666;margin-top:6px;text-align:center;">📍 GPS • Click para ampliar</div>
                    </div>
                `);
            }}
        }}).addTo(map);
        capaFotosGithub.bringToFront();
        fotosCargadas = true;
        
    }} catch (e) {{
        console.log('Error cargando fotos:', e);
    }}
}}

function actualizarGaleria() {{
    const grid = document.getElementById('fotoGrid');
    const fotos = todasLasFotos.slice(0, 6);
    grid.innerHTML = fotos.map(f => {{
        const url = f.properties.MINIATURA_URL || f.properties.IMAGEN_URL || '';
        const nombre = f.properties.NOMBRE_FOTO || 'Foto';
        return `<div class="thumb" onclick="verFoto('${{url}}')">
            ${{url ? `<img src="${{url}}" alt="${{nombre}}">` : `<span class="empty">📷</span>`}}
        </div>`;
    }}).join('');
}}

function verFoto(url) {{
    if (url) window.open(url, '_blank');
}}

// ============================================================
// SUBIR FOTO
// ============================================================

function abrirSubirFoto() {{
    document.getElementById('panelSubirFoto').style.display = 'block';
    obtenerUbicacionGPS();
}}

function cerrarPanelFoto() {{
    document.getElementById('panelSubirFoto').style.display = 'none';
    fotoActual = null;
}}

function obtenerUbicacionGPS() {{
    const infoGPS = document.getElementById('infoGPS');
    if (!navigator.geolocation) {{
        infoGPS.textContent = '❌ GPS no disponible';
        return;
    }}
    infoGPS.textContent = '📍 Obteniendo ubicación...';
    navigator.geolocation.getCurrentPosition(
        pos => {{
            gpsActual = {{
                lat: pos.coords.latitude.toFixed(6),
                lon: pos.coords.longitude.toFixed(6)
            }};
            infoGPS.textContent = `📍 ${{gpsActual.lat}}, ${{gpsActual.lon}}`;
        }},
        () => {{
            infoGPS.textContent = '⚠️ Usando ubicación por defecto';
            gpsActual = {lat: '-31.4201', lon: '-64.1888'};
        }}
    );
}}

function tomarFotoConCamara() {{
    const input = document.getElementById('inputFotoArchivo');
    input.setAttribute('capture', 'environment');
    input.click();
}}

function seleccionarFotoArchivo() {{
    const input = document.getElementById('inputFotoArchivo');
    input.removeAttribute('capture');
    input.click();
}}

document.getElementById('inputFotoArchivo').addEventListener('change', function(e) {{
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(event) {{
        fotoActual = event.target.result;
        document.getElementById('previewFoto').innerHTML = 
            `<img src="${{fotoActual}}" style="width:100%;height:100%;object-fit:cover;">`;
        document.getElementById('previewFoto').querySelector('span')?.remove();
        if (!gpsActual) obtenerUbicacionGPS();
    }};
    reader.readAsDataURL(file);
}});

async function subirFoto() {{
    if (!fotoActual) {{
        alert('Selecciona una foto primero');
        return;
    }}
    
    const btn = document.getElementById('btnSubirFoto');
    btn.textContent = '⏳ Subiendo...';
    btn.disabled = true;
    
    const base64Data = fotoActual.split(',')[1];
    const nombre = `foto_${{Date.now()}}.jpg`;
    const lat = gpsActual ? gpsActual.lat : '-31.4201';
    const lon = gpsActual ? gpsActual.lon : '-64.1888';
    
    try {{
        const response = await fetch(
            'https://api.github.com/repos/franciscotomatis/APP-CBA-2027/actions/workflows/recibir-foto.yml/dispatches',
            {{
                method: 'POST',
                headers: {{
                    'Accept': 'application/vnd.github.v3+json',
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify({{
                    ref: 'main',
                    inputs: {{
                        foto_base64: base64Data,
                        nombre_archivo: nombre,
                        latitud: lat,
                        longitud: lon
                    }}
                }})
            }}
        );
        
        if (response.ok) {{
            btn.textContent = '✅ ¡Subida!';
            setTimeout(() => {{
                cerrarPanelFoto();
                btn.textContent = '⬆️ Subir foto';
                btn.disabled = false;
                mostrarNotificacion('✅ Foto subida exitosamente');
                // Recargar fotos
                setTimeout(cargarFotosDesdeGithub, 5000);
            }}, 1500);
        }} else {{
            throw new Error('Error ' + response.status);
        }}
    }} catch (e) {{
        console.error(e);
        btn.textContent = '❌ Error';
        setTimeout(() => {{
            btn.textContent = '⬆️ Subir foto';
            btn.disabled = false;
            mostrarNotificacion('❌ Error al subir la foto');
        }}, 2000);
    }}
}}

function mostrarNotificacion(mensaje) {{
    const el = document.createElement('div');
    el.style.cssText = 'position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:#2d7d46;color:white;padding:12px 24px;border-radius:12px;z-index:99999;font-size:14px;box-shadow:0 4px 20px rgba(0,0,0,0.3);';
    el.textContent = mensaje;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 4000);
}}

// ============================================================
// EXPORTAR
// ============================================================

function exportarDatos() {{
    const data = GEOJSON_DATA.map(f => {{
        const p = f.properties;
        return {{
            cliente: p[CAMPOS.cliente] || '',
            cultivo: p[CAMPOS.cultivo] || '',
            hectareas: p[CAMPOS.hectareas] || 0,
            zona: p[CAMPOS.zona] || ''
        }};
    }});
    const csv = 'Cliente,Cultivo,Hectáreas,Zona\\n' + 
        data.map(r => `${{r.cliente}},${{r.cultivo}},${{r.hectareas}},${{r.zona}}`).join('\\n');
    const blob = new Blob([csv], {{type: 'text/csv'}});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'datos_cordoba.csv';
    a.click();
    URL.revokeObjectURL(url);
}}

// ============================================================
// INICIALIZAR
// ============================================================

console.log('🌽 PROGRAMA CÓRDOBA 25/26 - PRO');
console.log('📍 Lotes:', TOTAL_LOTES);
console.log('📏 Hectáreas:', TOTAL_HECTAREAS);
</script>
</body>
</html>
    '''
    
    # Agregar el HTML al mapa
    m.get_root().html.add_child(folium.Element(html_pro))
    
    # Guardar
    m.save(output_file)
    print(f"✅ App PRO guardada: {output_file}")
    return output_file

def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python generar_app_pro.py <geojson> [output]")
        sys.exit(1)
    
    ruta = sys.argv[1]
    salida = sys.argv[2] if len(sys.argv) > 2 else "index_pro.html"
    
    data, gdf = cargar_geojson(ruta)
    campos = encontrar_campos(gdf)
    
    print("\n✅ Campos encontrados:")
    for k, v in campos.items():
        print(f"   • {k}: '{v}'")
    
    crear_app_pro(data, gdf, campos, salida)
    print(f"\n🎉 App generada: {salida}")
    print(f"📊 {len(gdf)} polígonos cargados")
    print("🚀 Abrí el archivo en tu navegador")

if __name__ == "__main__":
    main()
