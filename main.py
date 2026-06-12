import requests
from concurrent.futures import ThreadPoolExecutor
import re

# --- CONFIGURACIÓN DE FILTRADO ULTRA ESTRICTO ---
ARCHIVO_FUENTES = "settings.log"
SALIDA_M3U = "styles.m3u"
TIMEOUT = 10 
MAX_WORKERS = 20
OPCIONES_POR_CANAL = 2  # Máximo 2 opciones por canal

# Categorías y marcas permitidas (Canales en vivo únicamente)
MARCAS_PERMITIDAS = [
    "ESPN", "DIRECTV", "DSPORTS", "ZAPPING", "FOX", "FOX SPORTS", 
    "FUTBOL", "CHAMPIONS", "LIBERTADORES", "LIGA PRO", "MUNDIAL", "WIN", "WIN SPORTS", "PARAMOUNT", "FIFA 2026"
]

ENTRETENIMIENTO_PERMITIDO = [
    "CARTOON NETWORK", "CARTOON", "DISNEY", "NICKELODEON", 
    "HBO", "WARNER", "TNT", "UNIVERSAL", "STAR CHANNEL", "AXN", "CINEMAX"
]

PALABRAS_ECUADOR = ["ECUADOR", "EC", "TELEAMAZONAS", "ECUAVISA", "TC TELEVISION", "RTS", "EL CANAL DEL FUTBOL", "ECDF"]

# Se agrega "24/7" y "24-7" para eliminar esos canales repetitivos de series/películas en bucle
PALABRAS_PROHIBIDAS = [
    "VOD", "PELICULA:", "MOVIE:", "SERIE:", "EPISODIO", "SEASON", "CAPITULO", 
    "TEMPORADA", "ADULTO", "XXX", "ANIME", "NOVELA", "24/7", "24-7", "LOOP"
]

def verificar_y_descargar(url):
    headers = {'User-Agent': 'VLC/3.0.18 LibVLC/3.0.18'}
    try:
        if not url.startswith("http"): return None
        with requests.get(url.strip(), headers=headers, timeout=TIMEOUT, stream=True) as r:
            if r.status_code == 200: return r.text
    except: pass
    return None

def limpiar_nombre(nombre):
    """Limpia y unifica los nombres para agruparlos como opciones"""
    nombre = nombre.upper()
    # Eliminar todo lo que esté entre corchetes o paréntesis
    nombre = re.sub(r'\[.*?\]|\(.*?\)', '', nombre)
    
    # Limpieza de conectores y basura técnica de las listas
    for basura in ["HD", "FHD", "4K", "SD", "1080P", "720P", "LATINO", "ECUADOR", "EC:", "EC ", "PREMIUM", "VIP", "CH"]:
        nombre = nombre.replace(basura, "")
    
    nombre = re.sub(r'\s+', ' ', nombre).strip() # Limpia espacios dobles
    
    # --- UNIFICACIÓN CRÍTICA (Empaqueta los canales sueltos aquí) ---
    if "ECUAVISA" in nombre: return "ECUAVISA"
    if "TELEAMAZONAS" in nombre: return "TELEAMAZONAS"
    if "TC" in nombre and "TELE" in nombre: return "TC TELEVISION"
    if "RTS" in nombre: return "RTS"
    if "CANAL DEL FUTBOL" in nombre or "ECDF" in nombre: return "EL CANAL DEL FÚTBOL"
    if "ESPN 1" in nombre or nombre == "ESPN": return "ESPN"
    if "ESPN 2" in nombre: return "ESPN 2"
    if "ESPN 3" in nombre: return "ESPN 3"
    if "FOX SPORTS" in nombre: return "FOX SPORTS"
    if "CARTOON" in nombre: return "CARTOON NETWORK"
    
    return nombre

def es_canal_valido(info_line):
    info_upper = info_line.upper()
    
    if any(p in info_upper for p in PALABRAS_PROHIBIDAS):
        return False
    if any(m in info_upper for m in MARCAS_PERMITIDAS):
        return True
    if any(e in info_upper for e in ENTRETENIMIENTO_PERMITIDO):
        return True
    if any(ec in info_upper for ec in PALABRAS_ECUADOR):
        return True
    return False

def generar_lista():
    try:
        with open(ARCHIVO_FUENTES, "r", encoding="utf-8", errors="ignore") as f:
            urls = [line.strip() for line in f if line.strip() and line.strip().startswith("http")]
    except:
        return

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        resultados = list(executor.map(verificar_y_descargar, urls))

    canales_agrupados = {}
    contenido_final = ["#EXTM3U\n"]

    for contenido in resultados:
        if not contenido: continue
        try:
            lineas = contenido.splitlines()
            for i in range(len(lineas)):
                if lineas[i].startswith("#EXTINF"):
                    info = lineas[i]
                    url = lineas[i+1] if (i+1) < len(lineas) else ""
                    
                    if es_canal_valido(info) and url.startswith("http"):
                        parts = info.split(',')
                        raw_name = parts[-1] if len(parts) > 1 else "Canal"
                        id_canal = limpiar_nombre(raw_name)
                        
                        count = canales_agrupados.get(id_canal, 0)
                        if count < OPCIONES_POR_CANAL:
                            # Reconstruimos el nombre limpio con su número de opción
                            nuevo_nombre = f"{id_canal} [Opción {count + 1}]"
                            
                            # Reemplazamos el nombre viejo por el unificado en la línea #EXTINF
                            info_limpia = info.replace(raw_name, nuevo_nombre)
                            
                            contenido_final.append(info_limpia + "\n")
                            contenido_final.append(url + "\n")
                            canales_agrupados[id_canal] = count + 1
        except:
            continue

    with open(SALIDA_M3U, "w", encoding="utf-8") as f:
        f.writelines(contenido_final)

if __name__ == "__main__":
    generar_lista()
