# descargador_automatico.py - VERSIÓN PARA GITHUB ACTIONS
import os
import sys
import json
import requests
import pandas as pd
import geopandas as gpd
from datetime import datetime
from bs4 import BeautifulSoup
import re

print("🚀 SCRIPT AUTOMÁTICO PARA GITHUB ACTIONS")
print("=" * 70)

# ============================================
# CONFIGURACIÓN DESDE SECRETS
# ============================================
BASE_URL = "https://multiriesgo-cba.com"
USERNAME = os.environ.get('MULTIRIESGO_USER', '')
PASSWORD = os.environ.get('MULTIRIESGO_PASS', '')

if not USERNAME or not PASSWORD:
    print("❌ ERROR: No se configuraron las credenciales en Secrets")
    print("   Configura MULTIRIESGO_USER y MULTIRIESGO_PASS en GitHub Secrets")
    sys.exit(1)

print(f"✅ Usuario configurado: {USERNAME}")
print(f"🔗 URL: {BASE_URL}")

# ============================================
# 1. FUNCIÓN DE LOGIN
# ============================================
def hacer_login():
    """Inicia sesión y devuelve sesión activa"""
    print("🔐 Iniciando sesión...")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    })
    
    try:
        # Obtener login y CSRF
        login_page = session.get(f"{BASE_URL}/user/login/")
        soup = BeautifulSoup(login_page.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'}).get('value', '')
        
        if not csrf_token:
            print("❌ No se pudo obtener token CSRF")
            return None
        
        # Login
        login_data = {
            'username': USERNAME,
            'password': PASSWORD,
            'csrfmiddlewaretoken': csrf_token,
        }
        
        login_response = session.post(
            f"{BASE_URL}/user/login/",
            data=login_data,
            headers={'Referer': f"{BASE_URL}/user/login/"}
        )
        
        if login_response.status_code == 200 and "dashboard" in login_response.url:
            print("✅ Login exitoso")
            return session
        else:
            print(f"❌ Login falló - Status: {login_response.status_code}")
            print(f"   URL final: {login_response.url}")
            return None
            
    except Exception as e:
        print(f"❌ Error en login: {e}")
        return None

# ============================================
# 2. DESCARGAR GEOJSON DEL DASHBOARD
# ============================================
def descargar_geojson(session):
    """Descarga GeoJSON desde dashboard"""
    print("\n🗺️ Descargando GeoJSON...")
    
    try:
        # Obtener dashboard
        dashboard = session.get(f"{BASE_URL}/user/staff/dashboard/")
        soup = BeautifulSoup(dashboard.text, 'html.parser')
        
        # Buscar formulario
        form = soup.find('form', {'id': 'staff-dashboard-filter-form'})
        if not form:
            print("❌ No se encontró formulario del dashboard")
            return None
        
        # Extraer datos del formulario
        form_data = {}
        for input_tag in form.find_all('input'):
            name = input_tag.get('name')
            value = input_tag.get('value', '')
            if name and name not in ['', 'submit']:
                form_data[name] = value
        
        # Descargar GeoJSON
        geojson_url = f"{BASE_URL}/user/staff/dashboard/export/geojson/"
        response = session.get(geojson_url, params=form_data)
        
        if response.status_code == 200:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"poligonos_{timestamp}.geojson"
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            # Verificar
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✅ GeoJSON descargado: {filename}")
            print(f"📊 Polígonos: {len(data.get('features', []))}")
            
            return filename
        else:
            print(f"❌ Error descargando GeoJSON: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error descargando GeoJSON: {e}")
        return None

# ============================================
# 3. DESCARGAR CSV DE SINIESTROS
# ============================================
def descargar_csv(session):
    """Descarga CSV desde página de siniestros"""
    print("\n📊 Descargando CSV de siniestros...")
    
    try:
        # Navegar a siniestros
        siniestros_url = f"{BASE_URL}/geo/sinister/list/"
        siniestros_page = session.get(siniestros_url)
        
        # Buscar enlace de descarga CSV
        soup = BeautifulSoup(siniestros_page.text, 'html.parser')
        
        # Buscar enlace con /geo/sinister/export-csv/
        csv_link = None
        for link in soup.find_all('a', href=True):
            if '/geo/sinister/export-csv/' in link['href']:
                csv_link = link['href']
                break
        
        if not csv_link:
            print("❌ No se encontró enlace CSV de siniestros")
            return None
        
        # Asegurar URL completa
        if csv_link.startswith('/'):
            csv_url = f"{BASE_URL}{csv_link}"
        else:
            csv_url = csv_link
        
        # Descargar CSV
        print(f"🔗 Descargando desde: {csv_url}")
        response = session.get(csv_url)
        
        if response.status_code == 200:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"siniestros_{timestamp}.csv"
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ CSV descargado: {filename}")
            print(f"📏 Tamaño: {len(response.content):,} bytes")
            
            return filename
        else:
            print(f"❌ Error descargando CSV: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error descargando CSV: {e}")
        return None

# ============================================
# 4. UNIFICAR ARCHIVOS
# ============================================
def unificar_archivos(geojson_file, csv_file):
    """Une GeoJSON con datos del CSV"""
    print("\n🔗 Unificando GeoJSON + CSV...")
    
    try:
        # Cargar GeoJSON
        print(f"📖 Cargando {geojson_file}...")
        with open(geojson_file, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
        gdf.crs = "EPSG:4326"
        
        print(f"📊 Polígonos: {len(gdf)}")
        
        # Cargar CSV
        print(f"📖 Cargando {csv_file}...")
        try:
            df_csv = pd.read_csv(csv_file, sep='\t', encoding='utf-8')
        except:
            df_csv = pd.read_csv(csv_file, encoding='utf-8')
        
        print(f"📊 Registros CSV: {len(df_csv)}")
        
        # Buscar columnas en CSV
        csv_id_col = None
        causa_col = None
        fecha_col = None
        danio_col = None
        
        for col in df_csv.columns:
            col_lower = str(col).lower()
            if 'id lote' in col_lower:
                csv_id_col = col
            elif 'causa stro' in col_lower:
                causa_col = col
            elif 'fecha stro' in col_lower:
                fecha_col = col
            elif 'daño estimado' in col_lower:
                danio_col = col
        
        if not csv_id_col or not causa_col:
            print("❌ Columnas necesarias no encontradas en CSV")
            return None
        
        print(f"🎯 Columnas CSV: ID='{csv_id_col}', Causa='{causa_col}'")
        
        # Buscar columna ID en GeoJSON
        geo_id_col = None
        for col in gdf.columns:
            if 'id' in col.lower() and 'lote' in col.lower():
                geo_id_col = col
                break
        
        if not geo_id_col:
            for col in gdf.columns:
                if 'id' in col.lower():
                    geo_id_col = col
                    break
        
        print(f"🎯 Columna GeoJSON ID: '{geo_id_col}'")
        
        # Crear diccionario de siniestros
        siniestros_dict = {}
        for idx, row in df_csv.iterrows():
            csv_id = str(row[csv_id_col]).strip()
            if csv_id and csv_id != 'nan':
                siniestros_dict[csv_id] = {
                    'CAUSA_STRO': str(row[causa_col]).strip() if causa_col and pd.notna(row.get(causa_col)) else None,
                    'FECHA_STRO': str(row[fecha_col]).strip() if fecha_col and pd.notna(row.get(fecha_col)) else None,
                    'DAÑO_ESTIMADO': str(row[danio_col]).strip() if danio_col and pd.notna(row.get(danio_col)) else None
                }
        
        print(f"📋 Siniestros únicos: {len(siniestros_dict)}")
        
        # Agregar datos al GeoJSON
        gdf['CAUSA_STRO'] = None
        gdf['FECHA_STRO'] = None
        gdf['DAÑO_ESTIMADO'] = None
        
        matches = 0
        if geo_id_col:
            for idx, row in gdf.iterrows():
                geo_id = str(row[geo_id_col]).strip() if pd.notna(row[geo_id_col]) else None
                if geo_id and geo_id in siniestros_dict:
                    datos = siniestros_dict[geo_id]
                    gdf.at[idx, 'CAUSA_STRO'] = datos['CAUSA_STRO']
                    gdf.at[idx, 'FECHA_STRO'] = datos['FECHA_STRO']
                    gdf.at[idx, 'DAÑO_ESTIMADO'] = datos['DAÑO_ESTIMADO']
                    matches += 1
        
        print(f"✅ Matches encontrados: {matches}")
        
        # Guardar GeoJSON unificado
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"geojson_unificado_{timestamp}.geojson"
        
        geojson_unificado = {
            'type': 'FeatureCollection',
            'properties': {
                'generado_por': 'Script Automático GitHub Actions',
                'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'poligonos': len(gdf),
                'siniestros': matches,
                'hectareas': float(gdf['HECTAREAS_ASEGURADAS'].sum()) if 'HECTAREAS_ASEGURADAS' in gdf.columns else 0
            },
            'features': json.loads(gdf.to_json())['features']
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(geojson_unificado, f, indent=2)
        
        print(f"✅ GeoJSON unificado: {output_file}")
        print(f"📏 Tamaño: {os.path.getsize(output_file):,} bytes")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error en unificación: {e}")
        import traceback
        traceback.print_exc()
        return None

# ============================================
# 5. FUNCIÓN PRINCIPAL
# ============================================
def main():
    """Función principal que ejecuta todo el proceso"""
    print("\n" + "="*70)
    print("🚀 INICIANDO PROCESO AUTOMÁTICO")
    print("="*70)
    
    # Paso 1: Login
    session = hacer_login()
    if not session:
        print("❌ No se pudo iniciar sesión. Abortando.")
        return None
    
    # Paso 2: Descargar GeoJSON
    geojson_file = descargar_geojson(session)
    if not geojson_file:
        print("❌ No se pudo descargar GeoJSON. Abortando.")
        return None
    
    # Paso 3: Descargar CSV
    csv_file = descargar_csv(session)
    if not csv_file:
        print("❌ No se pudo descargar CSV. Abortando.")
        return None
    
    # Paso 4: Unificar
    unificado_file = unificar_archivos(geojson_file, csv_file)
    
    if unificado_file:
        print("\n" + "="*70)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("="*70)
        
        # Mostrar estadísticas
        with open(unificado_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📊 Polígonos: {len(data.get('features', []))}")
        
        # Contar siniestros
        features = data.get('features', [])
        siniestros = sum(1 for f in features if f.get('properties', {}).get('CAUSA_STRO'))
        print(f"⚠️ Siniestros: {siniestros}")
        
        # Crear también el archivo con nombre fijo para la app
        archivo_fijo = "geojson_unificado_actual.geojson"
        with open(archivo_fijo, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"📁 Archivo fijo creado: {archivo_fijo}")
        
        return archivo_fijo
    else:
        print("❌ Error en la unificación")
        return None

# ============================================
# EJECUTAR
# ============================================
if __name__ == "__main__":
    archivo_final = main()
    
    if archivo_final:
        print(f"\n🎯 Archivo listo para usar: {archivo_final}")
        print("✅ Script ejecutado exitosamente")
        sys.exit(0)
    else:
        print("❌ Script falló")
        sys.exit(1)
