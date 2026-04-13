import requests
import sqlite3
import time
from db import insert_songs_bulk, get_songs, init_db

# Lista estricta de 50 artistas consolidados solicitada
artistas = [
    "Luis Miguel", "Jose Jose", "Camilo Sesto", "Juan Gabriel", "Rocio Durcal",
    "Ana Gabriel", "Julio Iglesias", "Roberto Carlos", "Nino Bravo", "Raphael",
    "Jose Luis Perales", "Myriam Hernandez", "Yuri", "Amanda Miguel", "Marisela",
    "Lupita D Alessio", "Daniela Romo", "Paloma San Basilio", "Laura Pausini", "Jeanette",
    "Tormenta", "Sandro de America", "Leo Dan", "Leonardo Favio", "Diego Verdaguer",
    "Palito Ortega", "Dyango", "Nicola Di Bari", "Piero", "Pimpinela",
    "Los Panchos", "Los Angeles Negros", "Los Terricolas", "Los Iracundos", "Los Pasteles Verdes",
    "Los Temerarios", "Vicente Fernandez", "Javier Solis", "Julio Jaramillo", "Joan Sebastian",
    "Antonio Aguilar", "Marco Antonio Solis", "Franco De Vita", "Ricardo Montaner", "Chayanne",
    "Emmanuel", "Mijares", "Alejandro Fernandez", "Cristian Castro", "Ricardo Arjona"
]

# Filtro estricto para no meter basura a las carpetas visuales
PALABRAS_PROHIBIDAS = ["live", "vivo", "karaoke", "instrumental", "remix", "version", "versión", "tributo", "dj"]

def es_cancion_limpia(titulo, album):
    texto = f"{titulo} {album}".lower()
    for palabra in PALABRAS_PROHIBIDAS:
        if palabra in texto:
            return False
    return True

def poblar_automaticamente():
    print("Iniciando extracción y filtrado de alto nivel (Solo éxitos puros)...")
    init_db()
    
    try:
        db_songs = get_songs()
        t_existentes_por_artista = {}
        if not db_songs.empty:
            for _, row in db_songs.iterrows():
                art = row['artist'].lower()
                if art not in t_existentes_por_artista:
                    t_existentes_por_artista[art] = set()
                t_existentes_por_artista[art].add(row['title'].lower())
    except Exception:
        t_existentes_por_artista = {}

    total_importadas = 0

    for artista in artistas:
        print(f"Indexando a: {artista}...")
        url = f"https://itunes.apple.com/search?term={artista.replace(' ', '+')}&entity=song&limit=100"
        
        try:
            respuesta = requests.get(url)
            if respuesta.status_code == 200:
                resultados = respuesta.json().get("results", [])
                nuevas_canciones = []
                artista_existentes = t_existentes_por_artista.get(artista.lower(), set())
                
                for item in resultados:
                    # Siempre usaremos nuestro nombre oficial del artista para agrupar perfecto las carpetas
                    titulo = item.get("trackName", "Desconocido")
                    album = item.get("collectionName", "Grandes Exitos")
                    genero = item.get("primaryGenreName", "Pop")
                    
                    titulo_clean = titulo.lower().strip()
                    
                    if es_cancion_limpia(titulo, album) and titulo_clean not in artista_existentes:
                        # Forzamos que el 'artista' sea exactamente el de nuestra lista
                        nuevas_canciones.append((titulo, artista, album, genero))
                        artista_existentes.add(titulo_clean)
                
                if nuevas_canciones:
                    insert_songs_bulk(nuevas_canciones)
                    t_existentes_por_artista[artista.lower()] = artista_existentes
                    total_importadas += len(nuevas_canciones)
                    print(f"  -> Se guardaron {len(nuevas_canciones)} canciones de {artista}.")
                else:
                    print(f"  -> Catálogo completo para {artista}.")
            
        except Exception as e:
            print(f"  -> Error con {artista}: {e}")
            
        time.sleep(1)

    print(f"\\n¡Proceso Finalizado! Se llenaron las carpetas con {total_importadas} canciones impecables y agrupadas.")

if __name__ == "__main__":
    poblar_automaticamente()
