import requests
import time
from db import supabase

API_URL = "https://lrclib.net/api/search"

def fetch_and_save_lyrics():
    print("="*50)
    print("🤖 ROBOT INTELIGENTE DE LETRAS (CLOUD EDITION)")
    print("="*50)
    
    print("Conectando a la Bóveda en la Nube (Supabase)...")
    try:
        # Paginar la búsqueda para evadir el límite de 1000 de Supabase
        canciones = []
        offset = 0
        while True:
            res = supabase.table('songs_saas').select('id, title, artist').is_('lyrics', 'null').range(offset, offset + 999).execute()
            if not res.data:
                break
            canciones.extend(res.data)
            if len(res.data) < 1000:
                break
            offset += 1000
    except Exception as e:
        print(f"Error accediendo a Supabase: {str(e)}")
        return
        
    if not canciones:
        print("¡El 100% de tu catálogo en la nube ya tiene letra!")
        return

    print(f"\nSe detectaron {len(canciones)} pistas sin cantar.")
    print("Iniciando cacería de letras a través de la API...\n")
    exitos = 0
    
    for song in canciones:
        song_id = song['id']
        titulo = song['title']
        artista = song['artist']
        
        import re
        
        # Limpieza intensiva de título para evadir el rechazo de la API
        # Ej: "La Culpa (Remastered 2004) - En vivo" -> "La Culpa"
        clean_title = re.sub(r'\s*[\(\[].*?[\)\]]', '', titulo)
        clean_title = re.split(r'\s-\s', clean_title)[0]
        clean_title = clean_title.strip()
        
        print(f"🎵 Buscando: {titulo} -> (Como: '{clean_title}') - {artista}...")
        
        # A veces el artista viene dual "Yuri & Leo", probar usar query libre si falla exacto
        params = {"track_name": clean_title, "artist_name": artista}
        
        try:
            response = requests.get(API_URL, params=params)
            
            # Si falla la búsqueda estricta, intentamos una búsqueda abierta (texto completo)
            if response.status_code == 200 and not response.json():
                params_abiertos = {"q": f"{clean_title} {artista}"}
                response = requests.get(API_URL, params=params_abiertos)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    letra = data[0].get("plainLyrics")
                    if letra:
                        # Inyectar directo a Supabase
                        supabase.table('songs_saas').update({'lyrics': letra}).eq('id', song_id).execute()
                        exitos += 1
                        print("  -> ☁️ EXITO! Letra subida a Supabase.")
                    else:
                        print("  -> ⚠️ Letra vacía en formato texto plano")
                else:
                    print("  -> ❌ No existe en el catálogo mundial")
            else:
                print(f"  -> ⚠️ Error de Conexión HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  -> ❌ Error de red: {e}")
            
        time.sleep(1) # Respeto extremo por las APIs públicas para no ser baneado

    print(f"\n=============================================")
    print(f"🎉 INYECCIÓN COMPLETADA.")
    print(f"🎤 {exitos} letras descargadas y sincronizadas!")
    print(f"=============================================")

if __name__ == "__main__":
    fetch_and_save_lyrics()
