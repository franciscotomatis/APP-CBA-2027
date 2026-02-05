#!/usr/bin/env python3
"""
PROCESADOR AUTOMÁTICO DE FOTOS NUEVAS
Se ejecuta automáticamente por GitHub Actions
Procesa fotos subidas a /fotos_subidas/ y las agrega al mapa
"""

import os
import json
from datetime import datetime
import hashlib
from PIL import Image
from pathlib import Path

def crear_carpetas():
    """Crea las carpetas necesarias si no existen"""
    carpetas = [
        "fotos_subidas/procesadas",
        "fotos_imagenes/full", 
        "fotos_imagenes/thumb",
        "fotos_metadata"
    ]
    
    for carpeta in carpetas:
        Path(carpeta).mkdir(parents=True, exist_ok=True)
    
    print("✅ Carpetas verificadas")

def buscar_fotos_nuevas():
    """Busca fotos nuevas en la carpeta de subidas"""
    fotos = list(Path("fotos_subidas").glob("*"))
    
    # Filtrar solo imágenes (no carpetas, no archivos procesados)
    fotos_validas = []
    for foto in fotos:
        if foto.is_file() and foto.suffix.lower() in ['.jpg', '.jpeg', '.png', '.heic']:
            fotos_validas.append(foto)
    
    print(f"📸 Encontradas {len(fotos_validas)} fotos nuevas")
    return fotos_validas

def extraer_ubicacion_del_nombre(nombre_archivo):
    """
    Intenta extraer coordenadas del nombre del archivo
    Formato esperado: foto_LAT_LON_... o LAT_LON.jpg
    """
    nombre = nombre_archivo.stem
    
    # Buscar patrones comunes
    partes = nombre.replace(',', '.').split('_')
    
    for i, parte in enumerate(partes):
        try:
            # Intentar convertir a número
            lat = float(parte)
            # Si la siguiente parte también es número, puede ser lon
            if i + 1 < len(partes):
                try:
                    lon = float(partes[i + 1])
                    print(f"   📍 Coordenadas extraídas del nombre: {lat}, {lon}")
                    return lat, lon
                except:
                    pass
        except:
            continue
    
    # Si no encuentra, usar coordenadas por defecto (Córdoba)
    print("   ⚠️ No se encontraron coordenadas, usando Córdoba por defecto")
    return -31.4201, -64.1888  # Córdoba centro

def procesar_foto(foto_path, datos_json):
    """Procesa una foto individual"""
    print(f"  🔄 Procesando: {foto_path.name}")
    
    # 1. Extraer ubicación
    lat, lon = extraer_ubicacion_del_nombre(foto_path)
    
    # 2. Generar nombre único
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hash_corto = hashlib.md5(f"{timestamp}_{foto_path.name}".encode()).hexdigest()[:6]
    nombre_jpg = f"foto_{timestamp}_{hash_corto}.jpg"
    
    # 3. Crear URLs de GitHub
    url_completa = f"https://raw.githubusercontent.com/franciscotomatis/APP-C-rdoba/main/fotos_imagenes/full/{nombre_jpg}"
    url_miniatura = f"https://raw.githubusercontent.com/franciscotomatis/APP-C-rdoba/main/fotos_imagenes/thumb/{nombre_jpg}"
    
    # 4. Procesar imagen
    try:
        with Image.open(foto_path) as img:
            # Convertir a RGB si es necesario
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Guardar versión completa
            img.save(f"fotos_imagenes/full/{nombre_jpg}", "JPEG", quality=85, optimize=True)
            
            # Crear miniatura
            thumb = img.copy()
            thumb.thumbnail((200, 200))
            thumb.save(f"fotos_imagenes/thumb/{nombre_jpg}", "JPEG", quality=70)
            
            print(f"    ✅ Imagen guardada: {nombre_jpg}")
            
    except Exception as e:
        print(f"    ❌ Error procesando imagen: {e}")
        return None
    
    # 5. Crear entrada para JSON
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]  # GeoJSON usa [longitud, latitud]
        },
        "properties": {
            "IMAGEN_URL": url_completa,
            "MINIATURA_URL": url_miniatura,
            "NOMBRE_FOTO": f"Foto desde campo - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "NOMBRE_ORIGINAL": foto_path.name,
            "METODO": "Subida automática",
            "FECHA": datetime.now().isoformat(),
            "GPS_LAT": lat,
            "GPS_LON": lon,
            "TAMANIO": os.path.getsize(f"fotos_imagenes/full/{nombre_jpg}"),
            "ID_UNICO": f"{timestamp}_{hash_corto}"
        }
    }
    
    return feature

def mover_a_procesadas(foto_path):
    """Mueve la foto procesada a la carpeta de procesadas"""
    destino = Path("fotos_subidas/procesadas") / foto_path.name
    
    # Si ya existe un archivo con ese nombre, agregar timestamp
    if destino.exists():
        timestamp = datetime.now().strftime("%H%M%S")
        nuevo_nombre = f"{foto_path.stem}_{timestamp}{foto_path.suffix}"
        destino = Path("fotos_subidas/procesadas") / nuevo_nombre
    
    foto_path.rename(destino)
    print(f"    📁 Movido a: procesadas/{destino.name}")

def main():
    """Función principal"""
    print("=" * 60)
    print("🔄 INICIANDO PROCESAMIENTO DE FOTOS NUEVAS")
    print("=" * 60)
    
    # 1. Preparar carpetas
    crear_carpetas()
    
    # 2. Buscar fotos nuevas
    fotos_nuevas = buscar_fotos_nuevas()
    
    if not fotos_nuevas:
        print("📭 No hay fotos nuevas para procesar")
        return
    
    # 3. Cargar JSON existente o crear uno nuevo
    json_path = "fotos_metadata/fotos_procesadas.json"
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            datos = json.load(f)
    else:
        datos = {
            "type": "FeatureCollection",
            "metadata": {
                "ultima_actualizacion": datetime.now().isoformat(),
                "total_fotos": 0,
                "version": "1.0"
            },
            "features": []
        }
    
    # 4. Procesar cada foto
    fotos_procesadas = 0
    for foto_path in fotos_nuevas:
        try:
            feature = procesar_foto(foto_path, datos)
            if feature:
                datos["features"].append(feature)
                mover_a_procesadas(foto_path)
                fotos_procesadas += 1
        except Exception as e:
            print(f"❌ Error procesando {foto_path.name}: {e}")
    
    # 5. Actualizar metadatos
    datos["metadata"]["ultima_actualizacion"] = datetime.now().isoformat()
    datos["metadata"]["total_fotos"] = len(datos["features"])
    
    # 6. Guardar JSON actualizado
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    
    print("=" * 60)
    print(f"✅ PROCESAMIENTO COMPLETADO")
    print(f"   📸 Fotos procesadas: {fotos_procesadas}")
    print(f"   📊 Total fotos en sistema: {len(datos['features'])}")
    print(f"   💾 JSON guardado en: {json_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
