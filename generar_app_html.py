#!/usr/bin/env python3
"""
GENERADOR AUTOMÁTICO DE APLICACIÓN HTML IDÉNTICO A COLAB
Versión para GitHub Actions - Toma geojson automático
CORREGIDO: Problemas con Jinja2 y llaves {}
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

print("🔐🌽🌱 GENERADOR DE APLICACIÓN WEB COMPLETA - PROGRAMA CÓRDOBA 25/26")
print("=" * 80)

# 🔐 CREDENCIALES DE ACCESO (MISMO QUE EN COLAB)
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
    """Encuentra campos clave automáticamente (IDÉNTICO A COLAB)"""
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

    return {
        'cultivo': campo_cultivo,
        'hectareas': campo_hectareas,
        'cliente': campo_cliente,
        'zona': campo_zona,
        'causa_stro': campo_causa_stro
    }

def agregar_html_seguro(mapa, html_content):
    """Agrega HTML de forma segura evitando problemas con Jinja2"""
    try:
        from branca.element import Element
        element = Element(html_content)
        mapa.get_root().html.add_child(element)
    except Exception as e:
        print(f"⚠️  Error agregando HTML: {e}")
        # Intento alternativo usando folium.Element
        try:
            folium_element = folium.Element(html_content)
            mapa.get_root().html.add_child(folium_element)
        except:
            print("❌ No se pudo agregar el HTML")

def crear_app_completa(geojson_data, gdf, campos, output_file):
    """CREA LA APLICACIÓN IDÉNTICA A COLAB - VERSIÓN CORREGIDA"""
    
    print(f"\n🗺️ Creando aplicación web IDÉNTICA A COLAB: {output_file}")
    
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

    # ========== CAPAS BASE (IDÉNTICAS) ==========
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

    # ========== ESTILOS POR CULTIVO (IDÉNTICOS) ==========
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

        # Guardar colores en propiedades para restaurar después
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

    # ========== ESTILOS PARA SINIESTROS (IDÉNTICOS) ==========
    def estilo_por_causa_siniestro(feature):
        """Estilo específico para siniestros"""
        propiedades = feature['properties']
        causa = propiedades.get(campos['causa_stro'], '').upper() if campos['causa_stro'] else ''

        # Mapeo de colores por causa de siniestro (IDÉNTICO)
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

        # Guardar colores en propiedades
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
        """Resaltado específico para siniestros"""
        return {
            'fillColor': '#FF5722',
            'color': '#D84315',
            'weight': 4,
            'fillOpacity': 0.9,
            'dashArray': '3, 3'
        }

    # ========== CAMPOS PARA POPUP (IDÉNTICOS) ==========
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

    # ========== CAPA DE SINIESTROS (IDÉNTICA) ==========
    if campos['causa_stro'] and gdf[campos['causa_stro']].notna().any():
        print("✅ Encontrados datos de siniestros")
        
        # Filtrar solo los polígonos que tienen causa de siniestro
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

            # Crear capa de siniestros SEPARADA
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
                    fields=[campos['causa_stro']] + campos_para_popup[:5],
                    aliases=['<b>Causa del siniestro</b>'] + 
                            [f"<b>{col}</b>" for col in campos_para_popup[:5]],
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

            # Obtener causas únicas para el buscador
            causas_unicas = sorted(gdf[campos['causa_stro']].dropna().unique())
            
            # ========== BUSCADOR PARA SINIESTROS (VERSIÓN CORREGIDA) ==========
            buscador_siniestros_html = '''
            <div id="buscadorSiniestros" style="position: fixed;
                    top: 260px; left: 10px;
                    background-color: rgba(244, 67, 54, 0.95);
                    padding: 8px 10px;
                    border-radius: 6px;
                    border: 2px solid #C62828;
                    z-index: 9997;
                    font-family: Arial, sans-serif;
                    font-size: 11px;
                    width: 220px;
                    box-shadow: 0 3px 8px rgba(0,0,0,0.15);
                    display: none;">
            '''

            # Agregar opciones dinámicas usando f-string fuera del JavaScript
            opciones_html = "".join(f'<option value="{causa}">{causa}</option>' for causa in causas_unicas)
            
            buscador_siniestros_html += f'''
                <!-- CABECERA -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div style="font-weight: bold; color: white; font-size: 12px; display: flex; align-items: center;">
                        <span style="margin-right: 5px;">⚠️</span>
                        Filtrar siniestros
                    </div>
                    <button onclick="toggleBuscadorSiniestros()"
                            style="background: none; border: none; cursor: pointer; font-size: 14px; color: white;">
                            ×</button>
                </div>

                <!-- CONTENIDO -->
                <div id="contenidoBuscadorSiniestros">
                    <div style="margin-bottom: 8px;">
                        <select id="causaSiniestroSelect"
                               style="width: 100%; padding: 5px; border: 1px solid #ddd;
                                      border-radius: 3px; font-size: 11px;">
                            <option value="">Todas las causas</option>
                            {opciones_html}
                        </select>
                    </div>

                    <div style="display: flex; gap: 5px; margin-bottom: 6px;">
                        <button onclick="filtrarSiniestros()"
                                style="flex: 1; background-color: white; color: #F44336;
                                       border: none; padding: 5px; border-radius: 3px;
                                       cursor: pointer; font-size: 10px; font-weight: bold;">
                            Filtrar
                        </button>
                        <button onclick="mostrarTodosSiniestros()"
                                style="flex: 1; background-color: #FFCCBC; color: #D84315;
                                       border: none; padding: 5px; border-radius: 3px;
                                       cursor: pointer; font-size: 10px;">
                            Mostrar todos
                        </button>
                    </div>

                    <div id="estadoSiniestros"
                         style="font-size: 9px; color: white; margin-top: 6px;
                                padding-top: 5px; border-top: 1px solid rgba(255,255,255,0.3);">
                        Total: {len(siniestros_features)} siniestros
                    </div>
                </div>
            </div>

            <script>
            var buscadorSiniestrosVisible = false;

            function toggleBuscadorSiniestros() {{
                var buscador = document.getElementById("buscadorSiniestros");
                if (buscadorSiniestrosVisible) {{
                    buscador.style.display = "none";
                }} else {{
                    buscador.style.display = "block";
                }}
                buscadorSiniestrosVisible = !buscadorSiniestrosVisible;
            }}

            function onCapaSiniestrosChange() {{
                var checkbox = document.querySelector('input[title="⚠️ Siniestros"]');
                var buscador = document.getElementById("buscadorSiniestros");

                if (checkbox && checkbox.checked) {{
                    buscador.style.display = "block";
                    buscadorSiniestrosVisible = true;
                }} else {{
                    buscador.style.display = "none";
                    buscadorSiniestrosVisible = false;
                }}
            }}

            function filtrarSiniestros() {{
                var causaSeleccionada = document.getElementById("causaSiniestroSelect").value;
                var capaSiniestros = window.siniestrosLayer;  // Usamos variable global
                var contador = 0;

                if (capaSiniestros) {{
                    capaSiniestros.eachLayer(function(layer) {{
                        var causa = layer.feature.properties.{campos['causa_stro']} || '';

                        if (!causaSeleccionada || causa === causaSeleccionada) {{
                            layer.setStyle({{
                                fillOpacity: 0.7,
                                weight: 3,
                                opacity: 1
                            }});
                            layer.options.interactive = true;
                            contador++;
                        }} else {{
                            layer.setStyle({{
                                fillOpacity: 0.1,
                                weight: 1,
                                opacity: 0.3
                            }});
                            layer.options.interactive = false;
                        }}
                    }});

                    document.getElementById("estadoSiniestros").innerHTML =
                        "Mostrando: " + contador + " siniestros" +
                        (causaSeleccionada ? " (" + causaSeleccionada + ")" : "");
                }}
            }}

            function mostrarTodosSiniestros() {{
                document.getElementById("causaSiniestroSelect").value = "";
                filtrarSiniestros();
            }}

            document.addEventListener("DOMContentLoaded", function() {{
                setTimeout(function() {{
                    // Guardar referencia a la capa de siniestros
                    window.siniestrosLayer = {siniestros_layer.get_name()};
                    
                    var checkboxes = document.querySelectorAll('input[type="checkbox"]');
                    checkboxes.forEach(function(checkbox) {{
                        if (checkbox.parentElement && checkbox.parentElement.textContent.includes('⚠️ Siniestros')) {{
                            checkbox.addEventListener("change", onCapaSiniestrosChange);
                        }}
                    }});
                    onCapaSiniestrosChange();
                }}, 1000);
            }});

            document.getElementById("causaSiniestroSelect").addEventListener("keypress", function(e) {{
                if (e.key === "Enter") {{
                    filtrarSiniestros();
                }}
            }});
            </script>
            '''

            agregar_html_seguro(m, buscador_siniestros_html)

    # ========== CAPA DE FOTOS DESDE GITHUB (VERSIÓN SIMPLIFICADA) ==========
    print("📸 Configurando capa de fotos desde GitHub...")
    
    # URL del archivo de fotos en GitHub
    GITHUB_USER = "franciscotomatis"
    REPO_NAME = "APP-C-rdoba"
    FOTOS_JSON_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/fotos.json"

    print(f"✅ Fotos se cargarán desde: {FOTOS_JSON_URL}")

    # Crear capa vacía para fotos
    fotos_layer = folium.FeatureGroup(name='📸 Fotos del perito', show=True)
    fotos_layer.add_to(m)

    print("✅ Sistema de carga de fotos desde GitHub configurado")

    # ========== CAPAS WMS (IDÉNTICAS) ==========
    print("\n" + "="*60)
    print("📡 AGREGANDO CAPAS WMS (IDÉNTICAS A COLAB)")
    print("="*60)

    # IMERG DIARIO
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

    # HUMEDAD DE SUELO
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

    # TVDI MODIS
    try:
        url_wms = "https://aplicaciones.gulich.unc.edu.ar/geoserver/ows"
        wms = WebMapService(url_wms, version='1.3.0')
        
        config_capas = [
            {
                "nombre": "tvdi_m_2024:tvdi_2025361_modis",
                "simbolo": "📊",
                "nombre_display": "TVDI",
                "opacidad": 0.75
            },
            {
                "nombre": "tvdi_anomsindex_m_2024:anomtvdi_2025361_anomindex_modis",
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

    # ========== LEYENDAS (SIMPLIFICADAS PARA EVITAR JINJA2) ==========
    
    # URLs de leyendas
    url_leyenda_normal = "https://aplicaciones.gulich.unc.edu.ar/geoserver/ows?service=WMS&version=1.3.0&request=GetLegendGraphic&format=image/png&layer=tvdi_m_2024:tvdi_2025361_modis&style=tvdi61"
    url_leyenda_anomalia = "https://aplicaciones.gulich.unc.edu.ar/geoserver/ows?service=WMS&version=1.3.0&request=GetLegendGraphic&format=image/png&layer=tvdi_anomsindex_m_2024:anomtvdi_2025361_anomindex_modis&style=anomaliasTVDIindex"
    url_leyenda_imerg = "https://geoservicios2.conae.gov.ar/geoserver/PrecipitacionAcumulada/wms?service=WMS&version=1.3.0&request=GetLegendGraphic&format=image/png&layer=MOM_GPMIMERG_PA1D_1&style=estilo_MOM_CMORPH2_PA1D"
    
    # LEYENDA NORMAL TVDI (SIMPLIFICADA)
    leyenda_normal_html = f'''
    <div id="leyendaNormal" style="position: fixed;
            bottom: 120px; left: 10px;
            background-color: white;
            padding: 8px;
            border-radius: 6px;
            border: 2px solid #9C27B0;
            z-index: 9996;
            width: 160px;
            display: none;
            box-shadow: 0 4px 15px rgba(0,0,0,0.25);">

        <div style="display: flex; justify-content: space-between; 
                    align-items: center; margin-bottom: 8px; padding-bottom: 6px;
                    border-bottom: 1px solid #e0e0e0;">
            <div style="font-size: 11px; font-weight: bold; color: #9C27B0;">
                📊 TVDI
            </div>
            <button onclick="ocultarLeyenda('normal')"
                    style="background: none; border: none; color: #666;
                           font-size: 16px; cursor: pointer; padding: 0;
                           line-height: 1; width: 20px; height: 20px;
                           display: flex; align-items: center; justify-content: center;
                           border-radius: 2px;"
                    title="Cerrar leyenda">
                ×
            </button>
        </div>

        <div style="text-align: center; background-color: white; padding: 5px; border-radius: 4px;">
            <img src="{url_leyenda_normal}" 
                 alt="Leyenda TVDI Normal"
                 style="max-width: 100%; 
                        height: auto;
                        border-radius: 3px;
                        display: block;">
        </div>
    </div>

    <div id="btnLeyendaNormal" style="position: fixed;
            bottom: 85px; left: 10px;
            background-color: #9C27B0;
            color: white;
            padding: 6px 10px;
            border-radius: 5px;
            z-index: 9996;
            cursor: pointer;
            font-family: Arial, sans-serif;
            font-size: 10px;
            display: none;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
            align-items: center;
            gap: 5px;
            border: 1px solid #7B1FA2;"
            onclick="mostrarLeyenda('normal')"
            title="Mostrar leyenda TVDI Normal">
        <span style="font-size: 12px;">📊</span>
        <span style="color: white;">Leyenda</span>
    </div>
    '''
    
    agregar_html_seguro(m, leyenda_normal_html)
    
    # LEYENDA ANOMALÍA TVDI (SIMPLIFICADA)
    leyenda_anomalia_html = f'''
    <div id="leyendaAnomalia" style="position: fixed;
            bottom: 120px; left: 10px;
            background-color: white;
            padding: 8px;
            border-radius: 6px;
            border: 2px solid #FF9800;
            z-index: 9996;
            width: 160px;
            display: none;
            box-shadow: 0 4px 15px rgba(0,0,0,0.25);">
        
        <div style="display: flex; justify-content: space-between; 
                    align-items: center; margin-bottom: 8px; padding-bottom: 6px;
                    border-bottom: 1px solid #e0e0e0;">
            <div style="font-size: 11px; font-weight: bold; color: #FF9800;">
                🟡 Anomalía
            </div>
            <button onclick="ocultarLeyenda('anomalia')"
                    style="background: none; border: none; color: #666;
                           font-size: 16px; cursor: pointer; padding: 0;
                           line-height: 1; width: 20px; height: 20px;
                           display: flex; align-items: center; justify-content: center;
                           border-radius: 2px;"
                    title="Cerrar leyenda">
                ×
            </button>
        </div>

        <div style="text-align: center; background-color: white; padding: 5px; border-radius: 4px;">
            <img src="{url_leyenda_anomalia}" 
                 alt="Leyenda TVDI Anomalía"
                 style="max-width: 100%; 
                        height: auto;
                        border-radius: 3px;
                        display: block;">
        </div>
    </div>

    <div id="btnLeyendaAnomalia" style="position: fixed;            bottom: 85px; left: 10px;
            background-color: #FF9800;
            color: white;
            padding: 6px 10px;
            border-radius: 5px;
            z-index: 9996;
            cursor: pointer;
            font-family: Arial, sans-serif;
            font-size: 10px;
            display: none;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
            align-items: center;
            gap: 5px;
            border: 1px solid #F57C00;"
            onclick="mostrarLeyenda('anomalia')"
            title="Mostrar leyenda TVDI Anomalía">
        <span style="font-size: 12px;">🟡</span>
        <span style="color: white;">Leyenda</span>
    </div>
    '''
    
    agregar_html_seguro(m, leyenda_anomalia_html)
    
    # LEYENDA IMERG (SIMPLIFICADA)
    leyenda_imerg_html = f'''
    <div id="leyendaImerg" style="position: fixed;
            bottom: 120px; left: 10px;
            background-color: white;
            padding: 8px;
            border-radius: 6px;
            border: 2px solid #1E88E5;
            z-index: 9996;
            width: 160px;
            display: none;
            box-shadow: 0 4px 15px rgba(0,0,0,0.25);">
    
        <div style="display: flex; justify-content: space-between; 
                    align-items: center; margin-bottom: 8px; padding-bottom: 6px;
                    border-bottom: 1px solid #e0e0e0;">
            <div style="font-size: 11px; font-weight: bold; color: #1E88E5;">
                🌧️ Precipitación IMERG
            </div>
            <button onclick="ocultarLeyenda('imerg')"
                    style="background: none; border: none; color: #666;
                           font-size: 16px; cursor: pointer; padding: 0;
                           line-height: 1; width: 20px; height: 20px;
                           display: flex; align-items: center; justify-content: center;
                           border-radius: 2px;"
                    title="Cerrar leyenda">
                ×
            </button>
        </div>
    
        <div style="text-align: center; background-color: white; padding: 5px; border-radius: 4px;">
            <img src="{url_leyenda_imerg}" 
                 alt="Leyenda Precipitación IMERG"
                 style="max-width: 70%; 
                        height: auto;
                        border-radius: 3px;
                        display: block;">
        </div>
    </div>
    
    <div id="btnLeyendaImerg" style="position: fixed;
            bottom: 85px; left: 10px;
            background-color: #1E88E5;
            color: white;
            padding: 6px 10px;
            border-radius: 5px;
            z-index: 9996;
            cursor: pointer;
            font-family: Arial, sans-serif;
            font-size: 10px;
            display: none;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
            align-items: center;
            gap: 5px;
            border: 1px solid #0D47A1;"
            onclick="mostrarLeyenda('imerg')"
            title="Mostrar leyenda Precipitación IMERG">
        <span style="font-size: 12px;">🌧️</span>
        <span style="color: white;">Leyenda</span>
    </div>
    '''
    
    agregar_html_seguro(m, leyenda_imerg_html)
    
    # LEYENDA HUMEDAD SUELO (SIMPLIFICADA)
    leyenda_humedad_html = '''
    <div id="leyendaHumedad" style="position: fixed;
            bottom: 120px; left: 10px;
            background-color: white;
            padding: 10px 12px;
            border-radius: 6px;
            border: 2px solid #795548;
            z-index: 9996;
            font-family: Arial, sans-serif;
            font-size: 11px;
            width: 140px;
            display: none;
            box-shadow: 0 4px 15px rgba(0,0,0,0.25);">
    
        <div style="font-weight: bold; color: #795548;
                    margin-bottom: 8px; border-bottom: 2px solid #795548;
                    padding-bottom: 6px; font-size: 10px;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 6px;">
                    <span>💧</span>
                    <span>Humedad Suelo (%)</span>
                </div>
                <button onclick="ocultarLeyenda('humedad')"
                        style="background: none; border: none; color: #795548;
                               font-size: 16px; cursor: pointer; padding: 0;
                               line-height: 1;">×</button>
            </div>
        </div>
    
        <div style="margin-bottom: 10px;">
            <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <div style="width: 16px; height: 16px; background-color: #FF0000;
                            margin-right: 8px; border: 1px solid #CC0000; border-radius: 3px;"></div>
                <div style="flex: 1; display: flex; justify-content: space-between;">
                    <span style="font-size: 9px;">0%</span>
                    <span style="font-size: 9px;">2%</span>
                </div>
            </div>
    
            <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <div style="width: 16px; height: 16px; background-color: #FF6600;
                            margin-right: 8px; border: 1px solid #CC5500; border-radius: 3px;"></div>
                <div style="flex: 1; display: flex; justify-content: space-between;">
                    <span style="font-size: 9px;">2%</span>
                    <span style="font-size: 9px;">5%</span>
                </div>
            </div>
    
            <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <div style="width: 16px; height: 16px; background-color: #FFCC00;
                            margin-right: 8px; border: 1px solid #CCA300; border-radius: 3px;"></div>
                <div style="flex: 1; display: flex; justify-content: space-between;">
                    <span style="font-size: 9px;">5%</span>
                    <span style="font-size: 9px;">10%</span>
                </div>
            </div>
    
            <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <div style="width: 16px; height: 16px; background-color: #00FF00;
                            margin-right: 8px; border: 1px solid #00CC00; border-radius: 3px;"></div>
                <div style="flex: 1; display: flex; justify-content: space-between;">
                    <span style="font-size: 9px;">10%</span>
                    <span style="font-size: 9px;">20%</span>
                </div>
            </div>
    
            <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <div style="width: 16px; height: 16px; background-color: #00FFFF;
                            margin-right: 8px; border: 1px solid #00CCCC; border-radius: 3px;"></div>
                <div style="flex: 1; display: flex; justify-content: space-between;">
                    <span style="font-size: 9px;">20%</span>
                    <span style="font-size: 9px;">30%</span>
                </div>
            </div>
    
            <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <div style="width: 16px; height: 16px; background-color: #0066FF;
                            margin-right: 8px; border: 1px solid #0055CC; border-radius: 3px;"></div>
                <div style="flex: 1; display: flex; justify-content: space-between;">
                    <span style="font-size: 9px;">30%</span>
                    <span style="font-size: 9px;">45%</span>
                </div>
            </div>
    
            <div style="display: flex; align-items: center;">
                <div style="width: 16px; height: 16px; background-color: #0000FF;
                            margin-right: 8px; border: 1px solid #0000CC; border-radius: 3px;"></div>
                <div style="flex: 1; display: flex; justify-content: space-between;">
                    <span style="font-size: 9px; font-weight: bold;">> 45%</span>
                    <span style="font-size: 9px;"></span>
                </div>
            </div>
        </div>
    </div>
    
    <div id="btnLeyendaHumedad" style="position: fixed;
            bottom: 85px; left: 180px;
            background-color: #795548;
            color: white;
            padding: 6px 10px;
            border-radius: 5px;
            z-index: 9996;
            cursor: pointer;
            font-family: Arial, sans-serif;
            font-size: 10px;
            display: none;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
            align-items: center;
            gap: 5px;
            border: 1px solid #5D4037;"
            onclick="mostrarLeyenda('humedad')"
            title="Mostrar leyenda Humedad de Suelo">
        <span style="font-size: 12px;">💧</span>
        <span style="color: white;">Leyenda</span>
    </div>
    '''
    
    agregar_html_seguro(m, leyenda_humedad_html)
    
    # LEYENDA SINIESTROS (SOLO SI HAY SINIESTROS)
    if campos['causa_stro'] and gdf[campos['causa_stro']].notna().any():
        leyenda_siniestros_boton = '''
        <div id="btnLeyendaSiniestros" style="position: fixed;
                bottom: 85px; left: 180px;
                background-color: #F44336;
                color: white;
                padding: 6px 10px;
                border-radius: 5px;
                z-index: 9996;
                cursor: pointer;
                font-family: Arial, sans-serif;
                font-size: 10px;
                display: none;
                box-shadow: 0 2px 6px rgba(0,0,0,0.2);
                align-items: center;
                gap: 5px;
                border: 1px solid #D32F2F;"
                onclick="mostrarLeyenda('siniestros')"
                title="Mostrar leyenda de Siniestros">
            <span style="font-size: 12px;">⚠️</span>
            <span style="color: white;">Leyenda</span>
        </div>
        
        <div id="leyendaSiniestros" style="position: fixed;
                bottom: 120px; left: 180px;
                background-color: white;
                padding: 10px 12px;
                border-radius: 8px;
                border: 2px solid #F44336;
                z-index: 9996;
                font-family: Arial, sans-serif;
                font-size: 11px;
                width: 140px;
                display: none;
                box-shadow: 0 4px 15px rgba(0,0,0,0.25);">
    
            <div style="display: flex; justify-content: space-between; 
                        align-items: center; margin-bottom: 8px; padding-bottom: 6px;
                        border-bottom: 1px solid #e0e0e0;">
                <div style="font-size: 11px; font-weight: bold; color: #F44336;">
                    ⚠️ Siniestros
                </div>
                <button onclick="ocultarLeyenda('siniestros')"
                        style="background: none; border: none; color: #666;
                               font-size: 16px; cursor: pointer; padding: 0;
                               line-height: 1; width: 20px; height: 20px;
                               display: flex; align-items: center; justify-content: center;
                               border-radius: 2px;"
                        title="Cerrar leyenda">
                    ×
                </button>
            </div>
    
            <div style="margin-bottom: 8px;">
                <div style="display: flex; align-items: center; margin-bottom: 4px;">
                    <div style="width: 14px; height: 14px; background-color: #00BCD4;
                                margin-right: 8px; border: 1px solid #0097A7; border-radius: 3px;"></div>
                    <div style="flex: 1; font-size: 10px;">Granizo</div>
                </div>
    
                <div style="display: flex; align-items: center; margin-bottom: 4px;">
                    <div style="width: 14px; height: 14px; background-color: #FF5252;
                                margin-right: 8px; border: 1px solid #D50000; border-radius: 3px;"></div>
                    <div style="flex: 1; font-size: 10px;">Sequía</div>
                </div>
    
                <div style="display: flex; align-items: center; margin-bottom: 4px;">
                    <div style="width: 14px; height: 14px; background-color: #448AFF;
                                margin-right: 8px; border: 1px solid #2979FF; border-radius: 3px;"></div>
                    <div style="flex: 1; font-size: 10px;">Inundación</div>
                </div>
    
                <div style="display: flex; align-items: center; margin-bottom: 4px;">
                    <div style="width: 14px; height: 14px; background-color: #7C4DFF;
                                margin-right: 8px; border: 1px solid #651FFF; border-radius: 3px;"></div>
                    <div style="flex: 1; font-size: 10px;">Viento</div>
                </div>
    
                <div style="display: flex; align-items: center; margin-bottom: 4px;">
                    <div style="width: 14px; height: 14px; background-color: #795548;
                                margin-right: 8px; border: 1px solid #5D4037; border-radius: 3px;"></div>
                    <div style="flex: 1; font-size: 10px;">Incendio</div>
                </div>
    
                <div style="display: flex; align-items: center;">
                    <div style="width: 14px; height: 14px; background-color: #FFFFFF;
                                margin-right: 8px; border: 1px solid #E0E0E0; border-radius: 3px;"></div>
                    <div style="flex: 1; font-size: 10px;">Helada</div>
                </div>
            </div>
        </div>
        '''
        
        agregar_html_seguro(m, leyenda_siniestros_boton)

    # ========== JAVASCRIPT PARA LEYENDAS (SIMPLIFICADO) ==========
    js_leyendas_completo = '''
    <script>
    // FUNCIONES SIMPLIFICADAS PARA LEYENDAS
    function mostrarLeyenda(tipo) {
        console.log("Mostrando leyenda:", tipo);
        ocultarTodasLeyendas();
        
        switch(tipo) {
            case 'normal':
                document.getElementById("leyendaNormal").style.display = "block";
                document.getElementById("btnLeyendaNormal").style.display = "none";
                break;
            case 'anomalia':
                document.getElementById("leyendaAnomalia").style.display = "block";
                document.getElementById("btnLeyendaAnomalia").style.display = "none";
                break;
            case 'imerg':
                document.getElementById("leyendaImerg").style.display = "block";
                document.getElementById("btnLeyendaImerg").style.display = "none";
                break;
            case 'humedad':
                document.getElementById("leyendaHumedad").style.display = "block";
                document.getElementById("btnLeyendaHumedad").style.display = "none";
                break;
            case 'siniestros':
                document.getElementById("leyendaSiniestros").style.display = "block";
                document.getElementById("btnLeyendaSiniestros").style.display = "none";
                break;
        }
    }
    
    function ocultarLeyenda(tipo) {
        console.log("Ocultando leyenda:", tipo);
        switch(tipo) {
            case 'normal':
                document.getElementById("leyendaNormal").style.display = "none";
                document.getElementById("btnLeyendaNormal").style.display = "flex";
                break;
            case 'anomalia':
                document.getElementById("leyendaAnomalia").style.display = "none";
                document.getElementById("btnLeyendaAnomalia").style.display = "flex";
                break;
            case 'imerg':
                document.getElementById("leyendaImerg").style.display = "none";
                document.getElementById("btnLeyendaImerg").style.display = "flex";
                break;
            case 'humedad':
                document.getElementById("leyendaHumedad").style.display = "none";
                document.getElementById("btnLeyendaHumedad").style.display = "flex";
                break;
            case 'siniestros':
                document.getElementById("leyendaSiniestros").style.display = "none";
                document.getElementById("btnLeyendaSiniestros").style.display = "flex";
                break;
        }
    }
    
    // FUNCIÓN PARA OCULTAR TODAS
    function ocultarTodasLeyendas() {
        document.getElementById("leyendaNormal").style.display = "none";
        document.getElementById("leyendaAnomalia").style.display = "none";
        document.getElementById("leyendaImerg").style.display = "none";
        document.getElementById("leyendaHumedad").style.display = "none";
        document.getElementById("leyendaSiniestros").style.display = "none";
        
        document.getElementById("btnLeyendaNormal").style.display = "none";
        document.getElementById("btnLeyendaAnomalia").style.display = "none";
        document.getElementById("btnLeyendaImerg").style.display = "none";
        document.getElementById("btnLeyendaHumedad").style.display = "none";
        document.getElementById("btnLeyendaSiniestros").style.display = "none";
    }
    
    // SISTEMA INTELIGENTE PARA DETECTAR CAPAS WMS
    function detectarCapasWMS() {
        console.log("=== DETECTANDO CAPAS WMS ===");
        
        var checkboxes = document.querySelectorAll('input[type="checkbox"]');
        var imergActiva = false;
        var humedadActiva = false;
        var tvdiNormalActiva = false;
        var tvdiAnomaliaActiva = false;
        var siniestrosActiva = false;
        
        checkboxes.forEach(function(checkbox) {
            var label = checkbox.parentElement;
            if (label && label.textContent) {
                var texto = label.textContent.trim();
                
                if ((texto.includes("🌧️ PP") || texto.includes("IMERG")) && 
                    !texto.includes("CHIRPS")) {
                    if (checkbox.checked) imergActiva = true;
                }
                
                if (texto.includes("💧 Humedad") || texto.includes("Humedad")) {
                    if (checkbox.checked) humedadActiva = true;
                }
                
                if ((texto.includes("TVDI") || texto.includes("📊")) && 
                    !texto.includes("Anomalía") && 
                    !texto.includes("🟡") &&
                    !texto.includes("anom")) {
                    if (checkbox.checked) tvdiNormalActiva = true;
                }
                
                if (texto.includes("Anomalía") || 
                    texto.includes("🟡") || 
                    texto.includes("anom") ||
                    texto.toLowerCase().includes("anomalia")) {
                    if (checkbox.checked) tvdiAnomaliaActiva = true;
                }
                
                if (texto.includes("⚠️ Siniestros")) {
                    if (checkbox.checked) siniestrosActiva = true;
                }
            }
        });
        
        console.log("Resultado: IMERG=" + imergActiva + ", Humedad=" + humedadActiva + 
                   ", TVDI_Normal=" + tvdiNormalActiva + ", TVDI_Anomalia=" + tvdiAnomaliaActiva +
                   ", Siniestros=" + siniestrosActiva);
        
        // Mostrar botones según prioridad
        ocultarTodasLeyendas();
        
        if (imergActiva) {
            document.getElementById("btnLeyendaImerg").style.display = "flex";
        }
        else if (humedadActiva) {
            document.getElementById("btnLeyendaHumedad").style.display = "flex";
        }
        else if (tvdiNormalActiva) {
            document.getElementById("btnLeyendaNormal").style.display = "flex";
        }
        else if (tvdiAnomaliaActiva) {
            document.getElementById("btnLeyendaAnomalia").style.display = "flex";
        }
        else if (siniestrosActiva) {
            document.getElementById("btnLeyendaSiniestros").style.display = "flex";
        }
    }
    
    function inicializarSistemaLeyendasWMS() {
        console.log("🚀 Inicializando sistema de leyendas...");
        
        var checkboxes = document.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(function(checkbox) {
            checkbox.addEventListener("change", function() {
                setTimeout(detectarCapasWMS, 100);
            });
        });
        
        if (typeof map !== "undefined") {
            map.on("overlayadd overlayremove", function(e) {
                console.log("🗺️ Evento mapa:", e.name);
                setTimeout(detectarCapasWMS, 100);
            });
        }
        
        setTimeout(function() {
            console.log("🔍 Estado inicial de capas WMS...");
            detectarCapasWMS();
        }, 2000);
        
        console.log("✅ Sistema de leyendas inicializado");
    }
    
    document.addEventListener("DOMContentLoaded", inicializarSistemaLeyendasWMS);
    
    if (typeof map !== "undefined") {
        map.whenReady(inicializarSistemaLeyendasWMS);
    }
    
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            ocultarTodasLeyendas();
            setTimeout(detectarCapasWMS, 100);
        }
    });
    </script>
    '''
    
    agregar_html_seguro(m, js_leyendas_completo)

    # ========== CONTROLES (IDÉNTICOS) ==========
    folium.LayerControl(position='topright', collapsed=True).add_to(m)
    Fullscreen(
        position='topright',
        title='Pantalla completa',
        title_cancel='Salir pantalla completa'
    ).add_to(m)
    MeasureControl(position='topright').add_to(m)

    # ========== GPS AUTO-ACTIVADO (SIMPLIFICADO) ==========
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
        </script>
        '''
        
        agregar_html_seguro(m, gps_auto_html)
        
    except Exception as e:
        print(f"⚠️  Error GPS: {e}")

    # ========== TÍTULO PRINCIPAL ==========
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
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
            Actualizado: {fecha_actual} • {len(gdf)} polígonos
        </div>
    </div>
    '''
    agregar_html_seguro(m, titulo_html)

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

        agregar_html_seguro(m, leyenda_html)

    # ========== BUSCADOR DE CLIENTES (SIMPLIFICADO) ==========
    if campos['cliente']:
        clientes = sorted(gdf[campos['cliente']].dropna().astype(str).unique())
        
        opciones_clientes = "".join(f'<option value="{cliente}">' for cliente in clientes)
        
        buscador_html = f'''
        <div id="lupitaBuscador" style="position: fixed;
                top: 80px; left: 8px;
                background: linear-gradient(135deg, rgba(250, 249, 246, 0.95), rgba(245, 245, 240, 0.95));
                padding: 10px 12px;
                border-radius: 12px;
                border: 1px solid rgba(212, 212, 212, 0.8);
                z-index: 9998;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 11px;
                width: 220px;
                box-shadow: 0 5px 20px rgba(44, 85, 48, 0.12);">

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
                                  font-size: 11px;">
                    <datalist id="clientesList">
                        {opciones_clientes}
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
                        Filtrar
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
                        Resetear
                    </button>
                </div>

                <div id="estadoFiltro"
                     style="font-size: 9px; 
                            color: #666; 
                            margin-top: 10px;
                            padding: 8px;
                            background: rgba(44, 85, 48, 0.05);
                            border-radius: 6px;">
                    Mostrando {len(gdf)} polígonos
                </div>
            </div>
        </div>

        <script>
        function filtrarCliente() {{
            var valor = document.getElementById("clienteInput").value.toLowerCase();
            if (!valor) return;
            
            var contador = 0;
            var layers = window.geoLayer.getLayers();
            
            layers.forEach(function(layer) {{
                var propiedades = layer.feature.properties;
                var clienteEnPoligono = propiedades["{campos['cliente']}"];
                
                if (clienteEnPoligono && clienteEnPoligono.toString().toLowerCase().includes(valor)) {{
                    layer.setStyle({{
                        fillOpacity: 0.6,
                        weight: 2,
                        opacity: 1
                    }});
                    contador++;
                }} else {{
                    layer.setStyle({{
                        fillOpacity: 0,
                        weight: 0,
                        opacity: 0
                    }});
                }}
            }});
            
            document.getElementById("estadoFiltro").innerHTML = 
                "Mostrando " + contador + " polígonos";
        }}
        
        function resetearFiltro() {{
            document.getElementById("clienteInput").value = "";
            var layers = window.geoLayer.getLayers();
            
            layers.forEach(function(layer) {{
                var propiedades = layer.feature.properties;
                layer.setStyle({{
                    fillColor: propiedades._color_fill || '#9C27B0',
                    color: propiedades._color_border || '#7B1FA2',
                    weight: 2,
                    fillOpacity: 0.6,
                    opacity: 1
                }});
            }});
            
            document.getElementById("estadoFiltro").innerHTML = 
                "Mostrando {len(gdf)} polígonos";
        }}
        
        // Guardar referencia a la capa
        window.geoLayer = {capa_nombre};
        </script>
        '''
        
        agregar_html_seguro(m, buscador_html)

    # ========== PANEL DE COMPARACIÓN POR ZONA (SIMPLIFICADO) ==========
    if campos['zona'] and campos['hectareas']:
        gdf[campos['zona']] = gdf[campos['zona']].astype(str).str.strip()
        hectareas_por_zona = {}
        for zona in gdf[campos['zona']].dropna().unique():
            zona_str = str(zona).strip()
            mascara = gdf[campos['zona']] == zona_str
            hectareas = gdf.loc[mascara, campos['hectareas']].sum()
            hectareas_por_zona[zona_str] = hectareas
        
        hectareas_proyectadas = {
            "1": 84940,
            "2": 155256,
            "3": 158675,
            "4": 134574
        }
        
        total_proyectado = sum(hectareas_proyectadas.values())
        total_actual = sum(hectareas_por_zona.values())
        diferencia_total = total_actual - total_proyectado
        porcentaje_total = (total_actual / total_proyectado * 100) if total_proyectado > 0 else 0
        
        panel_html = f'''
        <div id="btnGraficos" style="position: fixed;
                bottom: 25px; left: 25px;
                background: linear-gradient(135deg, #2C5530, #8A9A5B);
                color: white;
                padding: 12px;
                border-radius: 50%;
                z-index: 9997;
                cursor: pointer;
                box-shadow: 0 5px 15px rgba(44, 85, 48, 0.3);
                font-size: 20px;
                width: 50px;
                height: 50px;
                display: flex;
                align-items: center;
                justify-content: center;"
                onclick="togglePanel()">
            📈
        </div>

        <div id="panelGraficos" style="position: fixed;
                bottom: -300px;
                left: 50%;
                transform: translateX(-50%);
                width: 90%;
                max-width: 600px;
                height: 300px;
                background: white;
                z-index: 10001;
                box-shadow: 0 -5px 20px rgba(0,0,0,0.2);
                border-radius: 15px 15px 0 0;
                transition: bottom 0.3s;
                padding: 20px;
                overflow-y: auto;">
            
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3 style="margin: 0; color: #2C5530;">Comparación por Zona</h3>
                <button onclick="togglePanel()" style="background: none; border: none; font-size: 20px; cursor: pointer;">×</button>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 15px;">
                <div style="background: #f0f9ff; padding: 10px; border-radius: 8px; border-left: 4px solid #2E7D32;">
                    <div style="font-size: 12px; color: #666;">Proyectado</div>
                    <div style="font-size: 18px; font-weight: bold; color: #2E7D32;">{total_proyectado:,.0f} ha</div>
                </div>
                <div style="background: #fff0f0; padding: 10px; border-radius: 8px; border-left: 4px solid #2196F3;">
                    <div style="font-size: 12px; color: #666;">Actual</div>
                    <div style="font-size: 18px; font-weight: bold; color: #2196F3;">{total_actual:,.0f} ha</div>
                </div>
            </div>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 10px;">
                <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                    <thead>
                        <tr style="background: #2C5530; color: white;">
                            <th style="padding: 8px; text-align: left;">Zona</th>
                            <th style="padding: 8px; text-align: right;">Proyectado</th>
                            <th style="padding: 8px; text-align: right;">Actual</th>
                            <th style="padding: 8px; text-align: right;">Diferencia</th>
                        </tr>
                    </thead>
                    <tbody>
        '''
        
        for zona in ["1", "2", "3", "4"]:
            proyectado = hectareas_proyectadas.get(zona, 0)
            real = hectareas_por_zona.get(zona, 0) if zona in hectareas_por_zona else 0
            diferencia = real - proyectado
            
            panel_html += f'''
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 8px;">Zona {zona}</td>
                            <td style="padding: 8px; text-align: right;">{proyectado:,.0f}</td>
                            <td style="padding: 8px; text-align: right;">{real:,.0f}</td>
                            <td style="padding: 8px; text-align: right; color: {'#4CAF50' if diferencia >= 0 else '#f44336'};">
                                {diferencia:+,.0f}
                            </td>
                        </tr>
            '''
        
        panel_html += f'''
                        <tr style="background: #e8f5e8; font-weight: bold;">
                            <td style="padding: 8px;">TOTAL</td>
                            <td style="padding: 8px; text-align: right;">{total_proyectado:,.0f}</td>
                            <td style="padding: 8px; text-align: right;">{total_actual:,.0f}</td>
                            <td style="padding: 8px; text-align: right; color: {'#4CAF50' if diferencia_total >= 0 else '#f44336'};">
                                {diferencia_total:+,.0f} ({porcentaje_total:.1f}%)
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <script>
        function togglePanel() {{
            var panel = document.getElementById("panelGraficos");
            if (panel.style.bottom === "0px") {{
                panel.style.bottom = "-300px";
            }} else {{
                panel.style.bottom = "0px";
            }}
        }}
        </script>
        '''
        
        agregar_html_seguro(m, panel_html)

    # ========== ESTILOS GLOBALES ==========
    estilos_globales = '''
    <style>
        .leaflet-tooltip {
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 6px 10px;
            font-family: Arial, sans-serif;
            font-size: 11px;
        }
        
        .leaflet-popup-content-wrapper {
            border-radius: 10px;
            background: white;
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        }
        
        ::-webkit-scrollbar {
            width: 6px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #2C5530;
            border-radius: 8px;
        }
    </style>
    '''
    
    agregar_html_seguro(m, estilos_globales)

    # ========== PANTALLA DE LOGIN (SIMPLIFICADA) ==========
    login_html = f'''
    <div id="loginScreen" style="position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: linear-gradient(135deg, #2C5530 0%, #8A9A5B 100%);
            z-index: 10000;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;">
            
        <div style="background: white;
                    padding: 30px;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    text-align: center;
                    width: 300px;">
            
            <div style="margin-bottom: 20px;">
                <div style="width: 60px; height: 60px; background: #2C5530;
                        border-radius: 15px; display: flex; align-items: center; justify-content: center;
                        margin: 0 auto 12px;">
                    <span style="color: white; font-size: 28px;">🔐</span>
                </div>
                <h2 style="color: #2C5530; margin-bottom: 5px;">PROGRAMA CÓRDOBA 25/26</h2>
            </div>
            
            <div style="margin-bottom: 15px;">
                <input type="text" id="loginUsuario" placeholder="Usuario"
                       style="width: 100%; padding: 12px; margin-bottom: 10px;
                              border: 2px solid #ddd; border-radius: 8px;">
                <input type="password" id="loginContrasena" placeholder="Contraseña"
                       style="width: 100%; padding: 12px; margin-bottom: 15px;
                              border: 2px solid #ddd; border-radius: 8px;">
                <button onclick="verificarAcceso()"
                        style="width: 100%; background: #2C5530; color: white;
                               border: none; padding: 14px; border-radius: 8px;
                               font-size: 16px; cursor: pointer;">
                    INGRESAR
                </button>
            </div>
            
            <div id="loginError" style="color: #f44336; display: none;">
                ❌ Credenciales incorrectas
            </div>
        </div>
    </div>

    <script>
    const HASH_USUARIO = "{HASH_USUARIO}";
    const HASH_CONTRASENA = "{HASH_CONTRASENA}";
    
    async function calcularHash(texto) {{
        const salt = "ProgramaCordoba25/26-SancorSeguro";
        const encoder = new TextEncoder();
        const data = encoder.encode(texto + salt);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('').substring(0, 16);
    }}
    
    async function verificarAcceso() {{
        const usuario = document.getElementById("loginUsuario").value;
        const contrasena = document.getElementById("loginContrasena").value;
        
        try {{
            const hashUsuario = await calcularHash(usuario);
            const hashContrasena = await calcularHash(contrasena);
            
            if (hashUsuario === HASH_USUARIO && hashContrasena === HASH_CONTRASENA) {{
                document.getElementById("loginScreen").style.display = "none";
            }} else {{
                document.getElementById("loginError").style.display = "block";
            }}
        }} catch (error) {{
            console.error("Error:", error);
        }}
    }}
    
    // Enter para enviar
    document.getElementById("loginContrasena").addEventListener("keypress", function(e) {{
        if (e.key === "Enter") verificarAcceso();
    }});
    </script>
    '''
    
    agregar_html_seguro(m, login_html)

    # ========== AJUSTAR VISTA ==========
    if not gdf.empty:
        m.fit_bounds(bounds)

    # ========== GUARDAR ARCHIVO ==========
    m.save(output_file)
    print(f"✅ Aplicación CORREGIDA guardada como: {output_file}")
    
    return output_file

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("❌ Uso: python generar_app_html.py <ruta_al_geojson> [nombre_salida]")
        print("   Ejemplo: python generar_app_html.py geojson_unificado_actual.geojson app_cordoba_completa.html")
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
        
        # 3. Crear aplicación COMPLETA
        crear_app_completa(geojson_data, gdf, campos, output_file)
        
        print(f"\n{'='*80}")
        print("🎉 APLICACIÓN CORREGIDA GENERADA EXITOSAMENTE")
        print(f"{'='*80}")
        print(f"📁 Archivo: {output_file}")
        print(f"📊 Polígonos: {len(gdf)}")
        print(f"🔐 Usuario: {USUARIO_CORRECTO}")
        print(f"🔐 Contraseña: {CONTRASENA_CORRECTA}")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
           
