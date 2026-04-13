import requests
import json
import time

# Extract missing artists from auditoria file
missing_artists = []
with open('auditoria_artistas.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    in_missing_section = False
    for line in lines:
        if "### Artistas NO ENCONTRADOS" in line:
            in_missing_section = True
            continue
        if "### Artistas con FALTANTE" in line:
            break
        if in_missing_section and line.startswith('- ❌ '):
            missing_artists.append(line.replace('- ❌ ', '').strip())

print(f"Detectados {len(missing_artists)} artistas fantasma. Iniciando importacion masiva de iTunes API...")

url_supabase = 'https://gnepzgnrexurskyggrqo.supabase.co/rest/v1/songs_saas'
headers_supabase = {
    'apikey': 'sb_secret_E8BQY9JkYMWrE38YkPVMxQ_tyYfQo_f',
    'Authorization': 'Bearer sb_secret_E8BQY9JkYMWrE38YkPVMxQ_tyYfQo_f',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

nuevas_canciones = 0
current_id = 4000
for artist in missing_artists:
    print(f"📥 Buscando Top 15 de: {artist}")
    itunes_url = f"https://itunes.apple.com/search?term={requests.utils.quote(artist)}&entity=song&limit=15&country=CO"
    
    try:
        r = requests.get(itunes_url)
        if r.status_code == 200:
            data = r.json()
            results = data.get('results', [])
            
            insert_batch = []
            for track in results:
                insert_batch.append({
                    "id": current_id,
                    "bar_id": "bar_1",
                    "title": track.get('trackName', 'Desconocido'),
                    "artist": artist,  # Force original name for UI consistency
                    "album": track.get('collectionName', 'Sencillo'),
                    "genre": track.get('primaryGenreName', 'Balada'),
                    "lyrics": None,
                    "is_banned": 0
                })
                current_id += 1
            
            if insert_batch:
                # Insert directly into Supabase
                resp = requests.post(url_supabase, headers=headers_supabase, json=insert_batch)
                if resp.status_code in [201, 204]:
                    nuevas_canciones += len(insert_batch)
                    print(f"   ✅ +{len(insert_batch)} canciones agregadas con éxito.")
                else:
                    print(f"   ❌ Error Supabase: {resp.status_code} - {resp.text}")
            else:
                print(f"   ⚠️ No se encontraron canciones para este artista en iTunes.")
        else:
             print(f"   ❌ Error iTunes API: {r.status_code}")
             
    except Exception as e:
        print(f"   🚨 Error en el script: {e}")
        
    time.sleep(1) # Respetar API iTunes

print(f"\n======================================")
print(f"🎉 ORO PURO RECUPERADO")
print(f"🎵 Se inyectaron {nuevas_canciones} nuevas canciones a Supabase.")
print(f"======================================")
