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
        # Buscar canciones en la nube que no tienen letra
        res = supabase.table('songs_saas').select('id, title, artist').is_('lyrics', 'null').execute()
        canciones = res.data
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
        
        print(f"🎵 Buscando: {titulo} - {artista}...")
        
        params = {"track_name": titulo, "artist_name": artista}
        
        try:
            response = requests.get(API_URL, params=params)
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
