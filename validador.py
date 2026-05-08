import requests
from concurrent.futures import ThreadPoolExecutor
import re

# --- CONFIGURACIÓN ---
ARCHIVO_FUENTES = "fuentes.txt"
SALIDA_M3U = "lista_maestra.m3u"
TIMEOUT = 10 
MAX_WORKERS = 15
OPCIONES_POR_CANAL = 3  # <--- AQUÍ defines cuántas opciones quieres de cada canal

# Mantenemos las palabras clave para evitar que el archivo pese 1GB otra vez
PALABRAS_CLAVE = ["ECUADOR", "COLOMBIA", "ESPAÑA", "DEPORTES", "HBO", "FUTBOL", "CINEMA", "DISNEY", "STAR+"]

def verificar_y_descargar(url):
    headers = {'User-Agent': 'VLC/3.0.18 LibVLC/3.0.18'}
    url = url.strip()
    if not url: return None
    try:
        with requests.get(url, headers=headers, timeout=TIMEOUT, stream=True) as r:
            if r.status_code == 200:
                print(f"✅ VIVA: {url[:50]}...")
                return r.text
    except Exception: pass
    return None

def limpiar_nombre(nombre):
    """Limpia el nombre del canal para agruparlo mejor (quita HD, FHD, etc)"""
    nombre = nombre.upper()
    nombre = re.sub(r'\[.*?\]|\(.*?\)', '', nombre) # Quita lo que esté en corchetes o paréntesis
    nombre = nombre.replace("HD", "").replace("FHD", "").replace("4K", "").replace("SD", "")
    return nombre.strip()

def generar_lista():
    try:
        with open(ARCHIVO_FUENTES, "r") as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError: return

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        resultados = list(executor.map(verificar_y_descargar, urls))

    canales_agrupados = {} # Diccionario para llevar la cuenta: { 'NOMBRE_CANAL': contador }
    contenido_final = ["#EXTM3U\n"]
    total_canales = 0

    for contenido in resultados:
        if not contenido: continue
        
        lineas = contenido.splitlines()
        for i in range(len(lineas)):
            if lineas[i].startswith("#EXTINF"):
                info_line = lineas[i]
                url_line = lineas[i+1] if (i+1) < len(lineas) else ""
                
                # Extraer nombre del canal (lo que va después de la última coma)
                parts = info_line.split(',')
                raw_name = parts[-1] if len(parts) > 1 else "Canal Desconocido"
                nombre_id = limpiar_nombre(raw_name)

                # Filtro de palabras clave
                if any(p.upper() in info_line.upper() for p in PALABRAS_CLAVE):
                    # Lógica de redundancia: ¿Ya tenemos suficientes opciones de este canal?
                    count = canales_agrupados.get(nombre_id, 0)
                    
                    if count < OPCIONES_POR_CANAL:
                        # Modificamos el nombre para que en tu TV veas "Canal (Opción 1)"
                        nuevo_nombre = f"{raw_name} [Opción {count + 1}]"
                        nueva_info = info_line.replace(raw_name, nuevo_nombre)
                        
                        contenido_final.append(nueva_info + "\n")
                        contenido_final.append(url_line + "\n")
                        
                        canales_agrupados[nombre_id] = count + 1
                        total_canales += 1

    with open(SALIDA_M3U, "w", encoding="utf-8") as f:
        f.writelines(contenido_final)
    
    print(f"\n--- PROCESO TERMINADO ---")
    print(f"Canales únicos encontrados: {len(canales_agrupados)}")
    print(f"Total de enlaces guardados (con redundancia): {total_canales}")

if __name__ == "__main__":
    generar_lista()
