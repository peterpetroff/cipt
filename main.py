import requests
from concurrent.futures import ThreadPoolExecutor
import re

# --- CONFIGURACIÓN DE FILTRADO ULTRA ESTRICTO ---
ARCHIVO_FUENTES = "settings.log"
SALIDA_M3U = "styles.m3u"
TIMEOUT = 10 
MAX_WORKERS = 20
OPCIONES_POR_CANAL = 2  # Máximo 2 opciones por canal como solicitaste

# 1. Categorías y marcas deportivas/plataformas específicas
MARCAS_PERMITIDAS = [
    "ESPN", "DIRECTV", "DSPORTS", "ZAPPING", "FOX", "FOX SPORTS", 
    "FUTBOL", "CHAMPIONS", "LIBERTADORES", "LIGA PRO"
]

# 2. Canales infantiles y de entretenimiento general seleccionados
ENTRETENIMIENTO_PERMITIDO = [
    "CARTOON NETWORK", "CARTOON", "DISNEY", "NICKELODEON", # Infantil
    "HBO", "WARNER", "TNT", "UNIVERSAL", "STAR CHANNEL", "AXN", "CINEMAX" # Entretenimiento/Películas en vivo
]

# 3. Filtro geográfico estricto para Ecuador (buscando calidad HD)
PALABRAS_ECUADOR = ["ECUADOR", "EC", "TELEAMAZONAS", "ECUAVISA", "TC TELEVISION", "RTS", "EL CANAL DEL FUTBOL", "ECDF"]

# Bloqueo absoluto de bibliotecas VOD (Series y Películas que no son canales en vivo)
PALABRAS_PROHIBIDAS = [
    "VOD", "PELICULA:", "MOVIE:", "SERIE:", "EPISODIO", "SEASON", "CAPITULO", 
    "TEMPORADA", "ADULTO", "XXX", "ANIME", "NOVELA"
]

def verificar_y_descargar(url):
    headers = {'User-Agent': 'VLC/3.0.18 LibVLC/3.0.18'}
    try:
        with requests.get(url.strip(), headers=headers, timeout=TIMEOUT, stream=True) as r:
            if r.status_code == 200: return r.text
    except: pass
    return None

def limpiar_nombre(nombre):
    nombre = nombre.upper()
    nombre = re.sub(r'\[.*?\]|\(.*?\)', '', nombre)
    return nombre.replace("HD", "").replace("FHD", "").replace("4K", "").strip()

def es_canal_valido(info_line):
    info_upper = info_line.upper()
    
    # Si detecta que es una película/serie de catálogo (VOD), queda descartada inmediatamente
    if any(p in info_upper for p in PALABRAS_PROHIBIDAS):
        return False

    # Validación de Marcas Deportivas / Zapping / FOX
    if any(m in info_upper for m in MARCAS_PERMITIDAS):
        return True

    # Validación de Canales de Entretenimiento específicos (fijados a ~5 marcas de películas/series en vivo + Cartoon)
    if any(e in info_upper for e in ENTRETENIMIENTO_PERMITIDO):
        return True

    # Validación estricta para Ecuador: Debe tener la marca de Ecuador y preferiblemente ser HD
    if any(ec in info_upper for ec in PALABRAS_ECUADOR):
        # Prioriza que contenga la palabra HD para asegurar la calidad que buscas
        if "HD" in info_upper or "FHD" in info_upper:
            return True
        # Si es un canal clave local, dejarlo pasar de todas formas
        if any(local in info_upper for local in ["TELEAMAZONAS", "ECUAVISA", "TC TELEVISION", "ECDF"]):
            return True

    return False

def generar_lista():
    with open(ARCHIVO_FUENTES, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        resultados = list(executor.map(verificar_y_descargar, urls))

    canales_agrupados = {}
    contenido_final = ["#EXTM3U\n"]

    for contenido in resultados:
        if not contenido: continue
        lineas = contenido.splitlines()
        for i in range(len(lineas)):
            if lineas[i].startswith("#EXTINF"):
                info = lineas[i]
                url = lineas[i+1] if (i+1) < len(lineas) else ""
                
                if es_canal_valido(info):
                    parts = info.split(',')
                    raw_name = parts[-1] if len(parts) > 1 else "Canal Innombrado"
                    id_canal = limpiar_nombre(raw_name)
                    
                    count = canales_agrupados.get(id_canal, 0)
                    # Forzamos el máximo de 2 opciones por canal
                    if count < OPCIONES_POR_CANAL:
                        nuevo_nombre = f"{raw_name} [Opción {count + 1}]"
                        contenido_final.append(info.replace(raw_name, nuevo_nombre) + "\n")
                        contenido_final.append(url + "\n")
                        canales_agrupados[id_canal] = count + 1

    with open(SALIDA_M3U, "w", encoding="utf-8") as f:
        f.writelines(contenido_final)

if __name__ == "__main__":
    generar_lista()
