#!/usr/bin/env python3
"""
GENERADOR AUTOMÁTICO DE APLICACIÓN HTML
Versión para GitHub Actions - NO usa Colab
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

print("🔐🌽🌱 GENERADOR DE APLICACIÓN WEB AUTOMÁTICO - PROGRAMA CÓRDOBA 25/26")
print("=" * 80)

# 🔐 CREDENCIALES DE ACCESO
USUARIO_CORRECTO = "Sancor"
CONTRASENA_CORRECTA = "2025Sancor"

def generar_hash_seguro(texto):
    """Genera hash SHA-256 con salt para mayor seguridad"""
    salt = "ProgramaCordoba25/26-SancorSeguro"
    hash_obj = hashlib.sha256(f"{texto}{salt}".encode())
    return hash_obj.hexdigest()[:16]

HASH_USUARIO = generar_hash_seguro(USUARIO_CORRECTO)
HASH_CONTRASENA = generar_hash_seguro(CONTRASENA_CORRECTA)

def cargar_geojson(ruta_geojson):
    """Carga un archivo GeoJSON"""
    print(f"📖 Cargando {ruta_geojson}...")
    with open(ruta_geojson, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
    gdf.crs = "EPSG:4326"
    
    print(f"✅ GeoJSON cargado: {len(gdf)} polígonos")
    return geojson_data, gdf

def encontrar_campos(gdf):
    """Encuentra campos clave automáticamente"""
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

    # Siniestros
    campo_causa_stro = None
    for campo in ['CAUSA_STRO', 'CAUSA_SINIESTRO', 'CAUSA', 'causa_stro']:
        if campo in gdf.columns:
            campo_causa_stro = campo
            break

    return {
        'cultivo': campo_cultivo,
        'hectareas': campo_hectareas,
        'cliente': campo_cliente,
        'zona': campo_zona,
        'causa_stro': campo_causa_stro
    }

def calcular_estadisticas(gdf, campos):
    """Calcula estadísticas importantes"""
    estadisticas = {}
    
    if campos['hectareas']:
        gdf[campos['hectareas']] = pd.to_numeric(gdf[campos['hectareas']], errors='coerce').fillna(0)
    
    # Superficie por cultivo
    if campos['cultivo'] and campos['hectareas']:
        superficie_por_cultivo = {}
        for cultivo in gdf[campos['cultivo']].dropna().unique():
            mascara = gdf[campos['cultivo']] == cultivo
            hectareas = gdf.loc[mascara, campos['hectareas']].sum()
            superficie_por_cultivo[cultivo] = hectareas
        
        estadisticas['superficie_por_cultivo'] = superficie_por_cultivo
        estadisticas['total_superficie'] = sum(superficie_por_cultivo.values())
    
    # Hectáreas por zona
    if campos['zona'] and campos['hectareas']:
        gdf[campos['zona']] = gdf[campos['zona']].astype(str).str.strip()
        hectareas_por_zona = {}
        for zona in gdf[campos['zona']].dropna().unique():
            zona_str = str(zona).strip()
            mascara = gdf[campos['zona']] == zona_str
            hectareas = gdf.loc[mascara, campos['hectareas']].sum()
            hectareas_por_zona[zona_str] = hectareas
        
        estadisticas['hectareas_por_zona'] = hectareas_por_zona
    
    # Clientes
    if campos['cliente']:
        clientes_unicos = sorted(gdf[campos['cliente']].dropna().unique())
        estadisticas['clientes'] = clientes_unicos
    
    return estadisticas

def crear_mapa(geojson_data, gdf, campos, estadisticas, output_file):
    """Crea el mapa HTML con todas las funcionalidades"""
    
    print(f"\n🗺️ Creando aplicación web: {output_file}")
    
    # Centro del mapa
    if not gdf.empty:
        minx, miny, maxx, maxy = gdf.total_bounds
        bounds = [[miny, minx], [maxy, maxx]]
        center = [(miny + maxy) / 2, (minx + maxx) / 2]
    else:
        center = [-31.4201, -64.1888]
        bounds = [[center[0]-0.1, center[1]-0.1], [center[0]+0.1, center[1]+0.1]]

    # Crear mapa base
    m = folium.Map(
        location=center,
        zoom_start=11,
        control_scale=True,
        tiles=None,
        zoom_control=True
    )

    # ========== CAPAS BASE ==========
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='🌍 Google Satélite',
        max_zoom=20,
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google',
        name='🗺️ Google Híbrido',
        max_zoom=20,
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        attr='© CartoDB',
        name='🌙 Modo oscuro',
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attr='© OpenStreetMap',
        name='🌐 OpenStreetMap',
        overlay=False,
        control=True
    ).add_to(m)

    # ========== ESTILOS ==========
    def estilo_por_cultivo(feature):
        propiedades = feature['properties']
        color_relleno = '#9C27B0'
        color_borde = '#7B1FA2'

        if campos['cultivo'] and campos['cultivo'] in propiedades:
            cultivo = str(propiedades[campos['cultivo']]).lower()
            if 'soja' in cultivo or 'soya' in cultivo:
                color_relleno, color_borde = '#4CAF50', '#2E7D32'
            elif 'maíz' in cultivo or 'maiz' in cultivo or 'corn' in cultivo:
                color_relleno, color_borde = '#FFC107', '#FF8F00'
            elif 'trigo' in cultivo or 'wheat' in cultivo:
                color_relleno, color_borde = '#795548', '#5D4037'
            elif 'girasol' in cultivo or 'sunflower' in cultivo:
                color_relleno, color_borde = '#FF9800', '#EF6C00'
            elif 'algodón' in cultivo or 'algodon' in cultivo or 'cotton' in cultivo:
                color_relleno, color_borde = '#2196F3', '#1976D2'
            elif 'sorgo' in cultivo or 'sorghum' in cultivo:
                color_relleno, color_borde = '#E91E63', '#C2185B'

        feature['properties']['_color_fill'] = color_relleno
        feature['properties']['_color_border'] = color_borde

        return {
            'fillColor': color_relleno,
            'color': color_borde,
            'weight': 2,
            'fillOpacity': 0.6,
            'dashArray': '5, 5'
        }

    # ========== CAPA PRINCIPAL ==========
    campos_tooltip = []
    if campos['cliente']:
        campos_tooltip = [campos['cliente']]
    elif campos['cultivo']:
        campos_tooltip = [campos['cultivo']]
    else:
        campos_tooltip = ['excel_fila_num']

    geo_layer = folium.GeoJson(
        geojson_data,
        name='Lotes asegurados',
        style_function=estilo_por_cultivo,
        tooltip=folium.GeoJsonTooltip(
            fields=campos_tooltip,
            aliases=[f"{campo}" for campo in campos_tooltip],
            localize=True,
            sticky=True,
            style="""
                font-family: Arial, sans-serif;
                font-size: 11px;
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #4CAF50;
                border-radius: 3px;
                padding: 5px;
            """
        )
    ).add_to(m)

    capa_nombre = geo_layer.get_name()

    # ========== CONTROLES ==========
    folium.LayerControl(position='topright', collapsed=True).add_to(m)
    Fullscreen(
        position='topright',
        title='Pantalla completa',
        title_cancel='Salir pantalla completa'
    ).add_to(m)
    MeasureControl(position='topright').add_to(m)

    # ========== GPS ==========
    try:
        LocateControl(
            position='topright',
            drawCircle=True,
            follow=True,
            showPopup=True,
            keepCurrentZoomLevel=False,
            initialZoom=15,
            strings={
                'title': 'Mi ubicación actual',
                'popup': 'Tu ubicación: {distance} {unit} desde aquí',
                'metersUnit': 'metros',
                'feetUnit': 'pies'
            }
        ).add_to(m)
        print("✅ 📍 Geolocalización configurada")
    except Exception as e:
        print(f"⚠️  Error GPS: {e}")

    # ========== TÍTULO ==========
    titulo_html = f'''
    <div style="position: fixed;
            top: 8px; left: 8px;
            background: linear-gradient(135deg, #2C5530, #8A9A5B);
            padding: 6px 10px;
            border-radius: 8px;
            z-index: 9999;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 10px;
            box-shadow: 0 3px 10px rgba(44, 85, 48, 0.3);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);">
        
        <div style="font-weight: 800; color: white; font-size: 12px; letter-spacing: -0.2px;">
            PROGRAMA CÓRDOBA 25/26 - DATOS AUTOMÁTICOS
        </div>
        <div style="font-size: 9px; color: rgba(255, 255, 255, 0.9); margin-top: 1px;">
            Actualizado: {datetime.now().strftime("%d/%m/%Y %H:%M")} • {len(gdf)} polígonos
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(titulo_html))

    # ========== LEYENDA DE CULTIVOS ==========
    if 'superficie_por_cultivo' in estadisticas:
        hectareas_soja = sum(hect for cultivo, hect in estadisticas['superficie_por_cultivo'].items() 
                           if 'soja' in str(cultivo).lower() or 'soya' in str(cultivo).lower())
        hectareas_maiz = sum(hect for cultivo, hect in estadisticas['superficie_por_cultivo'].items() 
                           if 'maíz' in str(cultivo).lower() or 'maiz' in str(cultivo).lower() or 'corn' in str(cultivo).lower())
        
        items_leyenda = []
        if hectareas_soja > 0:
            items_leyenda.append(f'''
                <div style="display: flex; align-items: center; margin-bottom: 6px; padding: 6px; border-radius: 6px; background: rgba(76, 175, 80, 0.1);">
                    <div style="display: flex; align-items: center; justify-content: center; width: 24px; height: 24px; background: #4CAF50; margin-right: 8px; border-radius: 6px; flex-shrink: 0;">
                        <span style="color: white; font-size: 10px;">🟢</span>
                    </div>
                    <div style="flex: 1;">
                        <div style="font-size: 10px; font-weight: 700; color: #2C2C2C;">SOJA</div>
                        <div style="font-size: 11px; font-weight: 800; color: #2C5530;">{hectareas_soja:,.0f} ha</div>
                    </div>
                </div>
            ''')
        
        if hectareas_maiz > 0:
            items_leyenda.append(f'''
                <div style="display: flex; align-items: center; margin-bottom: 6px; padding: 6px; border-radius: 6px; background: rgba(255, 193, 7, 0.1);">
                    <div style="display: flex; align-items: center; justify-content: center; width: 24px; height: 24px; background: #FFC107; margin-right: 8px; border-radius: 6px; flex-shrink: 0;">
                        <span style="color: white; font-size: 10px;">🟡</span>
                    </div>
                    <div style="flex: 1;">
                        <div style="font-size: 10px; font-weight: 700; color: #2C2C2C;">MAÍZ</div>
                        <div style="font-size: 11px; font-weight: 800; color: #2C5530;">{hectareas_maiz:,.0f} ha</div>
                    </div>
                </div>
            ''')
        
        if 'total_superficie' in estadisticas:
            items_leyenda.append(f'''
                <div style="margin-top: 8px; padding: 8px; background: linear-gradient(135deg, #2C5530, #8A9A5B); border-radius: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 10px;">
                        <div style="font-weight: 700; color: white;">TOTAL</div>
                        <div style="font-size: 12px; font-weight: 800; color: white;">{estadisticas['total_superficie']:,.0f} ha</div>
                    </div>
                </div>
            ''')
        
        leyenda_html = f'''
        <div style="position: fixed;
                bottom: 8px; right: 8px;
                background: white;
                padding: 10px;
                border-radius: 10px;
                border: 1px solid rgba(212, 212, 212, 0.8);
                z-index: 9999;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 11px;
                width: 160px;
                max-height: 250px;
                overflow-y: auto;
                box-shadow: 0 3px 15px rgba(44, 85, 48, 0.15);">
            
            {"".join(items_leyenda)}
        </div>
        '''
        m.get_root().html.add_child(folium.Element(leyenda_html))

    # ========== BUSCADOR DE CLIENTES ==========
    if campos['cliente'] and 'clientes' in estadisticas:
        buscador_html = f'''
        <div id="lupitaBuscador" style="position: fixed;
                top: 80px; left: 8px;
                background: linear-gradient(135deg, rgba(250, 249, 246, 0.95) 0%, rgba(245, 245, 240, 0.95) 100%);
                padding: 10px 12px;
                border-radius: 12px;
                border: 1px solid rgba(212, 212, 212, 0.8);
                z-index: 9998;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 11px;
                width: 220px;
                box-shadow: 0 5px 20px rgba(44, 85, 48, 0.12);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);">

            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div style="display: flex; align-items: center; gap: 6px;">
                    <div style="width: 28px; height: 28px; background: linear-gradient(135deg, #2C5530, #8A9A5B);
                            border-radius: 6px; display: flex; align-items: center; justify-content: center;">
                        <span style="color: white; font-size: 12px;">🔍</span>
                    </div>
                    <div style="font-weight: 700; color: #2C5530; font-size: 12px;">
                        Buscar cliente
                    </div>
                </div>
                <button id="toggleBuscador"
                        style="background: rgba(44, 85, 48, 0.1); 
                               border: none; 
                               cursor: pointer; 
                               font-size: 14px; 
                               color: #2C5530;
                               width: 24px;
                               height: 24px;
                               border-radius: 6px;
                               display: flex;
                               align-items: center;
                               justify-content: center;"
                        onclick="toggleBuscador()">↻</button>
            </div>

            <div id="contenidoBuscador">
                <div style="margin-bottom: 10px;">
                    <input list="clientesList"
                           id="clienteInput"
                           placeholder="🔍 Escribe o selecciona cliente..."
                           style="width: 100%; 
                                  padding: 8px 10px;
                                  border: 2px solid rgba(212, 212, 212, 0.8);
                                  border-radius: 8px;
                                  font-size: 11px;
                                  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                                  background: white;
                                  color: #2C2C2C;">
                    <datalist id="clientesList">
                        {"".join(f'<option value="{cliente}">' for cliente in estadisticas['clientes'])}
                    </datalist>
                </div>

                <div style="display: flex; gap: 6px; margin-bottom: 8px;">
                    <button onclick="filtrarCliente()"
                            style="flex: 1; 
                                   background: linear-gradient(135deg, #2C5530, #8A9A5B);
                                   color: white;
                                   border: none;
                                   padding: 8px;
                                   border-radius: 8px;
                                   cursor: pointer;
                                   font-size: 10px;
                                   font-weight: 600;">
                        <span>✓</span>
                        <span>Filtrar</span>
                    </button>
    
                    <button onclick="resetearFiltro()"
                            style="flex: 1; 
                                   background: linear-gradient(135deg, #FAF9F6, #F5F5F0);
                                   color: #666;
                                   border: 2px solid rgba(212, 212, 212, 0.8);
                                   padding: 8px;
                                   border-radius: 8px;
                                   cursor: pointer;
                                   font-size: 10px;
                                   font-weight: 600;">
                        <span>↺</span>
                        <span>Resetear</span>
                    </button>
                </div>

                <div id="estadoFiltro"
                     style="font-size: 9px; 
                            color: #666; 
                            margin-top: 10px;
                            padding: 8px;
                            background: rgba(44, 85, 48, 0.05);
                            border-radius: 6px;
                            border-left: 4px solid #8A9A5B;
                            display: flex;
                            align-items: center;
                            gap: 6px;">
                    <div style="width: 6px; height: 6px; background: #2C5530; border-radius: 50%;"></div>
                    <div>Mostrando <span style="font-weight: 700; color: #2C5530;">{len(gdf)}</span> polígonos</div>
                </div>
            </div>
        </div>

        <script>
        // Variables globales
        var boundsGeneral = {capa_nombre}.getBounds();
        var contenidoVisible = true;

        function toggleBuscador() {{
            var contenido = document.getElementById("contenidoBuscador");
            var toggleBtn = document.getElementById("toggleBuscador");
            var lupita = document.getElementById("lupitaBuscador");

            if (contenidoVisible) {{
                contenido.style.display = "none";
                toggleBtn.innerHTML = "▼";
                lupita.style.width = "140px";
                lupita.style.padding = "6px 8px";
            }} else {{
                contenido.style.display = "block";
                toggleBtn.innerHTML = "↻";
                lupita.style.width = "220px";
                lupita.style.padding = "10px 12px";
            }}
            contenidoVisible = !contenidoVisible;
        }}

        function filtrarCliente() {{
            var valor = document.getElementById("clienteInput").value.toLowerCase();
            if (!valor) {{
                alert("Por favor, escribe o selecciona un cliente");
                return;
            }}

            var boundsFiltrados = null;
            var contador = 0;

            {capa_nombre}.eachLayer(function(layer) {{
                var propiedades = layer.feature.properties;
                var clienteEnPoligono = propiedades["{campos['cliente']}"];

                if (clienteEnPoligono && clienteEnPoligono.toString().toLowerCase().includes(valor)) {{
                    layer.setStyle({{
                        fillOpacity: 0.6,
                        weight: 2,
                        opacity: 1
                    }});
                    layer.options.interactive = true;
                    
                    var layerBounds = layer.getBounds();
                    if (layerBounds) {{
                        if (!boundsFiltrados) {{
                            boundsFiltrados = layerBounds;
                        }} else {{
                            boundsFiltrados = boundsFiltrados.extend(layerBounds);
                        }}
                    }}
                    contador++;
                }} else {{
                    layer.setStyle({{
                        fillOpacity: 0,
                        weight: 0,
                        opacity: 0
                    }});
                    layer.options.interactive = false;
                }}
            }});

            var estadoDiv = document.getElementById("estadoFiltro");
            if (contador > 0) {{
                estadoDiv.innerHTML = "Mostrando " + contador + " polígonos";
                estadoDiv.style.color = "#4CAF50";
                if (boundsFiltrados) {{
                    map.fitBounds(boundsFiltrados, {{padding: [50, 50]}});
                }}
            }} else {{
                estadoDiv.innerHTML = "❌ No se encontraron";
                estadoDiv.style.color = "#f44336";
            }}
        }}

        function resetearFiltro() {{
            document.getElementById("clienteInput").value = "";
            {capa_nombre}.eachLayer(function(layer) {{
                layer.setStyle({{
                    fillColor: layer.feature.properties._color_fill || '#9C27B0',
                    color: layer.feature.properties._color_border || '#7B1FA2',
                    weight: 2,
                    fillOpacity: 0.6,
                    opacity: 1
                }});
                layer.options.interactive = true;
            }});
            
            var estadoDiv = document.getElementById("estadoFiltro");
            estadoDiv.innerHTML = "Mostrando todos ({len(gdf)})";
            estadoDiv.style.color = "#666";
            
            if (boundsGeneral && boundsGeneral.isValid()) {{
                map.fitBounds(boundsGeneral);
            }}
        }}

        document.getElementById("clienteInput").addEventListener("keypress", function(e) {{
            if (e.key === "Enter") {{
                filtrarCliente();
            }}
        }});
        </script>
        '''
        m.get_root().html.add_child(folium.Element(buscador_html))

    # ========== PANTALLA DE LOGIN ==========
    login_html = f'''
    <div id="loginScreen" style="position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: linear-gradient(135deg, #2C5530 0%, #8A9A5B 100%);
            z-index: 10000;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            transition: opacity 0.5s ease;">

        <div style="background: rgba(255, 255, 255, 0.95);
                    padding: 30px 25px;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    text-align: center;
                    max-width: 320px;
                    width: 90%;
                    backdrop-filter: blur(15px);
                    -webkit-backdrop-filter: blur(15px);">

            <!-- LOGO -->
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

            <!-- FORMULARIO -->
            <div style="margin-bottom: 20px; text-align: left;">
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 6px; font-weight: 600; color: #2C5530; font-size: 12px;">
                        👤 Usuario
                    </label>
                    <input type="text" id="loginUsuario"
                           placeholder="Ingrese su usuario"
                           style="width: 100%; padding: 12px 14px;
                                  border: 2px solid rgba(212, 212, 212, 0.8);
                                  border-radius: 10px;
                                  font-size: 14px;
                                  background: white;
                                  color: #2C2C2C;
                                  box-sizing: border-box;">
                </div>

                <div style="margin-bottom: 20px;">
                    <label style="display: block; margin-bottom: 6px; font-weight: 600; color: #2C5530; font-size: 12px;">
                        🔒 Contraseña
                    </label>
                    <input type="password" id="loginContrasena"
                           placeholder="Ingrese su contraseña"
                           style="width: 100%; padding: 12px 14px;
                                  border: 2px solid rgba(212, 212, 212, 0.8);
                                  border-radius: 10px;
                                  font-size: 14px;
                                  background: white;
                                  color: #2C2C2C;
                                  box-sizing: border-box;">
                </div>

                <button onclick="verificarAcceso()"
                        style="width: 100%;
                               background: linear-gradient(135deg, #2C5530, #8A9A5B);
                               color: white;
                               border: none;
                               padding: 14px;
                               border-radius: 10px;
                               font-size: 15px;
                               font-weight: 700;
                               cursor: pointer;
                               transition: all 0.3s;
                               display: flex;
                               align-items: center;
                               justify-content: center;
                               gap: 8px;"
                        onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(44, 85, 48, 0.4)';"
                        onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
                    <span>🔓</span>
                    <span>INGRESAR</span>
                </button>
            </div>

            <!-- MENSAJE DE ERROR -->
            <div id="loginError"
                 style="margin-top: 15px;
                        color: #f44336;
                        font-size: 12px;
                        font-weight: 600;
                        display: none;
                        padding: 10px;
                        background: rgba(244, 67, 54, 0.1);
                        border-radius: 6px;
                        border-left: 4px solid #f44336;">
                ❌ Usuario o contraseña incorrectos
            </div>
        </div>
    </div>

    <script>
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
        const usuario = document.getElementById("loginUsuario").value.trim();
        const contrasena = document.getElementById("loginContrasena").value.trim();
        const errorDiv = document.getElementById("loginError");

        if (!usuario || !contrasena) {{
            errorDiv.innerHTML = "❌ Por favor, complete ambos campos";
            errorDiv.style.display = "block";
            return;
        }}

        try {{
            const hashUsuarioIngresado = await calcularHash(usuario);
            const hashContrasenaIngresada = await calcularHash(contrasena);

            if (hashUsuarioIngresado === HASH_USUARIO_VALIDO &&
                hashContrasenaIngresada === HASH_CONTRASENA_VALIDA) {{

                document.getElementById("loginScreen").style.opacity = "0";
                setTimeout(function() {{
                    document.getElementById("loginScreen").style.display = "none";
                    if (document.getElementById("lupitaBuscador")) {{
                        document.getElementById("lupitaBuscador").style.display = "block";
                    }}
                    map.getContainer().style.pointerEvents = "auto";
                }}, 500);

            }} else {{
                errorDiv.innerHTML = "❌ Usuario o contraseña incorrectos";
                errorDiv.style.display = "block";
                document.getElementById("loginContrasena").value = "";
                document.getElementById("loginContrasena").focus();
            }}
        }} catch (error) {{
            errorDiv.innerHTML = "❌ Error al verificar credenciales";
            errorDiv.style.display = "block";
        }}
    }}

    document.getElementById("loginUsuario").addEventListener("keypress", function(e) {{
        if (e.key === "Enter") {{
            document.getElementById("loginContrasena").focus();
        }}
    }});

    document.getElementById("loginContrasena").addEventListener("keypress", function(e) {{
        if (e.key === "Enter") {{
            verificarAcceso();
        }}
    }});

    document.addEventListener("DOMContentLoaded", function() {{
        map.getContainer().style.pointerEvents = "none";
        if (document.getElementById("lupitaBuscador")) {{
            document.getElementById("lupitaBuscador").style.display = "none";
        }}
        setTimeout(() => {{
            document.getElementById("loginUsuario").focus();
        }}, 500);
    }});
    </script>
    '''
    m.get_root().html.add_child(folium.Element(login_html))

    # ========== GUARDAR ARCHIVO ==========
    m.save(output_file)
    print(f"✅ Aplicación guardada como: {output_file}")
    
    return output_file

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("❌ Uso: python generar_app_html.py <ruta_al_geojson> [nombre_salida]")
        print("   Ejemplo: python generar_app_html.py geojson_unificado_actual.geojson app_cordoba.html")
        sys.exit(1)
    
    ruta_geojson = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = "app_cordoba_actual.html"
    
    if not os.path.exists(ruta_geojson):
        print(f"❌ El archivo {ruta_geojson} no existe")
        sys.exit(1)
    
    try:
        # 1. Cargar datos
        geojson_data, gdf = cargar_geojson(ruta_geojson)
        
        # 2. Encontrar campos
        campos = encontrar_campos(gdf)
        print("\n✅ Campos encontrados:")
        for nombre, campo in campos.items():
            if campo:
                print(f"   • {nombre}: '{campo}'")
        
        # 3. Calcular estadísticas
        estadisticas = calcular_estadisticas(gdf, campos)
        
        # 4. Crear mapa
        crear_mapa(geojson_data, gdf, campos, estadisticas, output_file)
        
        print(f"\n{'='*80}")
        print("🎉 APLICACIÓN GENERADA EXITOSAMENTE")
        print(f"{'='*80}")
        print(f"📁 Archivo: {output_file}")
        print(f"📊 Polígonos: {len(gdf)}")
        if 'total_superficie' in estadisticas:
            print(f"🌾 Superficie total: {estadisticas['total_superficie']:,.0f} ha")
        print(f"🔐 Credenciales: {USUARIO_CORRECTO} / **********")
        print(f"\n🌐 Para usar: Abre {output_file} en cualquier navegador")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
