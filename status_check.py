import pandas as pd
import requests

url = 'https://gnepzgnrexurskyggrqo.supabase.co/rest/v1/songs_saas?select=id,artist,title,lyrics'
headers = {
    'apikey': 'sb_secret_E8BQY9JkYMWrE38YkPVMxQ_tyYfQo_f',
    'Authorization': 'Bearer sb_secret_E8BQY9JkYMWrE38YkPVMxQ_tyYfQo_f'
}

all_data = []
offset = 0
while True:
    r = requests.get(url + f'&offset={offset}&limit=1000', headers=headers)
    data = r.json()
    if not data: break
    all_data.extend(data)
    offset += 1000

df = pd.DataFrame(all_data)
total_songs = len(df)
total_artists = df['artist'].nunique()
with_lyrics = df['lyrics'].notna().sum()

print("STATUS REPORT")
print("=============")
print(f"Total Discos (Canciones) en la Nube: {total_songs}")
print(f"Total Artistas Únicos: {total_artists}")
print(f"Total Discos con Letras Descargadas: {with_lyrics}")
