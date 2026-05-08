import requests
from concurrent.futures import ThreadPoolExecutor

# Configuración
ARCHIVO_FUENTES = "fuentes.txt" # Un link por línea
SALIDA_M3U = "lista_maestra.m3u"
TIMEOUT = 5 # Segundos para esperar respuesta
MAX_WORKERS = 10 # Cuántas listas revisar en paralelo

def verificar_y_descargar(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        # Usamos stream=True para no descargar gigas de datos, solo probar conexión
        with requests.get(url, headers=headers, timeout=TIMEOUT, stream=True) as r:
            if r.status_code == 200:
                print(f"[VIVA] {url[:50]}...")
                return r.text # Retorna el contenido de la lista
    except Exception:
        pass
    print(f"[CAÍDA] {url[:50]}...")
    return None

def generar_lista():
    with open(ARCHIVO_FUENTES, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"Iniciando validación de {len(urls)} fuentes...\n")
    
    # Ejecución en paralelo
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        resultados = list(executor.map(verificar_y_descargar, urls))

    # Filtrar solo las que devolvieron contenido y limpiar duplicados
    contenido_final = ["#EXTM3U\n"]
    for contenido in resultados:
        if contenido:
            # Quitamos el encabezado #EXTM3U de las listas hijas para no repetir
            lineas = contenido.splitlines()
            for linea in lineas:
                if not linea.startswith("#EXTM3U") and linea.strip():
                    contenido_final.append(linea + "\n")

    with open(SALIDA_M3U, "w", encoding="utf-8") as f:
        f.writelines(contenido_final)
    
    print(f"\nProceso terminado. Lista guardada en: {SALIDA_M3U}")

if __name__ == "__main__":
    generar_lista()