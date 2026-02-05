# 📸 Sistema de Fotos desde el Campo

## 📁 Estructura
- `/fotos_subidas/` → Fotos nuevas subidas (se procesan automáticamente)
- `/fotos_imagenes/full/` → Fotos procesadas (grandes)
- `/fotos_imagenes/thumb/` → Miniaturas
- `/fotos_metadata/fotos_procesadas.json` → Lista de todas las fotos

## 🔧 Proceso Automático
1. Se sube una foto a `/fotos_subidas/`
2. GitHub Actions detecta la foto nueva
3. Procesa la foto (crea miniatura)
4. Agrega la foto al `fotos_procesadas.json`
5. La foto aparece en el mapa

## 🗑️ Para eliminar una foto
1. Borrar la foto de `/fotos_imagenes/full/`
2. Borrar la miniatura de `/fotos_imagenes/thumb/`
3. Eliminar la entrada del JSON en `fotos_metadata/fotos_procesadas.json`
4. Hacer commit

## ⚠️ Notas
- Las fotos se procesan cada 5 minutos automáticamente
- El sistema funciona con o sin internet
- Las fotos offline se guardan localmente y se suben cuando hay conexión
