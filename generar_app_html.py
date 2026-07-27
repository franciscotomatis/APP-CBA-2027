#!/usr/bin/env python3
"""
GENERADOR DE APLICACIÓN WEB - VERSIÓN PRO
Mantiene TODAS las funcionalidades originales:
- LayerControl (selector de capas a la derecha)
- Buscador de clientes
- Filtros por Cultivo y Siniestro
- Dashboard de comparación por zona
- Modo oscuro/claro
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

print("🔐🌽🌱 GENERADOR PRO - PROGRAMA CÓRDOBA 25/26")
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

    # ========== ESTILOS POR CULTIVO ==========
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

    # ========== CAPA PRINCIPAL ==========
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

    # ========== CAPA DE SINIESTROS ==========
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

    # ========== CAPAS WMS ==========
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

    # ========== LEYENDAS WMS ==========
    url_leyenda_normal = "https://aplicaciones.gulich.unc.edu.ar/geoserver/ows?service=WMS&version=1.3.0&request=GetLegendGraphic&format=image/png&layer=tvdi_m_2024:tvdi_2025361_modis&style=tvdi61"
    url_leyenda_anomalia = "https://aplicaciones.gulich.unc.edu.ar/geoserver/ows?service=WMS&version=1.3.0&request=GetLegendGraphic&format=image/png&layer=tvdi_anomsindex_m_2024:anomtvdi_2025361_anomindex_modis&style=anomaliasTVDIindex"
    url_leyenda_imerg = "https://geoservicios2.conae.gov.ar/geoserver/PrecipitacionAcumulada/wms?service=WMS&version=1.3.0&request=GetLegendGraphic&format=image/png&layer=MOM_GPMIMERG_PA1D_1&style=estilo_MOM_CMORPH2_PA1D"
    
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
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid #e0e0e0;">
            <div style="font-size: 11px; font-weight: bold; color: #9C27B0;">📊 TVDI</div>
            <button onclick="ocultarLeyendaTvdi('normal')" style="background: none; border: none; color: #666; font-size: 16px; cursor: pointer; padding: 0; line-height: 1; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; border-radius: 2px;" title="Cerrar leyenda">×</button>
        </div>
        <div style="text-align: center; background-color: white; padding: 5px; border-radius: 4px;">
            <img src="{url_leyenda_normal}" alt="Leyenda TVDI Normal" style="max-width: 100%; height: auto; border-radius: 3px; display: block;">
        </div>
    </div>
    <div id="btnLeyendaNormal" style="position: fixed; bottom: 85px; left: 10px; background-color: #9C27B0; color: white; padding: 6px 10px; border-radius: 5px; z-index: 9996; cursor: pointer; font-family: Arial, sans-serif; font-size: 10px; display: none; box-shadow: 0 2px 6px rgba(0,0,0,0.2); align-items: center; gap: 5px; border: 1px solid #7B1FA2;" onclick="mostrarLeyendaTvdi('normal')" onmouseover="this.style.backgroundColor='#7B1FA2'; this.style.transform='translateY(-1px)';" onmouseout="this.style.backgroundColor='#9C27B0'; this.style.transform='translateY(0)';">
        <span style="font-size: 12px;">📊</span><span style="color: white;">Leyenda</span>
    </div>
    '''
    
    leyenda_anomalia_html = f'''
    <div id="leyendaAnomalia" style="position: fixed; bottom: 120px; left: 10px; background-color: white; padding: 8px; border-radius: 6px; border: 2px solid #FF9800; z-index: 9996; width: 160px; display: none; box-shadow: 0 4px 15px rgba(0,0,0,0.25);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid #e0e0e0;">
            <div style="font-size: 11px; font-weight: bold; color: #FF9800;">🟡 Anomalía</div>
            <button onclick="ocultarLeyendaTvdi('anomalia')" style="background: none; border: none; color: #666; font-size: 16px; cursor: pointer; padding: 0; line-height: 1; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; border-radius: 2px;" title="Cerrar leyenda">×</button>
        </div>
        <div style="text-align: center; background-color: white; padding: 5px; border-radius: 4px;">
            <img src="{url_leyenda_anomalia}" alt="Leyenda TVDI Anomalía" style="max-width: 100%; height: auto; border-radius: 3px; display: block;">
        </div>
    </div>
    <div id="btnLeyendaAnomalia" style="position: fixed; bottom: 85px; left: 10px; background-color: #FF9800; color: white; padding: 6px 10px; border-radius: 5px; z-index: 9996; cursor: pointer; font-family: Arial, sans-serif; font-size: 10px; display: none; box-shadow: 0 2px 6px rgba(0,0,0,0.2); align-items: center; gap: 5px; border: 1px solid #F57C00;" onclick="mostrarLeyendaTvdi('anomalia')" onmouseover="this.style.backgroundColor='#F57C00'; this.style.transform='translateY(-1px)';" onmouseout="this.style.backgroundColor='#FF9800'; this.style.transform='translateY(0)';">
        <span style="font-size: 12px;">🟡</span><span style="color: white;">Leyenda</span>
    </div>
    '''
    
    leyenda_imerg_html = f'''
    <div id="leyendaImerg" style="position: fixed; bottom: 120px; left: 10px; background-color: white; padding: 8px; border-radius: 6px; border: 2px solid #1E88E5; z-index: 9996; width: 160px; display: none; box-shadow: 0 4px 15px rgba(0,0,0,0.25);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid #e0e0e0;">
            <div style="font-size: 11px; font-weight: bold; color: #1E88E5;">🌧️ Precipitación IMERG</div>
            <button onclick="ocultarLeyendaImerg()" style="background: none; border: none; color: #666; font-size: 16px; cursor: pointer; padding: 0; line-height: 1; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; border-radius: 2px;" title="Cerrar leyenda">×</button>
        </div>
        <div style="text-align: center; background-color: white; padding: 5px; border-radius: 4px;">
            <img src="{url_leyenda_imerg}" alt="Leyenda Precipitación IMERG" style="max-width: 70%; height: auto; border-radius: 3px; display: block;">
        </div>
    </div>
    <div id="btnLeyendaImerg" style="position: fixed; bottom: 85px; left: 10px; background-color: #1E88E5; color: white; padding: 6px 10px; border-radius: 5px; z-index: 9996; cursor: pointer; font-family: Arial, sans-serif; font-size: 10px; display: none; box-shadow: 0 2px 6px rgba(0,0,0,0.2); align-items: center; gap: 5px; border: 1px solid #0D47A1;" onclick="mostrarLeyendaImerg()" onmouseover="this.style.backgroundColor='#0D47A1'; this.style.transform='translateY(-1px)';" onmouseout="this.style.backgroundColor='#1E88E5'; this.style.transform='translateY(0)';">
        <span style="font-size: 12px;">🌧️</span><span style="color: white;">Leyenda</span>
    </div>
    '''
    
    leyenda_humedad_html = '''
    <div id="leyendaHumedad" style="position: fixed; bottom: 120px; left: 10px; background-color: white; padding: 10px 12px; border-radius: 6px; border: 2px solid #795548; z-index: 9996; font-family: Arial, sans-serif; font-size: 11px; width: 140px; display: none; box-shadow: 0 4px 15px rgba(0,0,0,0.25);">
        <div style="font-weight: bold; color: #795548; margin-bottom: 8px; border-bottom: 2px solid #795548; padding-bottom: 6px; font-size: 10px;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 6px;"><span>💧</span><span>Humedad Suelo (%)</span></div>
                <button onclick="ocultarLeyendaHumedad()" style="background: none; border: none; color: #795548; font-size: 16px; cursor: pointer; padding: 0; line-height: 1;">×</button>
            </div>
        </div>
        <div style="margin-bottom: 10px;">
            <div style="display: flex; align-items: center; margin-bottom: 4px;"><div style="width: 16px; height: 16px; background-color: #FF0000; margin-right: 8px; border: 1px solid #CC0000; border-radius: 3px;"></div><div style="flex: 1; display: flex; justify-content: space-between;"><span style="font-size: 9px;">0%</span><span style="font-size: 9px;">2%</span></div></div>
            <div style="display: flex; align-items: center; margin-bottom: 4px;"><div style="width: 16px; height: 16px; background-color: #FF6600; margin-right: 8px; border: 1px solid #CC5500; border-radius: 3px;"></div><div style="flex: 1; display: flex; justify-content: space-between;"><span style="font-size: 9px;">2%</span><span style="font-size: 9px;">5%</span></div></div>
            <div style="display: flex; align-items: center; margin-bottom: 4px;"><div style="width: 16px; height: 16px; background-color: #FFCC00; margin-right: 8px; border: 1px solid #CCA300; border-radius: 3px;"></div><div style="flex: 1; display: flex; justify-content: space-between;"><span style="font-size: 9px;">5%</span><span style="font-size: 9px;">10%</span></div></div>
            <div style="display: flex; align-items: center; margin-bottom: 4px;"><div style="width: 16px; height: 16px; background-color: #00FF00; margin-right: 8px; border: 1px solid #00CC00; border-radius: 3px;"></div><div style="flex: 1; display: flex; justify-content: space-between;"><span style="font-size: 9px;">10%</span><span style="font-size: 9px;">20%</span></div></div>
            <div style="display: flex; align-items: center; margin-bottom: 4px;"><div style="width: 16px; height: 16px; background-color: #00FFFF; margin-right: 8px; border: 1px solid #00CCCC; border-radius: 3px;"></div><div style="flex: 1; display: flex; justify-content: space-between;"><span style="font-size: 9px;">20%</span><span style="font-size: 9px;">30%</span></div></div>
            <div style="display: flex; align-items: center; margin-bottom: 4px;"><div style="width: 16px; height: 16px; background-color: #0066FF; margin-right: 8px; border: 1px solid #0055CC; border-radius: 3px;"></div><div style="flex: 1; display: flex; justify-content: space-between;"><span style="font-size: 9px;">30%</span><span style="font-size: 9px;">45%</span></div></div>
            <div style="display: flex; align-items: center;"><div style="width: 16px; height: 16px; background-color: #0000FF; margin-right: 8px; border: 1px solid #0000CC; border-radius: 3px;"></div><div style="flex: 1; display: flex; justify-content: space-between;"><span style="font-size: 9px; font-weight: bold;">> 45%</span><span style="font-size: 9px;"></span></div></div>
        </div>
    </div>
    <div id="btnLeyendaHumedad" style="position: fixed; bottom: 85px; left: 10px; background-color: #795548; color: white; padding: 6px 10px; border-radius: 5px; z-index: 9996; cursor: pointer; font-family: Arial, sans-serif; font-size: 10px; display: none; box-shadow: 0 2px 6px rgba(0,0,0,0.2); align-items: center; gap: 5px; border: 1px solid #5D4037;" onclick="mostrarLeyendaHumedad()" onmouseover="this.style.backgroundColor='#5D4037'; this.style.transform='translateY(-1px)';" onmouseout="this.style.backgroundColor='#795548'; this.style.transform='translateY(0)';">
        <span style="font-size: 12px;">💧</span><span style="color: white;">Leyenda</span>
    </div>
    '''
    
    agregar_elemento_html_seguro(m, leyenda_normal_html)
    agregar_elemento_html_seguro(m, leyenda_anomalia_html)
    agregar_elemento_html_seguro(m, leyenda_imerg_html)
    agregar_elemento_html_seguro(m, leyenda_humedad_html)

    # ========== JAVASCRIPT PARA LEYENDAS ==========
    js_leyendas = '''
    <script>
    function mostrarLeyendaTvdi(tipo) {
        console.log("Mostrando leyenda TVDI:", tipo);
        ocultarTodasLeyendas();
        if (tipo === 'normal') {
            document.getElementById("leyendaNormal").style.display = "block";
            document.getElementById("btnLeyendaNormal").style.display = "none";
        } else if (tipo === 'anomalia') {
            document.getElementById("leyendaAnomalia").style.display = "block";
            document.getElementById("btnLeyendaAnomalia").style.display = "none";
        }
    }
    function ocultarLeyendaTvdi(tipo) {
        if (tipo === 'normal') {
            document.getElementById("leyendaNormal").style.display = "none";
            document.getElementById("btnLeyendaNormal").style.display = "flex";
        } else if (tipo === 'anomalia') {
            document.getElementById("leyendaAnomalia").style.display = "none";
            document.getElementById("btnLeyendaAnomalia").style.display = "flex";
        }
    }
    function mostrarLeyendaImerg() {
        document.getElementById("leyendaImerg").style.display = "block";
        document.getElementById("btnLeyendaImerg").style.display = "none";
    }
    function ocultarLeyendaImerg() {
        document.getElementById("leyendaImerg").style.display = "none";
        document.getElementById("btnLeyendaImerg").style.display = "flex";
    }
    function mostrarLeyendaHumedad() {
        document.getElementById("leyendaHumedad").style.display = "block";
        document.getElementById("btnLeyendaHumedad").style.display = "none";
    }
    function ocultarLeyendaHumedad() {
        document.getElementById("leyendaHumedad").style.display = "none";
        document.getElementById("btnLeyendaHumedad").style.display = "flex";
    }
    function ocultarTodasLeyendas() {
        document.getElementById("leyendaNormal").style.display = "none";
        document.getElementById("leyendaAnomalia").style.display = "none";
        document.getElementById("leyendaImerg").style.display = "none";
        document.getElementById("leyendaHumedad").style.display = "none";
        document.getElementById("btnLeyendaNormal").style.display = "none";
        document.getElementById("btnLeyendaAnomalia").style.display = "none";
        document.getElementById("btnLeyendaImerg").style.display = "none";
        document.getElementById("btnLeyendaHumedad").style.display = "none";
    }
    function detectarCapasWMS() {
        var checkboxes = document.querySelectorAll('input[type="checkbox"]');
        var imergActiva = false, humedadActiva = false, tvdiNormalActiva = false, tvdiAnomaliaActiva = false;
        checkboxes.forEach(function(checkbox) {
            var label = checkbox.parentElement;
            if (label && label.textContent) {
                var texto = label.textContent.trim();
                if ((texto.includes("🌧️ PP") || texto.includes("IMERG")) && !texto.includes("CHIRPS")) {
                    if (checkbox.checked) imergActiva = true;
                }
                if (texto.includes("💧 Humedad") || texto.includes("Humedad")) {
                    if (checkbox.checked) humedadActiva = true;
                }
                if ((texto.includes("TVDI") || texto.includes("📊")) && !texto.includes("Anomalía") && !texto.includes("🟡") && !texto.includes("anom")) {
                    if (checkbox.checked) tvdiNormalActiva = true;
                }
                if (texto.includes("Anomalía") || texto.includes("🟡") || texto.includes("anom") || texto.toLowerCase().includes("anomalia")) {
                    if (checkbox.checked) tvdiAnomaliaActiva = true;
                }
            }
        });
        ocultarTodasLeyendas();
        if (imergActiva) document.getElementById("btnLeyendaImerg").style.display = "flex";
        else if (humedadActiva) document.getElementById("btnLeyendaHumedad").style.display = "flex";
        else if (tvdiNormalActiva) document.getElementById("btnLeyendaNormal").style.display = "flex";
        else if (tvdiAnomaliaActiva) document.getElementById("btnLeyendaAnomalia").style.display = "flex";
    }
    document.addEventListener("DOMContentLoaded", function() {
        document.querySelectorAll('input[type="checkbox"]').forEach(function(cb) {
            cb.addEventListener("change", function() { setTimeout(detectarCapasWMS, 100); });
        });
        setTimeout(detectarCapasWMS, 2000);
    });
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') { ocultarTodasLeyendas(); setTimeout(detectarCapasWMS, 100); }
    });
    </script>
    '''
    agregar_elemento_html_seguro(m, js_leyendas)

    # ========== CONTROLES ==========
    folium.LayerControl(position='topright', collapsed=True).add_to(m)
    Fullscreen(position='topright', title='Pantalla completa', title_cancel='Salir pantalla completa').add_to(m)
    MeasureControl(position='topright').add_to(m)

    # ========== CAPA DE FOTOS ==========
    print("📸 Configurando capa de fotos desde GitHub...")
    GITHUB_USER = "franciscotomatis"
    REPO_NAME = "APP-CBA-2027"
    FOTOS_JSON_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/fotos_metadata/fotos_procesadas.json"
    print(f"✅ Fotos se cargarán desde: {FOTOS_JSON_URL}")

    # ========== OBTENER DATOS PARA LA INTERFAZ ==========
    from datetime import datetime, timezone, timedelta
    hora_argentina = datetime.now(timezone(timedelta(hours=-3)))
    fecha_hora_argentina = hora_argentina.strftime("%d/%m/%Y • %H:%M")
    
    total_poligonos = len(gdf)
    total_hectareas = gdf[campos.get('hectareas', 'HECTAREAS_ASEGURADAS')].sum() if campos.get('hectareas') else 0
    
    # ===== DATOS PARA CULTIVOS =====
    cultivos_unicos = []
    if campos['cultivo'] and campos['cultivo'] in gdf.columns:
        cultivos_unicos = sorted(gdf[campos['cultivo']].dropna().unique())
    
    # ===== DATOS PARA SINIESTROS =====
    causas_unicas = []
    if campos['causa_stro'] and campos['causa_stro'] in gdf.columns:
        causas_unicas = sorted(gdf[campos['causa_stro']].dropna().unique())
    
    # ===== DATOS PARA CLIENTES =====
    clientes_unicos = []
    if campos['cliente'] and campos['cliente'] in gdf.columns:
        clientes_unicos = sorted(gdf[campos['cliente']].dropna().astype(str).unique())
    
    opciones_clientes = "".join(f'<option value="{cliente}">' for cliente in clientes_unicos)
    
    # ===== GENERAR CHECKBOXES DE CULTIVOS =====
    checkboxes_cultivos = ""
    for cultivo in cultivos_unicos:
        cultivo_str = str(cultivo).upper()
        icono = '🌱' if 'SOJA' in cultivo_str else '🌽' if 'MAÍZ' in cultivo_str else '🌾' if 'TRIGO' in cultivo_str else '🌻' if 'GIRASOL' in cultivo_str else '📦'
        checkboxes_cultivos += f'<label class="active"><input type="checkbox" value="{cultivo_str}" checked><span>{icono} {cultivo_str.capitalize()}</span></label>'
    
    # ===== GENERAR CHECKBOXES DE SINIESTROS =====
    checkboxes_siniestros = ""
    for causa in causas_unicas:
        causa_str = str(causa).upper()
        icono = '⚠️' if 'GRANIZO' in causa_str else '🔥' if 'INCENDIO' in causa_str else '💧' if 'INUNDACIÓN' in causa_str or 'INUNDACION' in causa_str else '🌊' if 'VIENTO' in causa_str else '❄️' if 'HELADA' in causa_str else '☀️'
        checkboxes_siniestros += f'<label class="active"><input type="checkbox" value="{causa_str}" checked><span>{icono} {causa_str.capitalize()}</span></label>'

    # ========== INTERFAZ PRO ==========
    interfaz_pro_html = f'''
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
        width: 340px;
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
        transform: translateX(-340px);
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
        border-bottom: 1px solid rgba(255,255,255,0.08);
        padding-bottom: 6px;
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
    
    .filter-group input[type="text"] {{
        width:100%;
        padding:8px 12px;
        border:none;
        border-radius:8px;
        background:rgba(255,255,255,0.08);
        color:white;
        font-size:13px;
        outline:none;
    }}
    
    .filter-group input[type="text"]::placeholder {{
        color: rgba(255,255,255,0.4);
    }}
    
    .filter-group .btn-group {{
        display:flex;
        gap:6px;
        margin-top:8px;
    }}
    
    .filter-group .btn-group button {{
        flex:1;
        padding:8px;
        border:none;
        border-radius:8px;
        cursor:pointer;
        font-size:12px;
        font-weight:600;
    }}
    
    .filter-group .btn-group .btn-primary {{
        background:#2d7d46;
        color:white;
    }}
    
    .filter-group .btn-group .btn-secondary {{
        background:rgba(255,255,255,0.06);
        color:rgba(255,255,255,0.6);
    }}
    
    .filter-group .btn-group .btn-danger {{
        background:#d32f2f;
        color:white;
    }}
    
    .filter-group .estado-filtro {{
        font-size:10px;
        color:rgba(255,255,255,0.5);
        margin-top:6px;
    }}
    
    #map-container {{
        position: fixed;
        top: var(--header-height);
        left: 340px;
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
        left: 350px;
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
        <!-- Estadísticas Generales -->
        <div class="section">
            <div class="section-title">📊 Datos Generales</div>
            <div class="stats-grid">
                <div class="stat-card"><div class="num">{total_poligonos}</div><div class="label">Lotes</div></div>
                <div class="stat-card"><div class="num">{total_hectareas:,.0f}</div><div class="label">Hectáreas</div></div>
                <div class="stat-card"><div class="num" id="totalFotos">0</div><div class="label">Fotos</div></div>
                <div class="stat-card"><div class="num">{len(gdf[campos['zona']].dropna().unique()) if campos['zona'] else 0}</div><div class="label">Zonas</div></div>
            </div>
        </div>
        
        <!-- FILTRO POR CLIENTE -->
        <div class="section">
            <div class="section-title">🔍 Buscar Cliente</div>
            <div class="filter-group">
                <input list="clientesList" id="clienteInput" placeholder="🔍 Escribe o selecciona cliente...">
                <datalist id="clientesList">{opciones_clientes}</datalist>
                <div class="btn-group">
                    <button class="btn-primary" onclick="filtrarCliente()">✓ Filtrar</button>
                    <button class="btn-secondary" onclick="resetearFiltros()">↺ Resetear</button>
                </div>
                <div class="estado-filtro" id="estadoFiltroCliente">Mostrando {total_poligonos} polígonos</div>
            </div>
        </div>
        
        <!-- FILTRO POR CULTIVO -->
        <div class="section">
            <div class="section-title">🌱 Filtro por Cultivo</div>
            <div class="filter-group">
                <div class="checkbox-group" id="cultivoFilters">
                    {checkboxes_cultivos}
                </div>
                <div class="btn-group">
                    <button class="btn-primary" onclick="aplicarFiltroCultivos()">✓ Aplicar</button>
                    <button class="btn-secondary" onclick="resetearFiltros()">↺ Resetear</button>
                </div>
                <div class="estado-filtro" id="estadoFiltroCultivo">Todos los cultivos seleccionados</div>
            </div>
        </div>
        
        <!-- FILTRO POR SINIESTRO -->
        <div class="section">
            <div class="section-title">⚠️ Filtro por Siniestro</div>
            <div class="filter-group">
                <div class="checkbox-group" id="siniestroFilters">
                    {checkboxes_siniestros}
                </div>
                <div class="btn-group">
                    <button class="btn-primary" onclick="aplicarFiltroSiniestros()">✓ Aplicar</button>
                    <button class="btn-secondary" onclick="resetearFiltros()">↺ Resetear</button>
                </div>
                <div class="estado-filtro" id="estadoFiltroSiniestro">Todos los siniestros seleccionados</div>
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
    
    <div id="overlayFoto" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:10001;" onclick="cerrarPanelFoto()"></div>
    
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
    
    function abrirSubirFoto() {{
        document.getElementById('panelSubirFoto').style.display = 'block';
        document.getElementById('overlayFoto').style.display = 'block';
        obtenerUbicacionGPS();
    }}
    
    function cerrarPanelFoto() {{
        document.getElementById('panelSubirFoto').style.display = 'none';
        document.getElementById('overlayFoto').style.display = 'none';
        fotoActual = null;
    }}
    
    // Buscar global
    function buscarGlobal(texto) {{
        if (!texto || texto.length < 3) return;
        document.getElementById('clienteInput').value = texto;
        if (typeof filtrarCliente === 'function') filtrarCliente();
    }}
    
    // ============================================================
    // OBTENER CAPA DE POLÍGONOS
    // ============================================================
    
    function obtenerCapaPoligonos() {{
        if (capaPoligonos) return capaPoligonos;
        if (typeof map !== 'undefined') {{
            for (var key in map._layers) {{
                var layer = map._layers[key];
                if (layer && typeof layer.eachLayer === 'function') {{
                    var count = 0;
                    layer.eachLayer(function() {{ count++; }});
                    if (count > 1000) {{
                        console.log("✅ Capa de polígonos encontrada:", count);
                        capaPoligonos = layer;
                        return layer;
                    }}
                }}
            }}
        }}
        return null;
    }}
    
    function resetearEstilos() {{
        var capa = obtenerCapaPoligonos();
        if (!capa) return;
        capa.eachLayer(function(layer) {{
            layer.setStyle({{
                opacity: 1,
                fillOpacity: 0.6,
                weight: 2,
                color: '#2E7D32'
            }});
            layer.options.interactive = true;
            if (layer._popup) {{
                layer.bindPopup(layer._popup.getContent());
            }}
        }});
    }}
    
    // ============================================================
    // FILTRO POR CLIENTE (el original que ya funciona)
    // ============================================================
    
    function filtrarCliente() {{
        var valor = document.getElementById('clienteInput').value.toLowerCase().trim();
        if (!valor) {{
            resetearFiltros();
            return;
        }}
        var capa = obtenerCapaPoligonos();
        if (!capa) return;
        var contador = 0;
        var bounds = null;
        capa.eachLayer(function(layer) {{
            var props = layer.feature.properties;
            var cliente = (props.CLIENTE || props.cliente || '').toLowerCase();
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
        if (contador > 0 && bounds) map.fitBounds(bounds, {{padding: [50,50]}});
        document.getElementById('estadoFiltroCliente').innerHTML = '🔍 ' + contador + ' clientes encontrados';
    }}
    
    // ============================================================
    // FILTRO POR CULTIVO
    // ============================================================
    
    function aplicarFiltroCultivos() {{
        var seleccionados = [];
        document.querySelectorAll('#cultivoFilters input:checked').forEach(function(el) {{
            seleccionados.push(el.value);
        }});
        var capa = obtenerCapaPoligonos();
        if (!capa) return;
        if (seleccionados.length === 0) {{
            resetearEstilos();
            document.getElementById('estadoFiltroCultivo').innerHTML = 'Todos los cultivos';
            return;
        }}
        var contador = 0;
        var bounds = null;
        capa.eachLayer(function(layer) {{
            var props = layer.feature.properties;
            var cultivo = (props.CULTIVO || props.cultivo || '').toUpperCase();
            if (seleccionados.includes(cultivo)) {{
                layer.setStyle({{ opacity: 1, fillOpacity: 0.8, weight: 2, color: '#4CAF50' }});
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
        if (contador > 0 && bounds) map.fitBounds(bounds, {{padding: [50,50]}});
        document.getElementById('estadoFiltroCultivo').innerHTML = '🌱 ' + contador + ' polígonos (' + seleccionados.join(', ') + ')';
    }}
    
    // ============================================================
    // FILTRO POR SINIESTRO
    // ============================================================
    
    function aplicarFiltroSiniestros() {{
        var seleccionados = [];
        document.querySelectorAll('#siniestroFilters input:checked').forEach(function(el) {{
            seleccionados.push(el.value);
        }});
        var capa = obtenerCapaPoligonos();
        if (!capa) return;
        if (seleccionados.length === 0) {{
            resetearEstilos();
            document.getElementById('estadoFiltroSiniestro').innerHTML = 'Todos los siniestros';
            return;
        }}
        var contador = 0;
        var bounds = null;
        capa.eachLayer(function(layer) {{
            var props = layer.feature.properties;
            var causa = (props.CAUSA_STRO || props.causa_stro || '').toUpperCase();
            if (seleccionados.includes(causa)) {{
                layer.setStyle({{ opacity: 1, fillOpacity: 0.8, weight: 2, color: '#F44336' }});
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
        if (contador > 0 && bounds) map.fitBounds(bounds, {{padding: [50,50]}});
        document.getElementById('estadoFiltroSiniestro').innerHTML = '⚠️ ' + contador + ' polígonos (' + seleccionados.join(', ') + ')';
    }}
    
    // ============================================================
    // RESETEAR TODOS LOS FILTROS
    // ============================================================
    
    function resetearFiltros() {{
        document.getElementById('clienteInput').value = '';
        
        document.querySelectorAll('#cultivoFilters input').forEach(function(el) {{
            el.checked = true;
            el.closest('label').classList.add('active');
        }});
        document.querySelectorAll('#siniestroFilters input').forEach(function(el) {{
            el.checked = true;
            el.closest('label').classList.add('active');
        }});
        
        resetearEstilos();
        
        document.getElementById('estadoFiltroCliente').innerHTML = 'Mostrando todos los polígonos';
        document.getElementById('estadoFiltroCultivo').innerHTML = 'Todos los cultivos';
        document.getElementById('estadoFiltroSiniestro').innerHTML = 'Todos los siniestros';
        
        var capa = obtenerCapaPoligonos();
        if (capa) {{
            var bounds = capa.getBounds();
            if (bounds && bounds.isValid()) map.fitBounds(bounds, {{padding: [50,50]}});
        }}
    }}
    
    // ============================================================
    // ACTIVAR CHECKBOXES
    // ============================================================
    
    document.querySelectorAll('#cultivoFilters input').forEach(function(el) {{
        el.addEventListener('change', function() {{
            var label = this.closest('label');
            if (this.checked) label.classList.add('active');
            else label.classList.remove('active');
        }});
    }});
    
    document.querySelectorAll('#siniestroFilters input').forEach(function(el) {{
        el.addEventListener('change', function() {{
            var label = this.closest('label');
            if (this.checked) label.classList.add('active');
            else label.classList.remove('active');
        }});
    }});
    
    document.getElementById('clienteInput').addEventListener('keypress', function(e) {{
        if (e.key === 'Enter') filtrarCliente();
    }});
    
    // ============================================================
    // INICIALIZAR
    // ============================================================
    
    setTimeout(function() {{
        capaPoligonos = obtenerCapaPoligonos();
        console.log("✅ Sistema de filtros inicializado");
    }}, 1500);
    
    // ============================================================
    // SUBIR FOTO (funciones originales)
    // ============================================================
    
    let fotoActual = null;
    let gpsActual = null;
    let estaEnLinea = navigator.onLine;
    
    function obtenerUbicacionGPS() {{
        const infoGPS = document.getElementById('infoGPS');
        if (!navigator.geolocation) {{
            infoGPS.innerHTML = '❌ GPS no disponible en este dispositivo';
            gpsActual = null;
            return;
        }}
        infoGPS.innerHTML = '📍 Obteniendo ubicación...';
        navigator.geolocation.getCurrentPosition(
            function(posicion) {{
                const lat = posicion.coords.latitude.toFixed(6);
                const lon = posicion.coords.longitude.toFixed(6);
                const precision = posicion.coords.accuracy.toFixed(0);
                gpsActual = {{ lat: parseFloat(lat), lon: parseFloat(lon), precision: precision }};
                infoGPS.innerHTML = `📍 ${{lat}}, ${{lon}} (precisión: ${{precision}}m)`;
                infoGPS.style.color = '#4CAF50';
            }},
            function(error) {{
                console.error('Error GPS:', error);
                gpsActual = null;
                infoGPS.innerHTML = '⚠️ No se pudo obtener ubicación. Se usará ubicación aproximada.';
                infoGPS.style.color = '#FF9800';
            }},
            {{ enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }}
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
        const archivo = e.target.files[0];
        if (!archivo) return;
        const reader = new FileReader();
        reader.onload = function(event) {{
            fotoActual = event.target.result;
            document.getElementById('previewFoto').innerHTML = `<img src="${{fotoActual}}" style="width:100%;height:100%;object-fit:cover;">`;
            document.getElementById('previewFoto').querySelector('span')?.remove();
            if (!gpsActual) obtenerUbicacionGPS();
        }};
        reader.readAsDataURL(archivo);
    }});
    
    async function subirFoto() {{
        if (!fotoActual) {{
            alert('Por favor, selecciona una foto primero');
            return;
        }}
        document.getElementById('panelSubirFoto').querySelector('h3').textContent = '⏳ Subiendo...';
        const btnSubir = document.getElementById('btnSubirFoto');
        btnSubir.disabled = true;
        btnSubir.textContent = '⏳ Subiendo...';
        const timestamp = Date.now();
        const nombreArchivo = `foto_${{gpsActual ? gpsActual.lat + '_' + gpsActual.lon + '_' : ''}}${{timestamp}}.jpg`;
        const base64Data = fotoActual.split(',')[1];
        estaEnLinea = navigator.onLine;
        if (!estaEnLinea) {{
            alert('📸 Foto guardada localmente. Se subirá cuando haya conexión.');
            guardarFotoOffline(base64Data, nombreArchivo);
            cerrarPanelFoto();
            btnSubir.disabled = false;
            btnSubir.textContent = '⬆️ Subir foto';
            document.getElementById('panelSubirFoto').querySelector('h3').textContent = '📸 Subir foto';
            return;
        }}
        try {{
            const fotoData = {{ nombre: nombreArchivo, datos: base64Data, lat: gpsActual ? gpsActual.lat : -31.4201, lon: gpsActual ? gpsActual.lon : -64.1888, timestamp: new Date().toISOString() }};
            const response = await fetch(
                'https://api.github.com/repos/franciscotomatis/APP-CBA-2027/actions/workflows/recibir-foto.yml/dispatches',
                {{ method: 'POST', headers: {{ 'Accept': 'application/vnd.github.v3+json', 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ ref: 'main', inputs: {{ foto_base64: fotoData.datos, nombre_archivo: nombreArchivo, latitud: fotoData.lat.toString(), longitud: fotoData.lon.toString() }} }}) }}
            );
            if (response.ok) {{
                alert('✅ Foto subida exitosamente. Aparecerá en el mapa en unos minutos.');
                cerrarPanelFoto();
                if (window.capaFotosGithub) {{
                    window.capaFotosGithub.clearLayers();
                    if (typeof cargarFotosDesdeGithub === 'function') cargarFotosDesdeGithub();
                }}
            }} else {{
                throw new Error('Error ' + response.status);
            }}
        }} catch (error) {{
            console.error('Error subiendo foto:', error);
            alert('❌ Error al subir la foto. Guardando localmente.');
            guardarFotoOffline(base64Data, nombreArchivo);
            cerrarPanelFoto();
        }}
        btnSubir.disabled = false;
        btnSubir.textContent = '⬆️ Subir foto';
        document.getElementById('panelSubirFoto').querySelector('h3').textContent = '📸 Subir foto';
    }}
    
    function guardarFotoOffline(base64Data, nombreArchivo) {{
        const fotosOffline = JSON.parse(localStorage.getItem('fotosOffline') || '[]');
        const fotoOffline = {{ id: Date.now(), nombre: nombreArchivo, datos: base64Data, gps: gpsActual, timestamp: new Date().toISOString(), estado: 'pendiente' }};
        fotosOffline.push(fotoOffline);
        localStorage.setItem('fotosOffline', JSON.stringify(fotosOffline));
        console.log('📸 Foto guardada offline');
    }}
    
    // Actualizar contador de fotos
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
        </script>
        '''
        agregar_elemento_html_seguro(m, gps_auto_html)
        
    except Exception as e:
        print(f"⚠️  Error GPS: {e}")

    # ========== TÍTULO (mantenido) ==========
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

    # ========== PANEL DE COMPARACIÓN POR ZONA (ORIGINAL) ==========
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
                           style="width:100%;padding:12px 14px;border:2px solid rgba(212,212,212,0.8);border-radius:10px;font-size:14px;background:white;color:#2C2C2C;box-sizing:border-box;">
                </div>
                <div style="margin-bottom: 20px;">
                    <label style="display: block; margin-bottom: 6px; font-weight: 600; color: #2C5530; font-size: 12px;">🔒 Contraseña</label>
                    <input type="password" id="loginContrasena" placeholder="Ingrese su contraseña"
                           style="width:100%;padding:12px 14px;border:2px solid rgba(212,212,212,0.8);border-radius:10px;font-size:14px;background:white;color:#2C2C2C;box-sizing:border-box;">
                </div>
                <button onclick="verificarAcceso()"
                        style="width:100%;background:linear-gradient(135deg,#2C5530,#8A9A5B);color:white;border:none;padding:14px;border-radius:10px;font-size:15px;font-weight:700;cursor:pointer;transition:all 0.3s;display:flex;align-items:center;justify-content:center;gap:8px;">
                    <span>🔓</span> <span>INGRESAR</span>
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
        if (e.key === "Enter") document.getElementById("loginContrasena").focus();
    }});

    document.getElementById("loginContrasena").addEventListener("keypress", function(e) {{
        if (e.key === "Enter") verificarAcceso();
    }});

    document.addEventListener("DOMContentLoaded", function() {{
        map.getContainer().style.pointerEvents = "none";
        setTimeout(() => document.getElementById("loginUsuario").focus(), 500);
    }});
    </script>
    '''
    agregar_elemento_html_seguro(m, login_html)

    # ========== AJUSTAR VISTA ==========
    if not gdf.empty:
        m.fit_bounds(bounds)

    # ========== GUARDAR ==========
    m.save(output_file)
    print(f"✅ Aplicación PRO guardada como: {output_file}")
    
    return output_file

def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python generar_app_pro.py <ruta_al_geojson> [nombre_salida]")
        sys.exit(1)
    
    ruta_geojson = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "index_pro.html"
    
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
        print(f"\n🌐 Para usar: Abre {output_file} en cualquier navegador")
        print(f"📋 Funcionalidades PRO:")
        print(f"   ✅ Login seguro EXACTO")
        print(f"   ✅ Panel lateral con estadísticas")
        print(f"   ✅ Filtro de clientes (con zoom)")
        print(f"   ✅ Filtro por cultivo (con zoom)")
        print(f"   ✅ Filtro por siniestro (con zoom)")
        print(f"   ✅ Modo oscuro/claro")
        print(f"   ✅ Capa de fotos desde GitHub")
        print(f"   ✅ Capa de siniestros (con filtro)")
        print(f"   ✅ Selector de capas (LayerControl)")
        print(f"   ✅ Sistema de leyendas WMS")
        print(f"   ✅ GPS auto-activado")
        print(f"   ✅ Interfaz renovada y responsiva")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
