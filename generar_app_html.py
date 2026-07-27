#!/usr/bin/env python3
"""
GENERADOR DE APLICACIÓN WEB - VERSIÓN PRO
Basado en el código original que funciona
Agrega: Interfaz renovada, filtro de cultivos, modo oscuro
Mantiene: Buscador de clientes, capas, fotos, siniestros, WMS, etc.
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

print("🔐🌽🌱 GENERADOR DE APLICACIÓN WEB - VERSIÓN PRO")
print("=" * 80)

# ========== CREDENCIALES ==========
USUARIO_CORRECTO = os.environ.get("MULTIRIESGO_USER")
CONTRASENA_CORRECTA = os.environ.get("MULTIRIESGO_PASS")

if not USUARIO_CORRECTO or not CONTRASENA_CORRECTA:
    print("⚠️  ADVERTENCIA: No se encontraron credenciales en variables de entorno")
    print("   Usando valores por defecto (solo para desarrollo)")
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

def agregar_elemento_html_seguro(mapa, html_content):
    try:
        from branca.element import Element
        element = Element(html_content)
        mapa.get_root().html.add_child(element)
        return True
    except Exception as e:
        print(f"⚠️  Error agregando HTML (branca): {e}")
        try:
            mapa.get_root().html.add_child(folium.Element(html_content))
            return True
        except Exception as e2:
            print(f"❌ Error crítico: {e2}")
            return False

def crear_app_pro(geojson_data, gdf, campos, output_file):
    print(f"\n🗺️ Creando aplicación web PRO: {output_file}")
    
    if not gdf.empty:
        minx, miny, maxx, maxy = gdf.total_bounds
        bounds = [[miny, minx], [maxy, maxx]]
        center = [(miny + maxy) / 2, (minx + maxx) / 2]
    else:
        center = [-31.4201, -64.1888]
        bounds = [[center[0]-0.1, center[1]-0.1], [center[0]+0.1, center[1]+0.1]]

    m = folium.Map(
        location=center,
        zoom_start=11,
        control_scale=True,
        tiles=None,
        zoom_control=True
    )

    # ========== CAPAS BASE ==========
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='🛰️ Esri Satélite',
        max_zoom=19,
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
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='🌙 Esri Dark Gray',
        max_zoom=16,
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='🗺️ Esri Standard',
        max_zoom=19,
        overlay=False,
        control=True
    ).add_to(m)

    # ========== ESTILOS POR CULTIVO (IDÉNTICO A TU ORIGINAL) ==========
    def estilo_por_cultivo(feature):
        propiedades = feature['properties']
        color_relleno = '#9C27B0'
        color_borde = '#7B1FA2'

        if campos['cultivo'] and campos['cultivo'] in propiedades:
            cultivo = str(propiedades[campos['cultivo']]).lower()
            if 'soja' in cultivo or 'soya' in cultivo:
                color_relleno = '#4CAF50'
                color_borde = '#2E7D32'
            elif 'maíz' in cultivo or 'maiz' in cultivo or 'corn' in cultivo:
                color_relleno = '#FFC107'
                color_borde = '#FF8F00'
            elif 'trigo' in cultivo or 'wheat' in cultivo:
                color_relleno = '#795548'
                color_borde = '#5D4037'
            elif 'girasol' in cultivo or 'sunflower' in cultivo:
                color_relleno = '#FF9800'
                color_borde = '#EF6C00'
            elif 'algodón' in cultivo or 'algodon' in cultivo or 'cotton' in cultivo:
                color_relleno = '#2196F3'
                color_borde = '#1976D2'
            elif 'sorgo' in cultivo or 'sorghum' in cultivo:
                color_relleno = '#E91E63'
                color_borde = '#C2185B'

        feature['properties']['_color_fill'] = color_relleno
        feature['properties']['_color_border'] = color_borde

        return {
            'fillColor': color_relleno,
            'color': color_borde,
            'weight': 2,
            'fillOpacity': 0.6,
            'dashArray': '5, 5'
        }

    def highlight_function(feature):
        return {
            'fillColor': '#FF5722',
            'color': '#D84315',
            'weight': 3,
            'fillOpacity': 0.8,
            'dashArray': '5, 5'
        }

    # ========== ESTILOS PARA SINIESTROS ==========
    def estilo_por_causa_siniestro(feature):
        propiedades = feature['properties']
        causa = propiedades.get(campos['causa_stro'], '').upper() if campos['causa_stro'] else ''

        colores_causa = {
            'GRANIZO': ('#00BCD4', '#0097A7'),
            'SEQUÍA': ('#FF5252', '#D50000'),
            'SEQUIA': ('#FF5252', '#D50000'),
            'INUNDACIÓN': ('#448AFF', '#2979FF'),
            'INUNDACION': ('#448AFF', '#2979FF'),
            'VIENTO': ('#7C4DFF', '#651FFF'),
            'INCENDIO': ('#795548', '#5D4037'),
            'HELADA': ('#FFFFFF', '#E0E0E0'),
        }
        
        if causa in colores_causa:
            fill_color, border_color = colores_causa[causa]
        else:
            fill_color, border_color = '#9C27B0', '#7B1FA2'

        feature['properties']['_color_fill_siniestro'] = fill_color
        feature['properties']['_color_border_siniestro'] = border_color

        return {
            'fillColor': fill_color,
            'color': border_color,
            'weight': 3,
            'fillOpacity': 0.7,
            'dashArray': '3, 3'
        }

    def highlight_function_siniestros(feature):
        return {
            'fillColor': '#FF5722',
            'color': '#D84315',
            'weight': 4,
            'fillOpacity': 0.9,
            'dashArray': '3, 3'
        }

    # ========== CAMPOS PARA POPUP ==========
    campos_especificos = [
        'CUIT', 'CLIENTE', 'CAMPO', 'DEPARTAMENTO', 'LOCALIDAD', 'CULTIVO', 'LOTE',
        'CULTIVO_ANTERIOR', 'RENDIMIENTO_ANTERIOR', 'HECTAREAS_DECLARADAS',
        'HECTAREAS_ASEGURADAS', 'PORCENTAJE_ASEGURADO', 'ZONA_CZ4',
        'RENDIMIENTO_ASEGURADO', 'SUMA_ASEGURADA', 'FECHA_SIEMBRA'
    ]

    campos_existentes = [campo for campo in campos_especificos if campo in gdf.columns]
    campos_numericos = [col for col in gdf.columns if pd.api.types.is_numeric_dtype(gdf[col])]
    otros_campos = [campo for campo in campos_numericos if campo not in campos_existentes and 'HECTAREAS' in campo]
    campos_para_popup = campos_existentes + otros_campos[:5]

    campos_tooltip = []
    if campos['cliente'] and campos['cliente'] in gdf.columns:
        campos_tooltip = [campos['cliente']]
    elif campos['cultivo'] and campos['cultivo'] in gdf.columns:
        campos_tooltip = [campos['cultivo']]
    else:
        campos_tooltip = ['excel_fila_num']

    # ========== CAPA PRINCIPAL (IDÉNTICA) ==========
    geo_layer = folium.GeoJson(
        geojson_data,
        name='Lotes asegurados',
        style_function=estilo_por_cultivo,
        highlight_function=highlight_function,
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
        ),
        popup=folium.GeoJsonPopup(
            fields=campos_para_popup,
            aliases=[f"<b>{col}</b>" for col in campos_para_popup],
            localize=True,
            labels=True,
            style="""
                font-family: Arial, sans-serif;
                font-size: 11px;
                max-height: 400px;
                overflow-y: auto;
                max-width: 350px;
                padding: 10px;
                background-color: #f8f9fa;
                border: 2px solid #4CAF50;
                border-radius: 5px;
            """
        )
    ).add_to(m)

    capa_nombre = geo_layer.get_name()

    # ========== CAPA DE FOTOS DESDE GITHUB (IDÉNTICA) ==========
    print("📸 Configurando capa de fotos desde GitHub...")
    
    GITHUB_USER = "franciscotomatis"
    REPO_NAME = "APP-CBA-2027"
    FOTOS_JSON_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/fotos_metadata/fotos_procesadas.json"

    print(f"✅ Fotos se cargarán desde: {FOTOS_JSON_URL}")

    # ========== OBTENER DATOS PARA LA INTERFAZ ==========
    total_poligonos = len(gdf)
    total_hectareas = gdf[campos.get('hectareas', 'HECTAREAS_ASEGURADAS')].sum() if campos.get('hectareas') else 0
    
    cultivos_unicos = []
    if campos['cultivo'] and campos['cultivo'] in gdf.columns:
        cultivos_unicos = sorted(gdf[campos['cultivo']].dropna().unique())
    cultivos_js = json.dumps([str(c) for c in cultivos_unicos])
    
    # ========== HTML Y JAVASCRIPT DE FOTOS (IDÉNTICO A TU ORIGINAL) ==========
    fotos_html = f'''
    <div id="contenedorFotosGithub">
        <div id="cargandoFotos" style="position: fixed;
                top: 120px; right: 20px;
                background: rgba(244, 67, 54, 0.9);
                color: white;
                padding: 8px 12px;
                border-radius: 8px;
                z-index: 10000;
                font-family: Arial, sans-serif;
                font-size: 11px;
                display: none;
                box-shadow: 0 3px 10px rgba(244, 67, 54, 0.3);
                border: 1px solid #D32F2F;
                min-width: 160px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="width: 24px; height: 24px; background: rgba(255, 255, 255, 0.3); 
                        border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                    <span style="font-size: 12px; animation: spin 1s linear infinite;">⏳</span>
                </div>
                <div>
                    <div style="font-weight: bold; font-size: 12px;">Cargando fotos...</div>
                </div>
            </div>
        </div>
    </div>

    <style>
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>

    <script>
    var capaFotosGithub = null;
    var fotosCargadas = false;
    var cargandoFotos = false;
    var capaVisible = false;

    function crearPopupFotoGithub(feature) {{
        var props = feature.properties || {{}};
        var nombre = props.NOMBRE_FOTO || "Foto del perito";
        var metodo = props.METODO || "Desconocido";
        var imgUrl = props.IMAGEN_URL || props.IMAGEN || "";
        
        var html = `
        <div style="font-family: Arial, sans-serif; max-width: 500px; min-width: 300px;">
            <div style="background: linear-gradient(135deg, #F44336, #D32F2F); 
                        color: white; padding: 12px; border-radius: 8px 8px 0 0;
                        text-align: center;">
                <div style="font-size: 14px; font-weight: bold;">📸 ${{nombre}}</div>
                <div style="font-size: 10px; opacity: 0.9; margin-top: 3px;">${{metodo}}</div>
            </div>
            
            <div style="padding: 15px; text-align: center; background: #FFF3F2;">
                <img src="${{imgUrl}}" 
                    style="max-width: 100%; max-height: 350px; 
                            border-radius: 6px; border: 2px solid #F44336;
                            box-shadow: 0 3px 10px rgba(0,0,0,0.15);
                            cursor: pointer;"
                    onclick="this.style.maxHeight='none'; this.style.cursor='default';"
                    title="Click para ampliar la foto">
            </div>
            
            <div style="padding: 8px; background: #f9f9f9; border-radius: 0 0 8px 8px;
                        border-top: 1px solid #eee; font-size: 10px; color: #666;">
                <div style="text-align: center;">
                    📍 Foto geolocalizada • 👤 Perito en campo
                </div>
                <div style="margin-top: 5px; text-align: center; font-size: 9px;">
                    Click en la foto para ampliar • Programa Córdoba 25/26
                </div>
            </div>
        </div>
        `;
        
        return L.popup({{
            maxWidth: 550,
            minWidth: 320
        }}).setContent(html);
    }}

    async function cargarFotosDesdeGithub() {{
        if (fotosCargadas || cargandoFotos) return;
        
        cargandoFotos = true;
        var cargandoDiv = document.getElementById("cargandoFotos");
        if (cargandoDiv) cargandoDiv.style.display = "block";
        
        console.log("📸 Cargando fotos desde GitHub...");
        
        try {{
            const response = await fetch("{FOTOS_JSON_URL}");
            
            if (!response.ok) {{
                throw new Error(`Error HTTP: ${{response.status}}`);
            }}
            
            const fotosData = await response.json();
            const features = fotosData.features || [];
            
            console.log(`✅ ${{features.length}} fotos cargadas`);
            
            capaFotosGithub = L.geoJSON(features, {{
                pointToLayer: function(feature, latlng) {{
                    var marker = L.circleMarker(latlng, {{
                        radius: 8,
                        fillColor: "#F44336",
                        color: "#FFFFFF",
                        weight: 2,
                        opacity: 1,
                        fillOpacity: 0.9
                    }});
                    marker.options.zIndexOffset = 1000;
                    return marker;
                }},
                onEachFeature: function(feature, layer) {{
                    var nombre = feature.properties.NOMBRE_FOTO || "Foto";
                    layer.bindTooltip(`📸 ${{nombre}}`, {{
                        sticky: true,
                        direction: 'top',
                        className: 'foto-tooltip',
                        opacity: 0.9
                    }});
                    layer.bindPopup(crearPopupFotoGithub(feature));
                }}
            }});
            
            function agregarCapaAlMapa() {{
                console.log("🔍 Buscando mapa...");
                
                var mapaActual = null;
                
                if (typeof window.map !== "undefined" && window.map !== null) {{
                    mapaActual = window.map;
                    console.log("✅ Mapa encontrado: window.map");
                }}
                else {{
                    for (var key in window) {{
                        try {{
                            var obj = window[key];
                            if (obj && 
                                typeof obj.addLayer === "function" && 
                                typeof obj.fitBounds === "function") {{
                                mapaActual = obj;
                                console.log("✅ Mapa encontrado: window." + key);
                                break;
                            }}
                        }} catch(e) {{
                            // Ignorar errores
                        }}
                    }}
                }}
                
                if (mapaActual && typeof mapaActual.addLayer === "function") {{
                    try {{
                        mapaActual.addLayer(capaFotosGithub);
                        console.log("✅ Capa de fotos agregada");
                        fotosCargadas = true;
                        capaVisible = true;
                        capaFotosGithub.bringToFront();
                        return true;
                    }} catch (error) {{
                        console.error("❌ Error:", error);
                        return false;
                    }}
                }} else {{
                    console.warn("⚠️ Reintentando...");
                    setTimeout(agregarCapaAlMapa, 500);
                    return false;
                }}
            }}

            agregarCapaAlMapa();
            
        }} catch (error) {{
            console.error("❌ Error cargando fotos:", error);
            var cargandoDiv = document.getElementById("cargandoFotos");
            if (cargandoDiv) {{
                cargandoDiv.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 24px; height: 24px; background: rgba(255, 0, 0, 0.2); 
                            border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 12px; color: #FF0000;">❌</span>
                    </div>
                    <div style="font-size: 11px;">Error cargando fotos</div>
                </div>
                `;
            }}
        }} finally {{
            cargandoFotos = false;
            setTimeout(function() {{
                var cargandoDiv = document.getElementById("cargandoFotos");
                if (cargandoDiv) cargandoDiv.style.display = "none";
            }}, 2000);
        }}
    }}

    function toggleFotos(mostrar) {{
        if (!capaFotosGithub) return;
        capaVisible = mostrar;
        if (mostrar) {{
            capaFotosGithub.setStyle({{
                opacity: 1,
                fillOpacity: 0.9
            }});
            capaFotosGithub.bringToFront();
            console.log("✅ Fotos mostradas (ARRIBA)");
        }} else {{
            capaFotosGithub.setStyle({{
                opacity: 0,
                fillOpacity: 0
            }});
            console.log("✅ Fotos ocultadas");
        }}
    }}

    function configurarDeteccionFotos() {{
        function buscarCheckbox() {{
            var checkboxes = document.querySelectorAll('input[type="checkbox"]');
            for (var i = 0; i < checkboxes.length; i++) {{
                var checkbox = checkboxes[i];
                var label = checkbox.parentElement;
                if (label && label.textContent && label.textContent.includes("📸 Fotos del perito")) {{
                    console.log("✅ Checkbox de fotos encontrado");
                    checkbox.addEventListener("change", function() {{
                        console.log("🔄 Checkbox cambiado:", this.checked);
                        if (this.checked) {{
                            if (!fotosCargadas) {{
                                cargarFotosDesdeGithub();
                            }} else {{
                                toggleFotos(true);
                            }}
                        }} else {{
                            toggleFotos(false);
                        }}
                    }});
                    return true;
                }}
            }}
            return false;
        }}
        
        var intentos = 0;
        function intentarBuscar() {{
            if (buscarCheckbox()) {{
                console.log("✅ Sistema de fotos configurado");
            }} else {{
                intentos++;
                if (intentos < 5) {{
                    setTimeout(intentarBuscar, 1000);
                }} else {{
                    console.warn("⚠️ No se encontró el checkbox de fotos");
                }}
            }}
        }}
        intentarBuscar();
    }}

    document.addEventListener("DOMContentLoaded", configurarDeteccionFotos);
    if (typeof window.map !== "undefined") {{
        window.map.whenReady(configurarDeteccionFotos);
    }}
    </script>
    '''

    fotos_layer = folium.FeatureGroup(name='📸 Fotos del perito', show=True)
    fotos_layer.add_to(m)
    agregar_elemento_html_seguro(m, fotos_html)

    print("✅ Sistema de carga de fotos desde GitHub configurado")

    # ========== CAPA DE SINIESTROS (IDÉNTICA) ==========
    if campos['causa_stro'] and gdf[campos['causa_stro']].notna().any():
        print("✅ Encontrados datos de siniestros")
        
        siniestros_features = []
        for feature in geojson_data['features']:
            if feature['properties'].get(campos['causa_stro']):
                siniestros_features.append(feature)

        if siniestros_features:
            siniestros_data = {
                "type": "FeatureCollection",
                "features": siniestros_features
            }

            print(f"✅ {len(siniestros_features)} polígonos con siniestros")

            campos_siniestros_popup = [campos['causa_stro']]
            aliases_siniestros = ['<b>Causa del siniestro</b>']
            
            if campos['fecha_stro']:
                campos_siniestros_popup.append(campos['fecha_stro'])
                aliases_siniestros.append('<b>Fecha del siniestro</b>')
                
            if campos['dano_stro']:
                campos_siniestros_popup.append(campos['dano_stro'])
                aliases_siniestros.append('<b>Daño estimado</b>')
            
            campos_siniestros_popup.extend(campos_para_popup[:5])
            aliases_siniestros.extend([f"<b>{col}</b>" for col in campos_para_popup[:5]])

            siniestros_layer = folium.GeoJson(
                siniestros_data,
                name='⚠️ Siniestros',
                style_function=estilo_por_causa_siniestro,
                highlight_function=highlight_function_siniestros,
                tooltip=folium.GeoJsonTooltip(
                    fields=[campos['causa_stro']] + campos_tooltip[:3],
                    aliases=['Causa'] + [f"{campo}" for campo in campos_tooltip[:3]],
                    localize=True,
                    sticky=True,
                    style="""
                        font-family: Arial, sans-serif;
                        font-size: 11px;
                        background-color: rgba(255, 255, 255, 0.95);
                        border: 2px solid #F44336;
                        border-radius: 3px;
                        padding: 5px;
                    """
                ),
                popup=folium.GeoJsonPopup(
                    fields=campos_siniestros_popup,
                    aliases=aliases_siniestros,
                    localize=True,
                    labels=True,
                    style="""
                        font-family: Arial, sans-serif;
                        font-size: 11px;
                        max-height: 400px;
                        overflow-y: auto;
                        max-width: 350px;
                        padding: 10px;
                        background-color: #ffebee;
                        border: 2px solid #F44336;
                        border-radius: 5px;
                    """
                ),
                show=False
            ).add_to(m)

    # ========== CAPAS WMS (IDÉNTICAS) ==========
    print("\n📡 AGREGANDO CAPAS WMS")
    print("="*60)

    try:
        url_wms = "https://geoservicios2.conae.gov.ar/geoserver/PrecipitacionAcumulada/wms"
        wms = WebMapService(url_wms, version='1.3.0')
        
        capas_wms = ['MOM_GPMIMERG_PA1D_1', 'MOM_GPMIMERG_PA1D_2', 'MOM_GPMIMERG_PA1D_3']
        opacidades = [0.7, 0.6, 0.5]
        
        for i, capa_nombre_wms in enumerate(capas_wms):
            if capa_nombre_wms in wms.contents:
                capa_info = wms[capa_nombre_wms]
                titulo = capa_info.title
                fecha_match = re.search(r'(\d{4}-\d{2}-\d{2})|(\d{2}/\d{2}/\d{4})', titulo)
                
                if fecha_match:
                    fecha_str = fecha_match.group(0)
                    try:
                        if '-' in fecha_str:
                            fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d')
                        else:
                            fecha_dt = datetime.strptime(fecha_str, '%d/%m/%Y')
                        fecha_formateada = fecha_dt.strftime('%d/%m')
                    except:
                        fecha_formateada = fecha_str
                    
                    nombre_display = f'🌧️ PP {fecha_formateada}'
                else:
                    nombre_display = f'🌧️ PP Día {i+1}'
                
                folium.WmsTileLayer(
                    url=url_wms,
                    name=nombre_display,
                    layers=capa_nombre_wms,
                    fmt='image/png',
                    transparent=True,
                    opacity=opacidades[i],
                    overlay=True,
                    control=True,
                    show=False
                ).add_to(m)
                print(f"✅ {nombre_display}")
    except Exception as e:
        print(f"⚠️ Error IMERG: {e}")

    try:
        print("\n💧 Agregando capa de Humedad de Suelo CONAE...")
        url_wms = "https://geoservicios3.conae.gov.ar/geoserver/HumedadDeSuelos/wms"
        nombre_capa = "HumedadDeSuelos:DSS_MSMKR_1"
        nombre_display = "💧 Humedad Suelo (primeros 50 cm)"
        folium.WmsTileLayer(
            url=url_wms,
            name=nombre_display,
            layers=nombre_capa,
            fmt='image/png',
            transparent=True,
            opacity=0.65,
            overlay=True,
            control=True,
            show=False
        ).add_to(m)
        print(f"✅ {nombre_display} agregada")
    except Exception as e:
        print(f"⚠️ Error Humedad Suelo: {e}")

    try:
        url_wms = "https://aplicaciones.gulich.unc.edu.ar/geoserver/ows"
        wms = WebMapService(url_wms, version='1.3.0')
        
        config_capas = [
            {
                "nombre": "tvdi_m_2024:tvdi_2026009_modis",
                "simbolo": "📊",
                "nombre_display": "TVDI",
                "opacidad": 0.75
            },
            {
                "nombre": "tvdi_anomsindex_m_2024:anomtvdi_2026009_anomindex_modis",
                "simbolo": "🟡", 
                "nombre_display": "Anomalía TVDI",
                "opacidad": 0.75
            }
        ]
        
        for config in config_capas:
            nombre_capa = config["nombre"]
            simbolo = config["simbolo"]
            nombre_base = config["nombre_display"]
            
            if nombre_capa in wms.contents:
                match = re.search(r'(\d{4})(\d{3})', nombre_capa)
                if match:
                    año = match.group(1)
                    dia_año = int(match.group(2))
                    nombre_mostrar = f"{simbolo} {nombre_base} {año}-Día{dia_año}"
                else:
                    nombre_mostrar = f"{simbolo} {nombre_base}"
                
                folium.WmsTileLayer(
                    url=url_wms,
                    name=nombre_mostrar,
                    layers=nombre_capa,
                    fmt='image/png',
                    transparent=True,
                    opacity=config["opacidad"],
                    overlay=True,
                    control=True,
                    show=False,
                    styles='',
                    version='1.3.0'
                ).add_to(m)
                print(f"✅ {nombre_mostrar}")
    except Exception as e:
        print(f"⚠️ Error TVDI: {e}")

    # ========== INTERFAZ PRO (AGREGADO - NO TOCA LOS DATOS) ==========
    from datetime import datetime, timezone, timedelta
    hora_argentina = datetime.now(timezone(timedelta(hours=-3)))
    fecha_hora_argentina = hora_argentina.strftime("%d/%m/%Y • %H:%M")
    
    # Generar checkboxes de cultivos
    checkboxes_html = ""
    for cultivo in cultivos_unicos:
        cultivo_str = str(cultivo).upper()
        icono = '🌱' if 'SOJA' in cultivo_str else '🌽' if 'MAÍZ' in cultivo_str else '🌾' if 'TRIGO' in cultivo_str else '🌻' if 'GIRASOL' in cultivo_str else '📦'
        checkboxes_html += f'<label class="active"><input type="checkbox" value="{cultivo_str}" checked><span>{icono} {cultivo_str.capitalize()}</span></label>'
    
    # Obtener clientes
    clientes_unicos = []
    if campos['cliente'] and campos['cliente'] in gdf.columns:
        clientes_unicos = sorted(gdf[campos['cliente']].dropna().astype(str).unique())
    
    opciones_clientes = "".join(f'<option value="{cliente}">' for cliente in clientes_unicos)
    
    total_zonas = len(gdf[campos['zona']].dropna().unique()) if campos['zona'] else 0
    
    interfaz_pro_html = f'''
    <!-- ===== INTERFAZ PRO ===== -->
    <style>
    :root {{
        --bg: #f0f2f5;
        --sidebar: #1a2332;
        --sidebar-text: #e0e4ea;
        --card: #ffffff;
        --text: #1a2332;
        --border: #e2e8f0;
        --shadow: 0 4px 20px rgba(0,0,0,0.1);
        --header-height: 56px;
        --bottom-height: 48px;
    }}
    
    [data-theme="dark"] {{
        --bg: #0d1117;
        --sidebar: #161b22;
        --sidebar-text: #c9d1d9;
        --card: #1c2333;
        --text: #e6edf3;
        --border: #30363d;
        --shadow: 0 4px 20px rgba(0,0,0,0.4);
    }}
    
    #header {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: var(--header-height);
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
    
    #sidebar {{
        position: fixed;
        top: var(--header-height);
        left: 0;
        bottom: var(--bottom-height);
        width: 320px;
        background: var(--sidebar);
        color: var(--sidebar-text);
        z-index: 9998;
        overflow-y: auto;
        padding: 16px;
        transition: transform 0.3s ease;
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
    
    #map-container {{
        position: fixed;
        top: var(--header-height);
        left: 320px;
        right: 0;
        bottom: var(--bottom-height);
        transition: left 0.3s ease;
    }}
    
    #map-container.expanded {{
        left: 0;
    }}
    
    #map {{
        width: 100%;
        height: 100%;
    }}
    
    #toggleSidebar {{
        position: fixed;
        top: calc(var(--header-height) + 10px);
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
    
    #bottom-bar {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: var(--bottom-height);
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
        #toggleSidebar {{
            left: 10px;
        }}
    }}
    </style>
    
    <header id="header">
        <div class="logo">🌽 PROGRAMA CÓRDOBA 25/26 <span>PRO</span></div>
        <div class="search">
            <input type="text" id="searchInput" placeholder="🔍 Buscar cliente, campo, localidad..." oninput="buscarGlobal(this.value)">
        </div>
        <div class="actions">
            <button onclick="toggleTheme()" id="themeToggle" title="Modo nocturno">🌙</button>
            <button onclick="toggleSidebar()" title="Panel lateral">☰</button>
            <button onclick="abrirSubirFoto()" title="Subir foto">📸</button>
        </div>
    </header>
    
    <div id="sidebar">
        <div class="section">
            <div class="section-title">📊 Datos Generales</div>
            <div class="stats-grid">
                <div class="stat-card"><div class="num">{total_poligonos}</div><div class="label">Lotes</div></div>
                <div class="stat-card"><div class="num">{total_hectareas:,.0f}</div><div class="label">Hectáreas</div></div>
                <div class="stat-card"><div class="num" id="totalFotos">0</div><div class="label">Fotos</div></div>
                <div class="stat-card"><div class="num">{total_zonas}</div><div class="label">Zonas</div></div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">🌱 Filtro por Cultivo</div>
            <div class="filter-group">
                <div class="checkbox-group" id="cultivoFilters">
                    {checkboxes_html}
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">🔍 Buscar Cliente</div>
            <div class="filter-group">
                <input list="clientesList" id="clienteInput" placeholder="🔍 Escribe o selecciona cliente..."
                       style="width:100%;padding:8px 12px;border:none;border-radius:8px;background:rgba(255,255,255,0.08);color:white;font-size:13px;outline:none;">
                <datalist id="clientesList">{opciones_clientes}</datalist>
                <div style="display:flex;gap:6px;margin-top:8px;">
                    <button onclick="filtrarCliente()" style="flex:1;padding:8px;background:#2d7d46;border:none;border-radius:8px;color:white;cursor:pointer;font-size:12px;font-weight:600;">✓ Filtrar</button>
                    <button onclick="resetearFiltro()" style="flex:1;padding:8px;background:rgba(255,255,255,0.06);border:none;border-radius:8px;color:rgba(255,255,255,0.6);cursor:pointer;font-size:12px;">↺ Resetear</button>
                </div>
                <div id="estadoFiltro" style="font-size:10px;color:rgba(255,255,255,0.5);margin-top:6px;">Mostrando {total_poligonos} polígonos</div>
            </div>
        </div>
    </div>
    
    <div id="map-container">
        <div id="map"></div>
    </div>
    
    <button id="toggleSidebar" onclick="toggleSidebar()">◀</button>
    
    <div id="bottom-bar">
        <button onclick="toggleSidebar()">☰ Panel</button>
        <button onclick="toggleTheme()" id="themeBtn">🌙 Nocturno</button>
        <button onclick="abrirSubirFoto()">📸 Subir foto</button>
    </div>
    
    <script>
    // ============================================================
    // FUNCIONES DE LA INTERFAZ PRO
    // ============================================================
    
    let sidebarOpen = true;
    let darkMode = false;
    let capaPoligonos = null;
    
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
    
    // ============================================================
    // OBTENER CAPA DE POLÍGONOS (la misma que usa el buscador original)
    // ============================================================
    
    function obtenerCapaPoligonos() {{
        if (capaPoligonos) return capaPoligonos;
        
        // Buscar la capa de polígonos que creó Folium
        if (typeof map !== 'undefined') {{
            for (var key in map._layers) {{
                var layer = map._layers[key];
                if (layer && typeof layer.eachLayer === 'function') {{
                    var count = 0;
                    layer.eachLayer(function() {{ count++; }});
                    if (count > 1000) {{
                        console.log("✅ Capa de polígonos encontrada:", count, "polígonos");
                        capaPoligonos = layer;
                        return layer;
                    }}
                }}
            }}
        }}
        console.warn("⚠️ No se encontró la capa de polígonos");
        return null;
    }}
    
    // ============================================================
    // FILTRO DE CULTIVOS (FUNCIONAL)
    // ============================================================
    
    function aplicarFiltroCultivos() {{
        var seleccionados = [];
        document.querySelectorAll('#cultivoFilters input:checked').forEach(function(el) {{
            seleccionados.push(el.value);
        }});
        
        console.log("🌱 Filtrando por cultivos:", seleccionados);
        
        var capa = obtenerCapaPoligonos();
        if (!capa) return;
        
        if (seleccionados.length === 0) {{
            capa.eachLayer(function(layer) {{
                layer.setStyle({{ opacity: 1, fillOpacity: 0.6 }});
                layer.options.interactive = true;
            }});
            return;
        }}
        
        var contador = 0;
        capa.eachLayer(function(layer) {{
            var props = layer.feature.properties;
            var cultivo = (props["{campos['cultivo']}"] || '').toUpperCase();
            
            if (seleccionados.includes(cultivo)) {{
                layer.setStyle({{ opacity: 1, fillOpacity: 0.6 }});
                layer.options.interactive = true;
                contador++;
            }} else {{
                layer.setStyle({{ opacity: 0, fillOpacity: 0 }});
                layer.options.interactive = false;
            }}
        }});
        
        document.getElementById('estadoFiltro').innerHTML = 'Mostrando ' + contador + ' polígonos';
    }}
    
    // ============================================================
    // BÚSQUEDA GLOBAL
    // ============================================================
    
    function buscarGlobal(texto) {{
        if (!texto || texto.length < 3) return;
        var palabra = texto.toLowerCase();
        var encontrado = false;
        
        var capa = obtenerCapaPoligonos();
        if (!capa) return;
        
        capa.eachLayer(function(layer) {{
            var props = layer.feature.properties;
            var cliente = (props["{campos['cliente']}"] || '').toLowerCase();
            var campo = (props['CAMPO'] || '').toLowerCase();
            var localidad = (props['LOCALIDAD'] || '').toLowerCase();
            
            if (cliente.includes(palabra) || campo.includes(palabra) || localidad.includes(palabra)) {{
                encontrado = true;
                map.fitBounds(layer.getBounds(), {{padding: [80,80]}});
                layer.openPopup();
            }}
        }});
        
        if (!encontrado) {{
            mostrarNotificacion('🔍 No se encontraron resultados', 'error');
        }}
    }}
    
    function mostrarNotificacion(mensaje, tipo) {{
        var el = document.createElement('div');
        el.style.cssText = 'position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:' + 
            (tipo === 'error' ? '#f44336' : '#2d7d46') + 
            ';color:white;padding:12px 24px;border-radius:12px;z-index:99999;font-size:14px;box-shadow:0 4px 20px rgba(0,0,0,0.3);';
        el.textContent = mensaje;
        document.body.appendChild(el);
        setTimeout(function() {{ el.remove(); }}, 3000);
    }}
    
    // ============================================================
    // FILTRAR CLIENTE (el original, adaptado)
    // ============================================================
    
    function filtrarCliente() {{
        var valor = document.getElementById('clienteInput').value.toLowerCase().trim();
        if (!valor) {{
            resetearFiltro();
            return;
        }}
        
        var capa = obtenerCapaPoligonos();
        if (!capa) return;
        
        var contador = 0;
        var bounds = null;
        
        capa.eachLayer(function(layer) {{
            var props = layer.feature.properties;
            var cliente = (props["{campos['cliente']}"] || '').toLowerCase();
            
            if (cliente.includes(valor)) {{
                layer.setStyle({{ opacity: 1, fillOpacity: 0.8, weight: 3, color: '#FF5722' }});
                layer.options.interactive = true;
                contador++;
                if (layer.getBounds && layer.getBounds().isValid()) {{
                    bounds = bounds ? bounds.extend(layer.getBounds()) : layer.getBounds();
                }}
            }} else {{
                layer.setStyle({{ opacity: 0, fillOpacity: 0 }});
                layer.options.interactive = false;
            }}
        }});
        
        if (contador > 0 && bounds) {{
            map.fitBounds(bounds, {{padding: [50,50]}});
        }}
        
        document.getElementById('estadoFiltro').innerHTML = '🔍 ' + contador + ' clientes encontrados';
    }}
    
    function resetearFiltro() {{
        document.getElementById('clienteInput').value = '';
        document.querySelectorAll('#cultivoFilters input').forEach(function(el) {{
            el.checked = true;
        }});
        document.querySelectorAll('#cultivoFilters label').forEach(function(el) {{
            el.classList.add('active');
        }});
        
        var capa = obtenerCapaPoligonos();
        if (capa) {{
            capa.eachLayer(function(layer) {{
                layer.setStyle({{ opacity: 1, fillOpacity: 0.6 }});
                layer.options.interactive = true;
            }});
        }}
        
        document.getElementById('estadoFiltro').innerHTML = 'Mostrando todos los polígonos';
        aplicarFiltroCultivos();
    }}
    
    // ============================================================
    // ACTIVAR FILTROS
    // ============================================================
    
    document.addEventListener('DOMContentLoaded', function() {{
        // Checkboxes de cultivo
        document.querySelectorAll('#cultivoFilters input').forEach(function(el) {{
            el.addEventListener('change', function() {{
                var label = this.closest('label');
                if (this.checked) label.classList.add('active');
                else label.classList.remove('active');
                aplicarFiltroCultivos();
            }});
        }});
        
        // Inicializar
        setTimeout(function() {{
            capaPoligonos = obtenerCapaPoligonos();
            aplicarFiltroCultivos();
            console.log("✅ Filtro de cultivos inicializado");
        }}, 1500);
    }});
    
    // ============================================================
    // ACTUALIZAR CONTADOR DE FOTOS
    // ============================================================
    
    var originalCargarFotos = cargarFotosDesdeGithub;
    cargarFotosDesdeGithub = async function() {{
        await originalCargarFotos();
        var totalFotosEl = document.getElementById('totalFotos');
        if (totalFotosEl && typeof todasLasFotos !== 'undefined') {{
            totalFotosEl.textContent = todasLasFotos.length || 0;
        }}
    }};
    </script>
    '''

    # Agregar la interfaz PRO al mapa
    agregar_elemento_html_seguro(m, interfaz_pro_html)

    # ========== CONTROLES ==========
    folium.LayerControl(position='topright', collapsed=True).add_to(m)
    Fullscreen(
        position='topright',
        title='Pantalla completa',
        title_cancel='Salir pantalla completa'
    ).add_to(m)
    MeasureControl(position='topright').add_to(m)

    # ========== TÍTULO PRINCIPAL ==========
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
            PROGRAMA CÓRDOBA 25/26
        </div>
        <div style="font-size: 9px; color: rgba(255, 255, 255, 0.9); margin-top: 1px;">
            Actualizado: {fecha_hora_argentina}
        </div>
    </div>
    '''
    agregar_elemento_html_seguro(m, titulo_html)

    # ========== LEYENDA DE CULTIVOS ==========
    if campos['cultivo'] and campos['hectareas']:
        gdf[campos['hectareas']] = pd.to_numeric(gdf[campos['hectareas']], errors='coerce').fillna(0)
        
        superficie_por_cultivo = {}
        for cultivo in gdf[campos['cultivo']].dropna().unique():
            mascara = gdf[campos['cultivo']] == cultivo
            hectareas = gdf.loc[mascara, campos['hectareas']].sum()
            superficie_por_cultivo[cultivo] = hectareas
        
        total_superficie = sum(superficie_por_cultivo.values())
        
        hectareas_soja = 0
        hectareas_maiz = 0
        
        for cultivo, hectareas in superficie_por_cultivo.items():
            cultivo_str = str(cultivo).lower()
            if 'soja' in cultivo_str or 'soya' in cultivo_str:
                hectareas_soja += hectareas
            elif 'maíz' in cultivo_str or 'maiz' in cultivo_str or 'corn' in cultivo_str:
                hectareas_maiz += hectareas
        
        items_leyenda = []
        
        if hectareas_soja > 0:
            items_leyenda.append(
                f'<div style="display: flex; align-items: center; margin-bottom: 6px; padding: 6px; border-radius: 6px; background: rgba(76, 175, 80, 0.1);">'
                f'<div style="display: flex; align-items: center; justify-content: center; width: 24px; height: 24px; background: #4CAF50; margin-right: 8px; border-radius: 6px; flex-shrink: 0;">'
                f'<span style="color: white; font-size: 10px;">🟢</span>'
                f'</div>'
                f'<div style="flex: 1;">'
                f'<div style="font-size: 10px; font-weight: 700; color: #2C2C2C;">SOJA</div>'
                f'<div style="font-size: 11px; font-weight: 800; color: #2C5530;">{hectareas_soja:,.0f} ha</div>'
                f'</div>'
                f'</div>'
            )
        
        if hectareas_maiz > 0:
            items_leyenda.append(
                f'<div style="display: flex; align-items: center; margin-bottom: 6px; padding: 6px; border-radius: 6px; background: rgba(255, 193, 7, 0.1);">'
                f'<div style="display: flex; align-items: center; justify-content: center; width: 24px; height: 24px; background: #FFC107; margin-right: 8px; border-radius: 6px; flex-shrink: 0;">'
                f'<span style="color: white; font-size: 10px;">🟡</span>'
                f'</div>'
                f'<div style="flex: 1;">'
                f'<div style="font-size: 10px; font-weight: 700; color: #2C2C2C;">MAÍZ</div>'
                f'<div style="font-size: 11px; font-weight: 800; color: #2C5530;">{hectareas_maiz:,.0f} ha</div>'
                f'</div>'
                f'</div>'
            )
        
        items_leyenda.append(
            f'<div style="margin-top: 8px; padding: 8px; background: linear-gradient(135deg, #2C5530, #8A9A5B); border-radius: 8px;">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; font-size: 10px;">'
            f'<div style="font-weight: 700; color: white;">TOTAL</div>'
            f'<div style="font-size: 12px; font-weight: 800; color: white;">{total_superficie:,.0f} ha</div>'
            f'</div>'
            f'</div>'
        )

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

        agregar_elemento_html_seguro(m, leyenda_html)

    # ========== BOTÓN PARA SUBIR FOTOS (el original) ==========
    boton_fotos_html = '''
    <div id="controlSubirFotos" style="
        position: absolute;
        top: 230px;
        right: 10px;
        z-index: 1000;
    ">
        <a class="leaflet-bar-part leaflet-bar-part-single" 
           href="#" 
           title="📸 Subir foto desde campo"
           style="
                display: block;
                width: 30px;
                height: 30px;
                background: linear-gradient(135deg, #4CAF50, #2E7D32);
                border-radius: 4px;
                border: 2px solid rgba(255, 255, 255, 0.8);
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                text-align: center;
                line-height: 30px;
                font-size: 18px;
                color: white;
                text-decoration: none;
                cursor: pointer;
                margin-bottom: 5px;
           ">
            📸
        </a>
    </div>

    <div id="panelSubirFoto" style="
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 20px;
        border-radius: 15px;
        border: 3px solid #4CAF50;
        z-index: 10002;
        display: none;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        width: 90%;
        max-width: 400px;
        font-family: Arial, sans-serif;
    ">

        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div style="font-size: 18px; font-weight: bold; color: #2E7D32;">📸 Subir foto desde campo</div>
            <button onclick="cerrarPanelFoto()" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #666;">×</button>
        </div>

        <div id="contenidoSubir">
            <div id="paso1" style="text-align: center;">
                <button onclick="tomarFotoConCamara()" style="width:100%;padding:15px;margin-bottom:10px;background:#4CAF50;color:white;border:none;border-radius:10px;font-size:16px;cursor:pointer;">📷 Tomar foto con cámara</button>
                <div style="margin:15px 0;color:#666;font-size:14px;">─── o ───</div>
                <button onclick="seleccionarFotoArchivo()" style="width:100%;padding:15px;background:#2196F3;color:white;border:none;border-radius:10px;font-size:16px;cursor:pointer;">📁 Seleccionar foto existente</button>
                <input type="file" id="inputFotoArchivo" accept="image/*" style="display:none;" capture="environment">
            </div>

            <div id="paso2" style="display:none;">
                <div style="text-align:center;margin-bottom:15px;">
                    <img id="previewFoto" src="" style="max-width:100%;max-height:300px;border-radius:10px;border:2px solid #ddd;">
                </div>
                <div style="margin-bottom:15px;">
                    <div style="font-weight:bold;margin-bottom:5px;color:#666;">📍 Ubicación GPS:</div>
                    <div id="infoGPS" style="font-size:12px;color:#4CAF50;">Obteniendo ubicación...</div>
                </div>
                <button onclick="subirFoto()" id="btnSubirFoto" style="width:100%;padding:15px;background:linear-gradient(135deg,#4CAF50,#2E7D32);color:white;border:none;border-radius:10px;font-size:16px;cursor:pointer;font-weight:bold;">⬆️ Subir foto al mapa</button>
            </div>

            <div id="paso3" style="display:none;text-align:center;">
                <div style="margin-bottom:20px;">
                    <div style="width:50px;height:50px;margin:0 auto 15px;border:3px solid #f3f3f3;border-top:3px solid #4CAF50;border-radius:50%;animation:spin 1s linear infinite;"></div>
                    <div id="mensajeProgreso" style="font-weight:bold;color:#2E7D32;">Subiendo foto...</div>
                </div>
                <div id="infoSubida" style="font-size:12px;color:#666;">Esto puede tomar unos segundos</div>
            </div>
        </div>

        <div style="margin-top:20px;padding-top:15px;border-top:1px solid #eee;font-size:11px;color:#888;text-align:center;">
            <div>📍 La foto aparecerá en el mapa en 2 minutos</div>
        </div>
    </div>

    <div id="overlayFoto" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:10001;display:none;"></div>

    <style>
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .leaflet-top .leaflet-control { margin-top: 10px; }
    #controlSubirFotos a:hover { background: linear-gradient(135deg, #45a049, #1b5e20); transform: scale(1.05); transition: all 0.2s; }
    </style>

    <script>
    let fotoActual = null;
    let gpsActual = null;
    let estaEnLinea = navigator.onLine;

    function abrirPanelSubirFoto() {
        document.getElementById('panelSubirFoto').style.display = 'block';
        document.getElementById('overlayFoto').style.display = 'block';
        document.getElementById('paso1').style.display = 'block';
        document.getElementById('paso2').style.display = 'none';
        document.getElementById('paso3').style.display = 'none';
        obtenerUbicacionGPS();
    }

    function cerrarPanelFoto() {
        document.getElementById('panelSubirFoto').style.display = 'none';
        document.getElementById('overlayFoto').style.display = 'none';
        fotoActual = null;
    }

    function obtenerUbicacionGPS() {
        const infoGPS = document.getElementById('infoGPS');
        if (!navigator.geolocation) {
            infoGPS.innerHTML = '❌ GPS no disponible en este dispositivo';
            gpsActual = null;
            return;
        }
        infoGPS.innerHTML = '📍 Obteniendo ubicación...';
        navigator.geolocation.getCurrentPosition(
            function(posicion) {
                const lat = posicion.coords.latitude.toFixed(6);
                const lon = posicion.coords.longitude.toFixed(6);
                const precision = posicion.coords.accuracy.toFixed(0);
                gpsActual = { lat: parseFloat(lat), lon: parseFloat(lon), precision: precision };
                infoGPS.innerHTML = `📍 ${lat}, ${lon} (precisión: ${precision}m)`;
                infoGPS.style.color = '#4CAF50';
            },
            function(error) {
                console.error('Error GPS:', error);
                gpsActual = null;
                infoGPS.innerHTML = '⚠️ No se pudo obtener ubicación. Se usará ubicación aproximada.';
                infoGPS.style.color = '#FF9800';
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
    }

    function tomarFotoConCamara() {
        const input = document.getElementById('inputFotoArchivo');
        input.setAttribute('capture', 'environment');
        input.click();
    }

    function seleccionarFotoArchivo() {
        const input = document.getElementById('inputFotoArchivo');
        input.removeAttribute('capture');
        input.click();
    }

    document.getElementById('inputFotoArchivo').addEventListener('change', function(e) {
        const archivo = e.target.files[0];
        if (!archivo) return;
        const reader = new FileReader();
        reader.onload = function(event) {
            fotoActual = event.target.result;
            document.getElementById('previewFoto').src = fotoActual;
            document.getElementById('paso1').style.display = 'none';
            document.getElementById('paso2').style.display = 'block';
            if (!gpsActual) obtenerUbicacionGPS();
        };
        reader.readAsDataURL(archivo);
    });

    async function subirFoto() {
        if (!fotoActual) {
            alert('Por favor, selecciona una foto primero');
            return;
        }
        document.getElementById('paso2').style.display = 'none';
        document.getElementById('paso3').style.display = 'block';
        const btnSubir = document.getElementById('btnSubirFoto');
        const mensajeProgreso = document.getElementById('mensajeProgreso');
        const infoSubida = document.getElementById('infoSubida');
        btnSubir.disabled = true;
        const timestamp = Date.now();
        const nombreArchivo = `foto_${gpsActual ? gpsActual.lat + '_' + gpsActual.lon + '_' : ''}${timestamp}.jpg`;
        const base64Data = fotoActual.split(',')[1];
        estaEnLinea = navigator.onLine;
        if (!estaEnLinea) {
            guardarFotoOffline(base64Data, nombreArchivo);
            mensajeProgreso.innerHTML = '✅ Guardada localmente (offline)';
            infoSubida.innerHTML = 'Se subirá automáticamente cuando haya conexión';
            setTimeout(() => { cerrarPanelFoto(); mostrarNotificacion('📸 Foto guardada (modo offline)', 'success'); }, 2000);
            return;
        }
        mensajeProgreso.innerHTML = '🌐 Subiendo a GitHub...';
        try {
            const fotoData = { nombre: nombreArchivo, datos: base64Data, lat: gpsActual ? gpsActual.lat : -31.4201, lon: gpsActual ? gpsActual.lon : -64.1888, timestamp: new Date().toISOString() };
            async function subirFotoConWorkflow(fotoData) {
                console.log('🔄 Enviando foto a GitHub Actions...');
                const nombreArchivo = `foto_${Math.abs(fotoData.lat).toFixed(6)}_${Math.abs(fotoData.lon).toFixed(6)}_${Date.now()}.jpg`;
                try {
                    const response = await fetch(
                        'https://api.github.com/repos/franciscotomatis/APP-C-rdoba/actions/workflows/recibir-foto.yml/dispatches',
                        { method: 'POST', headers: { 'Accept': 'application/vnd.github.v3+json', 'Content-Type': 'application/json' },
                        body: JSON.stringify({ ref: 'main', inputs: { foto_base64: fotoData.datos, nombre_archivo: nombreArchivo, latitud: fotoData.lat.toString(), longitud: fotoData.lon.toString() } }) }
                    );
                    if (response.ok) { console.log('✅ Workflow ejecutado correctamente'); return { success: true }; }
                    else { console.error('❌ Error ejecutando workflow'); return { success: false }; }
                } catch (error) { console.error('❌ Error de red:', error); return { success: false }; }
            }
            const resultado = await subirFotoConWorkflow(fotoData);
            if (resultado.success) {
                mensajeProgreso.innerHTML = '✅ Foto subida exitosamente';
                infoSubida.innerHTML = 'Aparecerá en el mapa en 2 minutos';
                setTimeout(() => {
                    cerrarPanelFoto();
                    mostrarNotificacion('✅ Foto subida al mapa', 'success');
                    if (window.capaFotosGithub) {
                        window.capaFotosGithub.clearLayers();
                        if (typeof cargarFotosDesdeGithub === 'function') cargarFotosDesdeGithub();
                    }
                }, 2000);
            } else {
                throw new Error('Error en subida');
            }
        } catch (error) {
            console.error('Error subiendo foto:', error);
            guardarFotoOffline(base64Data, nombreArchivo);
            mensajeProgreso.innerHTML = '⚠️ Guardada localmente';
            infoSubida.innerHTML = 'Error de conexión. Se intentará más tarde.';
            setTimeout(() => { cerrarPanelFoto(); mostrarNotificacion('📸 Foto guardada (se subirá luego)', 'warning'); }, 2000);
        }
    }

    function guardarParaSubidaManual(fotoData, nombreArchivo) {
        const fotosOffline = JSON.parse(localStorage.getItem('fotosOffline') || '[]');
        fotosOffline.push({ id: Date.now(), nombre: nombreArchivo, datos: fotoData.datos, gps: { lat: fotoData.lat, lon: fotoData.lon }, timestamp: new Date().toISOString(), estado: 'pendiente', intentos: 0 });
        localStorage.setItem('fotosOffline', JSON.stringify(fotosOffline));
        actualizarBotonPendientes(fotosOffline.length);
        console.log('📸 Foto guardada para subida manual');
        return { success: false, mensaje: 'Guardada para subida manual', cantidad: fotosOffline.length };
    }

    function actualizarBotonPendientes(cantidad) {
        let boton = document.getElementById('btnFotosPendientes');
        if (!boton && cantidad > 0) {
            boton = document.createElement('div');
            boton.id = 'btnFotosPendientes';
            boton.style.position = 'fixed';
            boton.style.bottom = '80px';
            boton.style.right = '20px';
            boton.style.zIndex = '9998';
            document.body.appendChild(boton);
        }
        if (cantidad > 0 && boton) {
            boton.innerHTML = `<button onclick="mostrarFotosPendientes()" style="background:#FF9800;color:white;border:none;padding:10px 15px;border-radius:8px;font-family:Arial,sans-serif;font-size:12px;cursor:pointer;box-shadow:0 3px 10px rgba(0,0,0,0.2);">📋 ${cantidad} foto(s) pendientes</button>`;
        } else if (boton && cantidad === 0) {
            boton.remove();
        }
    }

    function guardarFotoOffline(base64Data, nombreArchivo) {
        const fotosOffline = JSON.parse(localStorage.getItem('fotosOffline') || '[]');
        const fotoOffline = { id: Date.now(), nombre: nombreArchivo, datos: base64Data, gps: gpsActual, timestamp: new Date().toISOString(), estado: 'pendiente' };
        fotosOffline.push(fotoOffline);
        localStorage.setItem('fotosOffline', JSON.stringify(fotosOffline));
        console.log('📸 Foto guardada offline');
        programarSincronizacion();
    }

    function programarSincronizacion() {
        window.addEventListener('online', function sincronizarAlConectar() {
            console.log('📶 Conexión recuperada, sincronizando fotos...');
            sincronizarFotosOffline();
            window.removeEventListener('online', sincronizarAlConectar);
        });
    }

    async function sincronizarFotosOffline() {
        const fotosOffline = JSON.parse(localStorage.getItem('fotosOffline') || '[]');
        if (fotosOffline.length === 0) return;
        console.log(`🔄 Intentando subir ${fotosOffline.length} fotos offline...`);
        const fotosExitosas = [];
        const fotosFallidas = [];
        for (const foto of fotosOffline) {
            try {
                const resultado = await subirAGitHubAPI({ datos: foto.datos, lat: foto.gps.lat, lon: foto.gps.lon, nombre: foto.nombre });
                if (resultado.success) { fotosExitosas.push(foto); }
                else { foto.intentos = (foto.intentos || 0) + 1; fotosFallidas.push(foto); }
                await new Promise(resolve => setTimeout(resolve, 1000));
            } catch (error) {
                console.error('Error subiendo foto offline:', error);
                foto.intentos = (foto.intentos || 0) + 1;
                fotosFallidas.push(foto);
            }
        }
        if (fotosExitosas.length > 0) {
            const nuevasFotos = fotosOffline.filter(f => !fotosExitosas.some(exitosa => exitosa.id === f.id));
            localStorage.setItem('fotosOffline', JSON.stringify(nuevasFotos));
            mostrarNotificacion(`✅ ${fotosExitosas.length} fotos subidas`, 'success');
        }
        actualizarBotonPendientes(fotosFallidas.length);
        console.log(`Resultado: ${fotosExitosas.length} exitosas, ${fotosFallidas.length} fallidas`);
    }

    function mostrarNotificacion(mensaje, tipo = 'info') {
        const notificacion = document.createElement('div');
        notificacion.style.position = 'fixed';
        notificacion.style.bottom = '20px';
        notificacion.style.right = '20px';
        notificacion.style.padding = '12px 20px';
        notificacion.style.borderRadius = '8px';
        notificacion.style.fontFamily = 'Arial, sans-serif';
        notificacion.style.fontSize = '14px';
        notificacion.style.zIndex = '10003';
        notificacion.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        const colores = { success: { bg: '#4CAF50', color: 'white' }, warning: { bg: '#FF9800', color: 'white' }, info: { bg: '#2196F3', color: 'white' } };
        notificacion.style.background = colores[tipo]?.bg || '#2196F3';
        notificacion.style.color = colores[tipo]?.color || 'white';
        notificacion.textContent = mensaje;
        document.body.appendChild(notificacion);
        setTimeout(() => {
            notificacion.style.opacity = '0';
            notificacion.style.transition = 'opacity 0.5s';
            setTimeout(() => { if (notificacion.parentNode) { notificacion.parentNode.removeChild(notificacion); } }, 500);
        }, 3000);
    }

    document.addEventListener('DOMContentLoaded', function() {
        const botonSubir = document.querySelector('#controlSubirFotos a');
        if (botonSubir) {
            botonSubir.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                abrirPanelSubirFoto();
            });
        }
        setTimeout(() => {
            const fotosPendientes = JSON.parse(localStorage.getItem('fotosOffline') || '[]');
            if (fotosPendientes.length > 0 && navigator.onLine) { sincronizarFotosOffline(); }
        }, 5000);
    });

    window.addEventListener('online', function() {
        estaEnLinea = true;
        mostrarNotificacion('📶 Conectado a internet', 'success');
    });

    window.addEventListener('offline', function() {
        estaEnLinea = false;
        mostrarNotificacion('⚠️ Sin conexión - Modo offline', 'warning');
    });
    </script>
    '''

    agregar_elemento_html_seguro(m, boton_fotos_html)

    # ========== GPS AUTO-ACTIVADO ==========
    try:
        locate = LocateControl(
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
            },
            locateOptions={
                'enableHighAccuracy': True,
                'maximumAge': 30000,
                'timeout': 27000,
                'watch': True
            }
        ).add_to(m)
        
        print("✅ 📍 Geolocalización configurada")
        
        gps_auto_html = '''
        <script>
        setTimeout(function() {
            var gpsButtons = document.querySelectorAll('.leaflet-control-locate a');
            if (gpsButtons.length > 0) {
                console.log("📍 Activando GPS automáticamente...");
                gpsButtons[0].click();
                var gpsControl = document.querySelector('.leaflet-control-locate');
                if (gpsControl) {
                    gpsControl.style.opacity = '0';
                    gpsControl.style.pointerEvents = 'none';
                }
            } else {
                setTimeout(arguments.callee, 1000);
            }
        }, 3000);
        
        function seguirUbicacionSiempre() {
            if (navigator.geolocation) {
                var options = { enableHighAccuracy: true, maximumAge: 10000, timeout: 5000 };
                navigator.geolocation.watchPosition(
                    function(position) { console.log("📍 Ubicación actualizada"); },
                    function(error) { console.log("⚠️ Error GPS:", error.message); },
                    options
                );
            }
        }
        if (typeof map !== 'undefined') {
            map.on('locationfound', function(e) {
                console.log("📍 GPS activado con éxito");
                seguirUbicacionSiempre();
            });
        }
        </script>
        '''
        agregar_elemento_html_seguro(m, gps_auto_html)
        
    except Exception as e:
        print(f"⚠️  Error GPS: {e}")

    # ========== PANEL DE COMPARACIÓN POR ZONA ==========
    if campos['zona'] and campos['hectareas']:
        gdf[campos['zona']] = gdf[campos['zona']].astype(str).str.strip()
        hectareas_por_zona = {}
        for zona in gdf[campos['zona']].dropna().unique():
            zona_str = str(zona).strip()
            mascara = gdf[campos['zona']] == zona_str
            hectareas = gdf.loc[mascara, campos['hectareas']].sum()
            hectareas_por_zona[zona_str] = hectareas
        
        hectareas_proyectadas = { "1": 128998, "2": 65245, "3": 187636, "4": 151566 }
        zonas_ordenadas = ["1", "2", "3", "4"]
        datos_proyectados = []
        datos_reales = []
        diferencias = []
        porcentajes_dif = []
        
        for zona in zonas_ordenadas:
            proyectado = hectareas_proyectadas.get(zona, 0)
            real = hectareas_por_zona.get(zona, 0) if zona in hectareas_por_zona else 0
            diferencia = real - proyectado
            porcentaje = (diferencia / proyectado * 100) if proyectado > 0 else 0
            datos_proyectados.append(proyectado)
            datos_reales.append(real)
            diferencias.append(diferencia)
            porcentajes_dif.append(porcentaje)
        
        max_valor = max(max(datos_proyectados), max(datos_reales)) if datos_proyectados and datos_reales else 100000
        
        panel_graficos_html = f'''
        <div id="btnGraficos" style="position: fixed;
                bottom: 25px; left: 25px;
                background: linear-gradient(135deg, #2C5530, #8A9A5B);
                color: white;
                padding: 12px;
                border-radius: 50%;
                z-index: 9997;
                cursor: pointer;
                box-shadow: 0 5px 15px rgba(44, 85, 48, 0.3);
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 20px;
                width: 50px;
                height: 50px;
                transition: all 0.3s;"
                onclick="togglePanelGraficos()"
                onmouseover="this.style.transform='scale(1.1)'; this.style.boxShadow='0 8px 25px rgba(44, 85, 48, 0.4)';"
                onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 5px 15px rgba(44, 85, 48, 0.3)';">
            <div style="display: flex; align-items: center; justify-content: center; width: 100%; height: 100%;">📈</div>
        </div>
        <div id="panelGraficos" style="position: fixed;
                bottom: -80%;
                left: 0;
                width: 100%;
                height: 80%;
                background-color: white;
                z-index: 10001;
                box-shadow: 0 -3px 15px rgba(0,0,0,0.3);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                transition: bottom 0.4s ease;
                overflow-y: auto;
                font-family: Arial, sans-serif;">
            <div style="position: sticky; top: 0; background: linear-gradient(135deg, #2C5530, #8A9A5B); color: white;
                    padding: 15px 20px; border-top-left-radius: 12px; border-top-right-radius: 12px;
                    display: flex; justify-content: space-between; align-items: center; z-index: 1;
                    box-shadow: 0 3px 15px rgba(44, 85, 48, 0.3);">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="width: 36px; height: 36px; background: rgba(255, 255, 255, 0.2); 
                            border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 18px;">📊</span>
                    </div>
                    <div>
                        <div style="font-size: 16px; font-weight: 700; color: white;">COMPARACIÓN POR ZONA</div>
                        <div style="font-size: 11px; color: rgba(255, 255, 255, 0.9); margin-top: 2px;">Proyectado vs Actual - Campaña 25/26</div>
                    </div>
                </div>
                <button onclick="togglePanelGraficos()" style="background: rgba(255, 255, 255, 0.2); border: none; color: white; font-size: 22px; cursor: pointer; padding: 0; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center;">×</button>
            </div>
            <div style="padding: 15px; max-width: 900px; margin: 0 auto;">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 20px;">
                    <div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid #2E7D32;">
                        <div style="font-size: 11px; color: #666; margin-bottom: 5px;">TOTAL PROYECTADO</div>
                        <div style="font-size: 20px; font-weight: bold; color: #2E7D32;">{sum(hectareas_proyectadas.values()):,.0f} ha</div>
                    </div>
                    <div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid #2196F3;">
                        <div style="font-size: 11px; color: #666; margin-bottom: 5px;">TOTAL ACTUAL</div>
                        <div style="font-size: 20px; font-weight: bold; color: #2196F3;">{sum(hectareas_por_zona.values()):,.0f} ha</div>
                    </div>
                    <div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid #FF9800;">
                        <div style="font-size: 11px; color: #666; margin-bottom: 5px;">DIFERENCIA TOTAL</div>
                        <div style="font-size: 20px; font-weight: bold; color: {'red' if (sum(hectareas_por_zona.values()) - sum(hectareas_proyectadas.values())) < 0 else '#4CAF50'};">
                            {sum(hectareas_por_zona.values()) - sum(hectareas_proyectadas.values()):+,.0f} ha
                        </div>
                    </div>
                    <div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid #9C27B0;">
                        <div style="font-size: 11px; color: #666; margin-bottom: 5px;">% DE CUMPLIMIENTO</div>
                        <div style="font-size: 20px; font-weight: bold; color: {'red' if ((sum(hectareas_por_zona.values()) / sum(hectareas_proyectadas.values()) * 100) if sum(hectareas_proyectadas.values()) > 0 else 0) < 100 else '#4CAF50'};">
                            {(sum(hectareas_por_zona.values()) / sum(hectareas_proyectadas.values()) * 100) if sum(hectareas_proyectadas.values()) > 0 else 0:.1f}%
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <script>
        let panelAbierto = false;
        function togglePanelGraficos() {{
            const panel = document.getElementById("panelGraficos");
            const btn = document.getElementById("btnGraficos");
            if (panelAbierto) {{
                panel.style.bottom = "-80%";
                panel.style.zIndex = "9998";
                btn.innerHTML = "📈";
            }} else {{
                panel.style.zIndex = "10001";
                panel.style.bottom = "0";
                btn.innerHTML = "📊";
            }}
            panelAbierto = !panelAbierto;
        }}
        document.addEventListener('click', function(event) {{
            const panel = document.getElementById("panelGraficos");
            const btn = document.getElementById("btnGraficos");
            if (panelAbierto && !panel.contains(event.target) && !btn.contains(event.target)) {{
                togglePanelGraficos();
            }}
        }});
        document.addEventListener('DOMContentLoaded', function() {{
            document.getElementById("btnGraficos").style.display = "none";
        }});
        </script>
        '''
        agregar_elemento_html_seguro(m, panel_graficos_html)

    # ========== LOGIN ==========
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

            <div style="margin-bottom: 20px;">
                <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #2C5530, #8A9A5B);
                        border-radius: 15px; display: flex; align-items: center; justify-content: center;
                        margin: 0 auto 12px; box-shadow: 0 4px 15px rgba(44, 85, 48, 0.3);">
                    <span style="color: white; font-size: 28px;">🔐</span>
                </div>
                <h2 style="color: #2C5530; margin-bottom: 5px; font-weight: 800; font-size: 18px;">PROGRAMA CÓRDOBA 25/26</h2>
            </div>

            <div style="margin-bottom: 20px; text-align: left;">
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 6px; font-weight: 600; color: #2C5530; font-size: 12px;">👤 Usuario</label>
                    <input type="text" id="loginUsuario" placeholder="Ingrese su usuario"
                           style="width:100%;padding:12px 14px;border:2px solid rgba(212,212,212,0.8);border-radius:10px;font-size:14px;background:white;color:#2C2C2C;box-sizing:border-box;"
                           onfocus="this.style.borderColor='#8A9A5B'; this.style.boxShadow='0 0 0 3px rgba(138,154,91,0.2)';"
                           onblur="this.style.borderColor='rgba(212,212,212,0.8)'; this.style.boxShadow='none';">
                </div>
                <div style="margin-bottom: 20px;">
                    <label style="display: block; margin-bottom: 6px; font-weight: 600; color: #2C5530; font-size: 12px;">🔒 Contraseña</label>
                    <input type="password" id="loginContrasena" placeholder="Ingrese su contraseña"
                           style="width:100%;padding:12px 14px;border:2px solid rgba(212,212,212,0.8);border-radius:10px;font-size:14px;background:white;color:#2C2C2C;box-sizing:border-box;"
                           onfocus="this.style.borderColor='#8A9A5B'; this.style.boxShadow='0 0 0 3px rgba(138,154,91,0.2)';"
                           onblur="this.style.borderColor='rgba(212,212,212,0.8)'; this.style.boxShadow='none';">
                </div>
                <button onclick="verificarAcceso()"
                        style="width:100%;background:linear-gradient(135deg,#2C5530,#8A9A5B);color:white;border:none;padding:14px;border-radius:10px;font-size:15px;font-weight:700;cursor:pointer;transition:all 0.3s;display:flex;align-items:center;justify-content:center;gap:8px;"
                        onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(44,85,48,0.4)';"
                        onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
                    <span>🔓</span>
                    <span>INGRESAR</span>
                </button>
            </div>
            <div id="loginError" style="margin-top:15px;color:#f44336;font-size:12px;font-weight:600;display:none;padding:10px;background:rgba(244,67,54,0.1);border-radius:6px;border-left:4px solid #f44336;">
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
                }}, 500);

                map.getContainer().style.pointerEvents = "auto";

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
        setTimeout(() => {{
            document.getElementById("loginUsuario").focus();
        }}, 500);
    }});
    </script>
    '''
    
    agregar_elemento_html_seguro(m, login_html)

    # ========== AJUSTAR VISTA ==========
    if not gdf.empty:
        m.fit_bounds(bounds)

    # ========== GUARDAR ARCHIVO ==========
    m.save(output_file)
    print(f"✅ Aplicación PRO guardada como: {output_file}")
    
    return output_file

def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python generar_app_pro.py <ruta_al_geojson> [nombre_salida]")
        print("   Ejemplo: python generar_app_pro.py geojson_unificado_actual.geojson index_pro.html")
        sys.exit(1)
    
    ruta_geojson = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = "index_pro.html"
    
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
        
        crear_app_pro(geojson_data, gdf, campos, output_file)
        
        print(f"\n{'='*80}")
        print("🎉 APLICACIÓN PRO GENERADA EXITOSAMENTE")
        print(f"{'='*80}")
        print(f"📁 Archivo: {output_file}")
        print(f"📊 Polígonos: {len(gdf)}")
        print(f"🔐 Credenciales: {USUARIO_CORRECTO} / {CONTRASENA_CORRECTA}")
        print(f"\n🌐 Para usar: Abre {output_file} en cualquier navegador")
        print(f"📋 Funcionalidades PRO:")
        print(f"   ✅ Login seguro EXACTO")
        print(f"   ✅ Interfaz renovada (header, sidebar, bottom bar)")
        print(f"   ✅ Filtro de cultivos funcional")
        print(f"   ✅ Buscador de clientes (el original)")
        print(f"   ✅ Modo oscuro/claro")
        print(f"   ✅ Capa de fotos desde GitHub")
        print(f"   ✅ Capa de siniestros (con filtro)")
        print(f"   ✅ Sistema de leyendas WMS")
        print(f"   ✅ GPS auto-activado")
        print(f"   ✅ Panel de comparación por zona")
        print(f"   ✅ Título, leyenda de cultivos, estilos EXACTOS")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
