#!/usr/bin/env python3
"""
GENERADOR DE APLICACIÓN WEB - LEAFLET PURO
Versión con controles en sidebar y mapa limpio
"""

import geopandas as gpd
import pandas as pd
import json
import hashlib
import sys
import os
from datetime import datetime
from owslib.wms import WebMapService
import re

print("🌱 GENERADOR DE APLICACIÓN WEB - LEAFLET PURO")
print("=" * 80)

# 🔐 CREDENCIALES DE ACCESO
USUARIO_CORRECTO = os.environ.get("MULTIRIESGO_USER")
CONTRASENA_CORRECTA = os.environ.get("MULTIRIESGO_PASS")

if not USUARIO_CORRECTO or not CONTRASENA_CORRECTA:
    print("⚠️  ADVERTENCIA: No se encontraron credenciales")
    USUARIO_CORRECTO = USUARIO_CORRECTO or "UsuarioDemo"
    CONTRASENA_CORRECTA = CONTRASENA_CORRECTA or "PassDemo"

def generar_hash_seguro(texto):
    salt = "ProgramaCordoba25/26-SancorSeguro"
    hash_obj = hashlib.sha256(f"{texto}{salt}".encode())
    return hash_obj.hexdigest()[:16]

HASH_USUARIO = generar_hash_seguro(USUARIO_CORRECTO)
HASH_CONTRASENA = generar_hash_seguro(CONTRASENA_CORRECTA)

def cargar_geojson(ruta_geojson):
    print(f"📖 Cargando {ruta_geojson}...")
    with open(ruta_geojson, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
    gdf.crs = "EPSG:4326"
    print(f"✅ GeoJSON cargado: {len(gdf)} polígonos")
    return geojson_data, gdf

def encontrar_campos(gdf):
    campo_cultivo = None
    for campo in ['CULTIVO', 'cultivo', 'Cultivo', 'CROP', 'crop']:
        if campo in gdf.columns:
            campo_cultivo = campo
            break

    campo_hectareas = None
    for campo in ['HECTAREAS_ASEGURADAS', 'HECTAREAS_DECLARADAS', 'hectareas', 'HECTAREAS', 'HAS', 'has']:
        if campo in gdf.columns:
            campo_hectareas = campo
            break

    campo_cliente = None
    for campo in ['CLIENTE', 'cliente', 'Cliente', 'NOMBRE_CLIENTE']:
        if campo in gdf.columns:
            campo_cliente = campo
            break

    campo_zona = None
    for campo in ['ZONA_CZ4', 'ZONA', 'Zona', 'zona', 'CZ4']:
        if campo in gdf.columns:
            campo_zona = campo
            break

    campo_causa_stro = None
    for campo in ['CAUSA_STRO', 'CAUSA_SINIESTRO', 'CAUSA', 'causa_stro']:
        if campo in gdf.columns:
            campo_causa_stro = campo
            break

    campo_fecha_stro = None
    if 'Fecha Stro' in gdf.columns:
        campo_fecha_stro = 'Fecha Stro'
    else:
        for campo in ['FechaStro', 'Fecha_Stro', 'FECHA_STRO', 'FECHA_SINIESTRO', 'FECHA', 'fecha_stro']:
            if campo in gdf.columns:
                campo_fecha_stro = campo
                break

    campo_dano_stro = None
    for campo in ['DAÑO_ESTIMADO', 'DAÑO', 'DANO_ESTIMADO', 'DANO', 'PERDIDA', 'PERDIDA_ESTIMADA']:
        if campo in gdf.columns:
            campo_dano_stro = campo
            break

    return {
        'cultivo': campo_cultivo,
        'hectareas': campo_hectareas,
        'cliente': campo_cliente,
        'zona': campo_zona,
        'causa_stro': campo_causa_stro,
        'fecha_stro': campo_fecha_stro,
        'dano_stro': campo_dano_stro
    }

def crear_app_leaflet(geojson_data, gdf, campos, output_file):
    """CREA APLICACIÓN CON LEAFLET PURO"""
    
    print(f"\n🗺️ Creando aplicación con Leaflet puro: {output_file}")
    
    if not gdf.empty:
        minx, miny, maxx, maxy = gdf.total_bounds
        bounds = [[miny, minx], [maxy, maxx]]
        center = [(miny + maxy) / 2, (minx + maxx) / 2]
    else:
        center = [-31.4201, -64.1888]
        bounds = [[center[0]-0.1, center[1]-0.1], [center[0]+0.1, center[1]+0.1]]

    # ===== PREPARAR DATOS =====
    total_poligonos = len(gdf)
    total_hectareas = gdf[campos.get('hectareas', 'HECTAREAS_ASEGURADAS')].sum() if campos.get('hectareas') else 0
    
    cultivos_unicos = []
    if campos['cultivo'] and campos['cultivo'] in gdf.columns:
        cultivos_unicos = sorted(gdf[campos['cultivo']].dropna().unique())
    
    clientes_unicos = []
    if campos['cliente'] and campos['cliente'] in gdf.columns:
        clientes_unicos = sorted(gdf[campos['cliente']].dropna().astype(str).unique())
    
    # ===== Checkboxes cultivos =====
    checkboxes_cultivos = ""
    for cultivo in cultivos_unicos:
        cultivo_str = str(cultivo).upper()
        checkboxes_cultivos += f'<label class="active"><input type="checkbox" value="{cultivo_str}" checked><span>{cultivo_str.capitalize()}</span></label>'
    
    opciones_clientes = "".join(f'<option value="{cliente}">' for cliente in clientes_unicos)
    
    # ===== Datos de cultivos para el panel =====
    datos_cultivos = {}
    if campos['cultivo'] and campos['cultivo'] in gdf.columns and campos['hectareas']:
        for cultivo in cultivos_unicos:
            mascara = gdf[campos['cultivo']] == cultivo
            hectareas = gdf.loc[mascara, campos['hectareas']].sum() if campos['hectareas'] else 0
            datos_cultivos[str(cultivo)] = float(hectareas)
    
    cultivos_panel_html = ""
    for cultivo, hectareas in datos_cultivos.items():
        cultivo_str = str(cultivo).upper()
        cultivos_panel_html += f'''
        <div class="stat-row">
            <span>{cultivo_str.capitalize()}</span>
            <span>{hectareas:,.0f} ha</span>
        </div>
        '''
    
    total_zonas = len(gdf[campos['zona']].dropna().unique()) if campos['zona'] else 0
    
    # ===== Convertir datos a JSON para JavaScript =====
    geojson_str = json.dumps(geojson_data)
    FOTOS_JSON_URL = "https://raw.githubusercontent.com/franciscotomatis/APP-C-rdoba/main/fotos_metadata/fotos_procesadas.json"
    
    # ===== GENERAR HTML COMPLETO =====
    html_completo = f'''
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Programa Córdoba 25/26</title>

<!-- Leaflet CSS -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<!-- Leaflet JS -->
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<!-- Leaflet Draw (para medición) -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.css" />
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js"></script>
<!-- Esri Leaflet -->
<script src="https://unpkg.com/esri-leaflet@3.0.12/dist/esri-leaflet.js"></script>

<!-- Google Fonts -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">

<style>
/* ===== RESET & BASE ===== */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

:root {{
    --bg: #f5f7fa;
    --sidebar: #ffffff;
    --sidebar-text: #1a2332;
    --card: #ffffff;
    --text: #0f172a;
    --border: #e8ecf0;
    --shadow: 0 2px 12px rgba(0,0,0,0.06);
    --header-height: 56px;
    --bottom-height: 48px;
    --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --accent: #1a7a3a;
    --accent-hover: #145a2a;
    --radius: 8px;
    --sidebar-width: 300px;
}}

[data-theme="dark"] {{
    --bg: #0a0a0a;
    --sidebar: #141414;
    --sidebar-text: #e5e5e5;
    --card: #1a1a1a;
    --text: #f0f0f0;
    --border: #2a2a2a;
    --shadow: 0 2px 12px rgba(0,0,0,0.4);
}}

html, body {{ 
    height: 100%; 
    font-family: var(--font); 
    background: var(--bg); 
    color: var(--text); 
    overflow: hidden;
    -webkit-font-smoothing: antialiased;
}}

/* ===== HEADER ===== */
#header {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: var(--header-height);
    background: var(--sidebar);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    z-index: 9999;
    box-shadow: var(--shadow);
}}

#header .logo {{
    font-weight: 700;
    font-size: 15px;
    letter-spacing: -0.3px;
    color: var(--text);
}}

#header .logo span {{
    background: var(--accent);
    color: white;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 10px;
    font-weight: 600;
    margin-left: 6px;
}}

#header .actions {{
    display: flex;
    align-items: center;
    gap: 6px;
}}

#header .actions button {{
    background: none;
    border: none;
    color: var(--text);
    opacity: 0.5;
    font-size: 12px;
    cursor: pointer;
    padding: 6px 12px;
    border-radius: var(--radius);
    transition: all 0.2s;
    font-family: var(--font);
    font-weight: 500;
}}

#header .actions button:hover {{
    opacity: 1;
    background: var(--border);
}}

/* ===== SIDEBAR ===== */
#sidebar {{
    position: fixed;
    top: var(--header-height);
    left: 0;
    bottom: var(--bottom-height);
    width: var(--sidebar-width);
    background: var(--sidebar);
    border-right: 1px solid var(--border);
    color: var(--sidebar-text);
    z-index: 9998;
    overflow-y: auto;
    padding: 16px 16px 20px;
    transition: transform 0.3s ease;
    scrollbar-width: thin;
    scrollbar-color: var(--border) transparent;
}}

#sidebar::-webkit-scrollbar {{ width: 4px; }}
#sidebar::-webkit-scrollbar-track {{ background: transparent; }}
#sidebar::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 4px; }}

#sidebar.collapsed {{
    transform: translateX(-300px);
}}

#sidebar .section {{
    margin-bottom: 20px;
}}

#sidebar .section-title {{
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text);
    opacity: 0.35;
    margin-bottom: 10px;
    font-weight: 600;
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
}}

/* ===== STATS ===== */
#sidebar .stats-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}}

#sidebar .stat-card {{
    background: var(--bg);
    border-radius: var(--radius);
    padding: 12px;
    text-align: center;
    border: 1px solid var(--border);
}}

#sidebar .stat-card .num {{
    font-size: 20px;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.3px;
}}

#sidebar .stat-card .label {{
    font-size: 9px;
    color: var(--text);
    opacity: 0.4;
    margin-top: 2px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}}

/* ===== STATS LIST ===== */
.stats-list {{
    background: var(--bg);
    border-radius: var(--radius);
    padding: 6px 12px;
    border: 1px solid var(--border);
}}

.stats-list .stat-row {{
    display: flex;
    justify-content: space-between;
    padding: 5px 0;
    border-bottom: 1px solid var(--border);
    font-size: 12px;
    color: var(--text);
}}

.stats-list .stat-row:last-child {{
    border-bottom: none;
}}

.stats-list .stat-row span:last-child {{
    font-weight: 600;
}}

.stats-list .stat-total {{
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    margin-top: 4px;
    border-top: 1px solid var(--border);
    font-weight: 700;
    font-size: 13px;
    color: var(--text);
}}

/* ===== FILTROS ===== */
.filter-group {{
    margin-bottom: 12px;
}}

.filter-group label {{
    display: block;
    font-size: 11px;
    color: var(--text);
    opacity: 0.5;
    margin-bottom: 5px;
    font-weight: 500;
}}

.filter-group .checkbox-group {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}}

.filter-group .checkbox-group label {{
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    background: var(--bg);
    padding: 4px 12px;
    border-radius: 16px;
    cursor: pointer;
    transition: all 0.2s;
    color: var(--text);
    opacity: 0.5;
    font-weight: 400;
    margin-bottom: 0;
    border: 1px solid var(--border);
}}

.filter-group .checkbox-group label:hover {{
    opacity: 0.8;
}}

.filter-group .checkbox-group input:checked + span {{
    opacity: 1;
}}

.filter-group .checkbox-group input {{
    display: none;
}}

.filter-group .checkbox-group label.active {{
    background: var(--accent);
    color: white;
    opacity: 1;
    border-color: var(--accent);
}}

.filter-group input[type="text"] {{
    width: 100%;
    padding: 8px 12px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--bg);
    color: var(--text);
    font-size: 12px;
    outline: none;
    font-family: var(--font);
    transition: border-color 0.2s;
}}

.filter-group input[type="text"]:focus {{
    border-color: var(--accent);
}}

.filter-group input[type="text"]::placeholder {{
    opacity: 0.3;
}}

.filter-group .btn-group {{
    display: flex;
    gap: 6px;
    margin-top: 8px;
}}

.filter-group .btn-group button {{
    flex: 1;
    padding: 7px;
    border: none;
    border-radius: var(--radius);
    cursor: pointer;
    font-size: 11px;
    font-weight: 600;
    font-family: var(--font);
    transition: all 0.2s;
}}

.filter-group .btn-group .btn-primary {{
    background: var(--accent);
    color: white;
}}

.filter-group .btn-group .btn-primary:hover {{
    background: var(--accent-hover);
}}

.filter-group .btn-group .btn-secondary {{
    background: var(--bg);
    color: var(--text);
    border: 1px solid var(--border);
}}

.filter-group .btn-group .btn-secondary:hover {{
    background: var(--border);
}}

.filter-group .estado-filtro {{
    font-size: 10px;
    color: var(--text);
    opacity: 0.35;
    margin-top: 6px;
}}

/* ===== CONTROLES DEL MAPA ===== */
.map-controls {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}}

.map-controls .control-btn {{
    flex: 1;
    min-width: 40px;
    padding: 8px 12px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--bg);
    color: var(--text);
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    font-family: var(--font);
    text-align: center;
}}

.map-controls .control-btn:hover {{
    background: var(--border);
}}

.map-controls .control-btn.primary {{
    background: var(--accent);
    color: white;
    border-color: var(--accent);
}}

.map-controls .control-btn.primary:hover {{
    background: var(--accent-hover);
}}

/* ===== MAPA ===== */
#map-container {{
    position: fixed;
    top: var(--header-height);
    left: var(--sidebar-width);
    right: 0;
    bottom: var(--bottom-height);
    transition: left 0.3s ease;
    background: var(--bg);
}}

#map-container.expanded {{
    left: 0;
}}

#map {{
    width: 100%;
    height: 100%;
    background: #e8ecf0;
}}

/* ===== OCULTAR CONTROLES NATIVOS DE LEAFLET ===== */
.leaflet-control-zoom {{
    display: none !important;
}}
.leaflet-control-layers {{
    display: none !important;
}}
.leaflet-control-measure {{
    display: none !important;
}}
.leaflet-control-scale {{
    display: none !important;
}}
.leaflet-draw-toolbar {{
    display: none !important;
}}
.leaflet-draw-section {{
    display: none !important;
}}

/* ===== TOGGLE SIDEBAR ===== */
#toggleSidebar {{
    position: fixed;
    top: calc(var(--header-height) + 10px);
    left: calc(var(--sidebar-width) + 10px);
    z-index: 9997;
    background: var(--sidebar);
    border: 1px solid var(--border);
    border-radius: 50%;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: var(--shadow);
    font-size: 12px;
    transition: all 0.3s;
    color: var(--text);
    font-family: var(--font);
    border: none;
}}

#toggleSidebar:hover {{
    transform: scale(1.05);
    background: var(--border);
}}

#toggleSidebar.shifted {{
    left: 10px;
}}

/* ===== BOTTOM BAR ===== */
#bottom-bar {{
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: var(--bottom-height);
    background: var(--sidebar);
    border-top: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    padding: 0 16px;
    z-index: 9996;
}}

#bottom-bar button {{
    background: none;
    border: none;
    color: var(--text);
    opacity: 0.4;
    padding: 6px 14px;
    border-radius: var(--radius);
    font-size: 11px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    font-family: var(--font);
}}

#bottom-bar button:hover {{
    opacity: 0.8;
    background: var(--bg);
}}

#bottom-bar button.primary {{
    background: var(--accent);
    color: white;
    opacity: 1;
}}

#bottom-bar button.primary:hover {{
    background: var(--accent-hover);
    opacity: 1;
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
    #toggleSidebar {{
        left: 10px;
    }}
}}
</style>
</head>
<body>

<!-- HEADER -->
<header id="header">
    <div class="logo">Programa Cordoba 25/26 <span>PRO</span></div>
    <div class="actions">
        <button onclick="toggleTheme()" id="themeToggle">Modo</button>
        <button onclick="toggleSidebar()">Panel</button>
    </div>
</header>

<!-- SIDEBAR -->
<div id="sidebar">
    <!-- Estadísticas -->
    <div class="section">
        <div class="section-title">Datos generales</div>
        <div class="stats-grid">
            <div class="stat-card"><div class="num">{total_poligonos}</div><div class="label">Lotes</div></div>
            <div class="stat-card"><div class="num">{total_hectareas:,.0f}</div><div class="label">Hectareas</div></div>
            <div class="stat-card"><div class="num" id="totalFotos">0</div><div class="label">Fotos</div></div>
            <div class="stat-card"><div class="num">{total_zonas}</div><div class="label">Zonas</div></div>
        </div>
    </div>
    
    <!-- Superficie por cultivo -->
    <div class="section">
        <div class="section-title">Superficie por cultivo</div>
        <div class="stats-list">
            {cultivos_panel_html}
            <div class="stat-total">
                <span>Total</span>
                <span>{total_hectareas:,.0f} ha</span>
            </div>
        </div>
    </div>
    
    <!-- Filtros -->
    <div class="section">
        <div class="section-title">Filtros</div>
        
        <div class="filter-group">
            <label>Cliente</label>
            <input list="clientesList" id="clienteInput" placeholder="Escribe o selecciona un cliente...">
            <datalist id="clientesList">{opciones_clientes}</datalist>
            <div class="btn-group">
                <button class="btn-primary" onclick="aplicarFiltros()">Aplicar</button>
                <button class="btn-secondary" onclick="resetearFiltros()">Resetear</button>
            </div>
            <div class="estado-filtro" id="estadoFiltroCliente">Mostrando todos los lotes</div>
        </div>
        
        <div class="filter-group">
            <label>Cultivo</label>
            <div class="checkbox-group" id="cultivoFilters">
                {checkboxes_cultivos}
            </div>
            <div class="btn-group">
                <button class="btn-primary" onclick="aplicarFiltros()">Aplicar</button>
                <button class="btn-secondary" onclick="resetearFiltros()">Resetear</button>
            </div>
            <div class="estado-filtro" id="estadoFiltroCultivo">Todos los cultivos</div>
        </div>
    </div>
    
    <!-- Controles del mapa -->
    <div class="section">
        <div class="section-title">Controles</div>
        <div class="map-controls">
            <button onclick="zoomIn()" class="control-btn">+</button>
            <button onclick="zoomOut()" class="control-btn">-</button>
            <button onclick="toggleMedicion()" class="control-btn">Medir</button>
            <button onclick="toggleCapas()" class="control-btn">Capas</button>
        </div>
    </div>
</div>

<!-- MAPA -->
<div id="map-container">
    <div id="map"></div>
</div>

<!-- TOGGLE SIDEBAR -->
<button id="toggleSidebar" onclick="toggleSidebar()">◀</button>

<!-- BOTTOM BAR -->
<div id="bottom-bar">
    <button onclick="toggleSidebar()">Panel</button>
    <button onclick="toggleTheme()" id="themeBtn">Modo</button>
</div>

<!-- PANTALLA DE LOGIN -->
<div id="loginScreen" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: linear-gradient(135deg, #2C5530 0%, #8A9A5B 100%);
        z-index: 10000; display: flex; flex-direction: column;
        justify-content: center; align-items: center;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        transition: opacity 0.5s ease;">
    <div style="background: rgba(255, 255, 255, 0.95); padding: 30px 25px;
            border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center; max-width: 320px; width: 90%;
            backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);">
        <div style="margin-bottom: 20px;">
            <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #2C5530, #8A9A5B);
                    border-radius: 15px; display: flex; align-items: center; justify-content: center;
                    margin: 0 auto 12px; box-shadow: 0 4px 15px rgba(44, 85, 48, 0.3);">
                <span style="color: white; font-size: 28px;">🔐</span>
            </div>
            <h2 style="color: #2C5530; margin-bottom: 5px; font-weight: 800; font-size: 18px;">
                PROGRAMA CÓRDOBA 25/26
            </h2>
        </div>
        <div style="margin-bottom: 20px; text-align: left;">
            <div style="margin-bottom: 15px;">
                <label style="display: block; margin-bottom: 6px; font-weight: 600; color: #2C5530; font-size: 12px;">👤 Usuario</label>
                <input type="text" id="loginUsuario" placeholder="Ingrese su usuario"
                       style="width: 100%; padding: 12px 14px; border: 2px solid rgba(212, 212, 212, 0.8);
                              border-radius: 10px; font-size: 14px; background: white; color: #2C2C2C;
                              box-sizing: border-box;">
            </div>
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 6px; font-weight: 600; color: #2C5530; font-size: 12px;">🔒 Contraseña</label>
                <input type="password" id="loginContrasena" placeholder="Ingrese su contraseña"
                       style="width: 100%; padding: 12px 14px; border: 2px solid rgba(212, 212, 212, 0.8);
                              border-radius: 10px; font-size: 14px; background: white; color: #2C2C2C;
                              box-sizing: border-box;">
            </div>
            <button onclick="verificarAcceso()"
                    style="width: 100%; background: linear-gradient(135deg, #2C5530, #8A9A5B);
                           color: white; border: none; padding: 14px; border-radius: 10px;
                           font-size: 15px; font-weight: 700; cursor: pointer;
                           transition: all 0.3s; display: flex; align-items: center;
                           justify-content: center; gap: 8px;">
                <span>🔓</span><span>INGRESAR</span>
            </button>
        </div>
        <div id="loginError" style="margin-top: 15px; color: #f44336; font-size: 12px;
                font-weight: 600; display: none; padding: 10px; background: rgba(244, 67, 54, 0.1);
                border-radius: 6px; border-left: 4px solid #f44336;">
            ❌ Usuario o contraseña incorrectos
        </div>
    </div>
</div>

<script>
// ============================================================
//  DATOS
// ============================================================
const geojsonData = {geojson_str};

// ============================================================
//  INICIALIZAR MAPA
// ============================================================
const map = L.map('map', {{
    center: [{center[0]}, {center[1]}],
    zoom: 11,
    zoomControl: false  // Sin controles de zoom nativos
}});

// Capa base (OpenStreetMap)
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution: '© OpenStreetMap',
    maxZoom: 19
}}).addTo(map);

// ============================================================
//  VARIABLES GLOBALES
// ============================================================
let capaPoligonos = null;
let drawnItems = null;
let drawControl = null;
let modoMedicion = false;
let capaSatelite = null;
let capaVisible = true;

// ============================================================
//  COLORES POR CULTIVO (VERDE SOJA, AMARILLO MAÍZ)
// ============================================================
function getColor(cultivo) {{
    if (!cultivo) return '#9C27B0';  // Default púrpura
    
    const cultivoLower = cultivo.toLowerCase();
    if (cultivoLower.includes('soja') || cultivoLower.includes('soya')) {{
        return '#4CAF50';  // Verde para Soja
    }} else if (cultivoLower.includes('maíz') || cultivoLower.includes('maiz') || cultivoLower.includes('corn')) {{
        return '#FFC107';  // Amarillo para Maíz
    }} else if (cultivoLower.includes('trigo') || cultivoLower.includes('wheat')) {{
        return '#795548';  // Marrón para Trigo
    }} else if (cultivoLower.includes('girasol') || cultivoLower.includes('sunflower')) {{
        return '#FF9800';  // Naranja para Girasol
    }} else if (cultivoLower.includes('algodón') || cultivoLower.includes('algodon') || cultivoLower.includes('cotton')) {{
        return '#2196F3';  // Azul para Algodón
    }} else if (cultivoLower.includes('sorgo') || cultivoLower.includes('sorghum')) {{
        return '#E91E63';  // Rosa para Sorgo
    }}
    return '#9C27B0';  // Default púrpura
}}

// ============================================================
//  CARGAR POLÍGONOS
// ============================================================
function cargarPoligonos() {{
    if (capaPoligonos) {{
        map.removeLayer(capaPoligonos);
    }}
    
    capaPoligonos = L.geoJSON(geojsonData, {{
        style: function(feature) {{
            const cultivo = feature.properties.CULTIVO || '';
            const color = getColor(cultivo);
            return {{
                fillColor: color,
                color: '#2E7D32',
                weight: 2,
                fillOpacity: 0.6,
                opacity: 1
            }};
        }},
        onEachFeature: function(feature, layer) {{
            const props = feature.properties;
            const cultivo = props.CULTIVO || 'Sin cultivo';
            const cliente = props.CLIENTE || 'Sin cliente';
            const hectareas = props.HECTAREAS_ASEGURADAS || 'N/A';
            
            // Tooltip
            layer.bindTooltip(`
                <strong>${{cultivo}}</strong><br>
                Cliente: ${{cliente}}<br>
                Ha: ${{hectareas}}
            `, {{ permanent: false, direction: 'top' }});
            
            // Popup
            layer.on('click', function(e) {{
                L.popup()
                    .setLatLng(e.latlng)
                    .setContent(`
                        <strong>${{cultivo}}</strong><br>
                        Cliente: ${{cliente}}<br>
                        Hectáreas: ${{hectareas}}
                    `)
                    .openOn(map);
            }});
        }}
    }}).addTo(map);
    
    // Ajustar vista
    const bounds = capaPoligonos.getBounds();
    if (bounds.isValid()) {{
        map.fitBounds(bounds, {{ padding: [50, 50] }});
    }}
}}

// ============================================================
//  CONTROLES DEL MAPA (desde sidebar)
// ============================================================
function zoomIn() {{
    map.zoomIn();
}}

function zoomOut() {{
    map.zoomOut();
}}

function toggleMedicion() {{
    if (!drawControl) {{
        drawnItems = new L.FeatureGroup();
        map.addLayer(drawnItems);
        
        drawControl = new L.Control.Draw({{
            position: 'topright',
            draw: {{
                polygon: true,
                polyline: true,
                rectangle: true,
                circle: false,
                marker: false,
                circlemarker: false
            }},
            edit: {{
                featureGroup: drawnItems,
                remove: true
            }}
        }});
        map.addControl(drawControl);
        
        map.on(L.Draw.Event.CREATED, function(event) {{
            const layer = event.layer;
            drawnItems.addLayer(layer);
            
            if (layer.getArea) {{
                const area = layer.getArea();
                const hectareas = area / 10000;
                alert('Área: ' + hectareas.toFixed(2) + ' ha');
            }}
        }});
        
        // Cambiar texto del botón
        document.querySelector('button[onclick="toggleMedicion()"]').textContent = 'Detener';
    }} else {{
        map.removeControl(drawControl);
        map.removeLayer(drawnItems);
        drawControl = null;
        drawnItems = null;
        document.querySelector('button[onclick="toggleMedicion()"]').textContent = 'Medir';
    }}
}}

function toggleCapas() {{
    // Alternar visibilidad de los polígonos
    if (capaPoligonos) {{
        if (capaVisible) {{
            map.removeLayer(capaPoligonos);
            capaVisible = false;
            document.querySelector('button[onclick="toggleCapas()"]').textContent = 'Mostrar';
        }} else {{
            map.addLayer(capaPoligonos);
            capaVisible = true;
            document.querySelector('button[onclick="toggleCapas()"]').textContent = 'Capas';
        }}
    }}
}}

// ============================================================
//  FILTROS
// ============================================================
function aplicarFiltros() {{
    const clienteValor = document.getElementById('clienteInput').value.toLowerCase().trim();
    const cultivosSeleccionados = [];
    document.querySelectorAll('#cultivoFilters input:checked').forEach(el => {{
        cultivosSeleccionados.push(el.value);
    }});
    
    if (!capaPoligonos) return;
    
    let contador = 0;
    let bounds = null;
    
    capaPoligonos.eachLayer(function(layer) {{
        const props = layer.feature.properties;
        const cliente = (props.CLIENTE || '').toLowerCase();
        const cultivo = (props.CULTIVO || '').toUpperCase();
        
        const coincideCliente = !clienteValor || cliente.includes(clienteValor);
        const coincideCultivo = cultivosSeleccionados.length === 0 || cultivosSeleccionados.includes(cultivo);
        
        if (coincideCliente && coincideCultivo) {{
            layer.setStyle({{
                opacity: 1,
                fillOpacity: 0.8,
                weight: 3,
                color: '#FF5722'
            }});
            contador++;
            if (layer.getBounds && layer.getBounds().isValid()) {{
                bounds = bounds ? bounds.extend(layer.getBounds()) : layer.getBounds();
            }}
        }} else {{
            layer.setStyle({{
                opacity: 0,
                fillOpacity: 0
            }});
        }}
    }});
    
    if (contador > 0 && bounds) {{
        map.fitBounds(bounds, {{ padding: [50, 50] }});
    }}
    
    document.getElementById('estadoFiltroCliente').innerHTML = 'Mostrando ' + contador + ' lotes';
    document.getElementById('estadoFiltroCultivo').innerHTML = contador + ' lotes encontrados';
}}

function resetearFiltros() {{
    document.getElementById('clienteInput').value = '';
    document.querySelectorAll('#cultivoFilters input').forEach(el => {{
        el.checked = true;
        el.closest('label').classList.add('active');
    }});
    
    if (capaPoligonos) {{
        capaPoligonos.eachLayer(function(layer) {{
            const cultivo = layer.feature.properties.CULTIVO || '';
            const color = getColor(cultivo);
            layer.setStyle({{
                fillColor: color,
                color: '#2E7D32',
                weight: 2,
                fillOpacity: 0.6,
                opacity: 1
            }});
        }});
        
        const bounds = capaPoligonos.getBounds();
        if (bounds.isValid()) {{
            map.fitBounds(bounds, {{ padding: [50, 50] }});
        }}
    }}
    
    document.getElementById('estadoFiltroCliente').innerHTML = 'Mostrando todos los lotes';
    document.getElementById('estadoFiltroCultivo').innerHTML = 'Todos los cultivos';
}}

// ============================================================
//  CHECKBOXES
// ============================================================
document.querySelectorAll('#cultivoFilters input').forEach(el => {{
    el.addEventListener('change', function() {{
        const label = this.closest('label');
        if (this.checked) label.classList.add('active');
        else label.classList.remove('active');
    }});
}});

document.getElementById('clienteInput').addEventListener('keypress', function(e) {{
    if (e.key === 'Enter') aplicarFiltros();
}});

// ============================================================
//  TOGGLES
// ============================================================
let sidebarOpen = true;
let darkMode = false;

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
    document.getElementById('themeToggle').textContent = darkMode ? 'Claro' : 'Oscuro';
    document.getElementById('themeBtn').textContent = darkMode ? 'Claro' : 'Oscuro';
    setTimeout(() => map.invalidateSize(), 100);
}}

// ============================================================
//  LOGIN
// ============================================================
const HASH_USUARIO_VALIDO = "{HASH_USUARIO}";
const HASH_CONTRASENA_VALIDA = "{HASH_CONTRASENA}";

async function calcularHash(texto) {{
    const salt = "ProgramaCordoba25/26-SancorSeguro";
    const encoder = new TextEncoder();
    const data = encoder.encode(texto + salt);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex.substring(0, 16);
}}

async function verificarAcceso() {{
    const usuario = document.getElementById('loginUsuario').value.trim();
    const contrasena = document.getElementById('loginContrasena').value.trim();
    const errorDiv = document.getElementById('loginError');
    
    if (!usuario || !contrasena) {{
        errorDiv.innerHTML = '❌ Por favor, complete ambos campos';
        errorDiv.style.display = 'block';
        return;
    }}
    
    try {{
        const hashUsuarioIngresado = await calcularHash(usuario);
        const hashContrasenaIngresada = await calcularHash(contrasena);
        
        if (hashUsuarioIngresado === HASH_USUARIO_VALIDO &&
            hashContrasenaIngresada === HASH_CONTRASENA_VALIDA) {{
            document.getElementById('loginScreen').style.opacity = '0';
            setTimeout(function() {{
                document.getElementById('loginScreen').style.display = 'none';
            }}, 500);
        }} else {{
            errorDiv.innerHTML = '❌ Usuario o contraseña incorrectos';
            errorDiv.style.display = 'block';
            document.getElementById('loginContrasena').value = '';
            document.getElementById('loginContrasena').focus();
        }}
    }} catch (error) {{
        errorDiv.innerHTML = '❌ Error al verificar credenciales';
        errorDiv.style.display = 'block';
    }}
}}

document.getElementById('loginUsuario').addEventListener('keypress', function(e) {{
    if (e.key === 'Enter') document.getElementById('loginContrasena').focus();
}});

document.getElementById('loginContrasena').addEventListener('keypress', function(e) {{
    if (e.key === 'Enter') verificarAcceso();
}});

// ============================================================
//  INICIAR
// ============================================================
document.addEventListener('DOMContentLoaded', function() {{
    cargarPoligonos();
    setTimeout(() => document.getElementById('loginUsuario').focus(), 500);
}});
</script>

</body>
</html>
'''

    # ===== GUARDAR ARCHIVO =====
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_completo)
    
    print(f"✅ Aplicación Leaflet puro guardada como: {output_file}")
    return output_file

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("❌ Uso: python generar_app_html_identico.py <ruta_al_geojson> [nombre_salida]")
        print("   Ejemplo: python generar_app_html_identico.py geojson_unificado_actual.geojson app_leaflet.html")
        sys.exit(1)
    
    ruta_geojson = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = "app_leaflet.html"
    
    if not os.path.exists(ruta_geojson):
        print(f"❌ El archivo {ruta_geojson} no existe")
        sys.exit(1)
    
    try:
        geojson_data, gdf = cargar_geojson(ruta_geojson)
        campos = encontrar_campos(gdf)
        print("\n✅ Campos encontrados:")
        for nombre, campo in campos.items():
            if campo:
                print(f"   • {nombre}: '{campo}'")
        
        crear_app_leaflet(geojson_data, gdf, campos, output_file)
        
        print(f"\n{'='*80}")
        print("🎉 APLICACIÓN LEAFLET PURO GENERADA EXITOSAMENTE")
        print(f"{'='*80}")
        print(f"📁 Archivo: {output_file}")
        print(f"📊 Polígonos: {len(gdf)}")
        print(f"🔐 Credenciales: {USUARIO_CORRECTO} / {CONTRASENA_CORRECTA}")
        print(f"\n🌐 Para usar: Abre {output_file} en cualquier navegador")
        print(f"📋 Funcionalidades:")
        print(f"   ✅ Login seguro")
        print(f"   ✅ Colores: Verde para Soja, Amarillo para Maíz")
        print(f"   ✅ Controles en sidebar (Zoom, Medición, Capas)")
        print(f"   ✅ Filtros combinados (Cliente + Cultivo)")
        print(f"   ✅ Modo oscuro/claro")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
