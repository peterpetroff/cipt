import requests
from concurrent.futures import ThreadPoolExecutor

# Configuración
ARCHIVO_FUENTES = "fuentes.txt"
SALIDA_M3U = "lista_maestra.m3u"
TIMEOUT = 10 
MAX_WORKERS = 15 # Procesamos 15 listas a la vez para ir rápido

def verificar_y_descargar(url):
    # Usamos un User-Agent de un reproductor común para evitar bloqueos
    headers = {
        'User-Agent': 'VLC/3.0.18 LibVLC/3.0.18'
    }
    url = url.strip()
    if not url:
        return None
        
    try:
        # Probamos la conexión
        with requests.get(url, headers=headers, timeout=TIMEOUT, stream=True) as r:
            if r.status_code == 200:
                print(f"✅ VIVA: {url[:60]}...")
                # Retornamos el texto completo de la lista
                return r.text
            else:
                print(f"❌ ERROR {r.status_code}: {url[:60]}...")
    except Exception as e:
        print(f"⚠️ FALLO: {url[:60]}... Motivo: {e}")
    return None

def generar_lista():
    try:
        with open(ARCHIVO_FUENTES, "r") as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {ARCHIVO_FUENTES}")
        return

    print(f"Iniciando validación de {len(urls)} fuentes...\n")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        resultados = list(executor.map(verificar_y_descargar, urls))

    # Construcción de la lista maestra
    contenido_final = ["#EXTM3U\n"]
    fuentes_activas = 0

    for contenido in resultados:
        if contenido:
            fuentes_activas += 1
            lineas = contenido.splitlines()
            for linea in lineas:
                # Evitamos repetir el encabezado en cada unión
                if not linea.startswith("#EXTM3U") and linea.strip():
                    contenido_final.append(linea + "\n")

    with open(SALIDA_M3U, "w", encoding="utf-8") as f:
        f.writelines(contenido_final)
    
    print(f"\n--- PROCESO TERMINADO ---")
    print(f"Listas procesadas con éxito: {fuentes_activas}")
    print(f"Archivo generado: {SALIDA_M3U}")

if __name__ == "__main__":
    generar_lista()
