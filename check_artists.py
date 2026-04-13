import requests
import pandas as pd

url = 'https://gnepzgnrexurskyggrqo.supabase.co/rest/v1/songs_saas?select=artist,lyrics'
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
# Clean artist names for matching
df['clean_artist'] = df['artist'].str.lower().str.strip()

desired_artists = [
    "Leo Dan", "Palito Ortega", "Sandro de América", "Leonardo Favio", "Raphael",
    "Angélica María", "Enrique Guzmán", "Alberto Vázquez", "César Costa", "Los Iracundos",
    "Los Galos", "Los Ángeles Negros", "Los Terrícolas", "El Greco", "Estela Nuñez",
    "Libertad Lamarque", "Roberto Ledesma", "Alci Acosta", "Oscar Agudelo", "Julio Jaramillo",
    "Camilo Sesto", "José José", "Roberto Carlos", "José Vélez", "Julio Iglesias",
    "Nino Bravo", "Nelson Ned", "Jeanette", "Salvatore Adamo", "Nicola Di Bari",
    "Dyango", "Manolo Galván", "Yaco Monti", "Los Pasteles Verdes", "Juan Bau",
    "Danny Daniel", "Basilio", "Pablo Abraira", "Umberto Tozzi", "Matia Bazar",
    "Mari Trini", "Miguel Gallardo", "Sergio y Estíbaliz", "Mocedades", "Trigo Limpio",
    "Lorenzo Antonio", "Juan Gabriel", "Rocío Dúrcal", "José Luis Perales", "Ana Gabriel",
    "Daniela Romo", "Pimpinela", "Marisela", "Amanda Miguel", "Diego Verdaguer",
    "Luis Miguel", "Franco de Vita", "Ricardo Montaner", "Rudy La Scala", "Braulio",
    "Álvaro Torres", "José Luis Rodríguez", "Emmanuel", "Manuel Mijares", "Yuri",
    "Pandora", "Flans", "María Conchita Alonso", "Guillermo Dávila", "Kiara",
    "Karina", "Yolandita Monge", "Ednita Nazario", "Ricardo Arjona", "Alberto Cortez",
    "Alejandro Sanz", "Cristian Castro", "Myriam Hernández", "Laura Pausini", "Alejandro Fernández",
    "Chayanne", "Ricky Martin", "Eros Ramazzotti", "Sergio Dalma", "Gian Marco",
    "Jon Secada", "Soraya", "Shakira", "Enrique Iglesias", "Thalía",
    "Paulina Rubio", "Nek", "Sin Bandera", "Benny Ibarra", "Sentidos Opuestos",
    "MDO", "Charlie Zaa", "Julio Sabala", "Galy Galiano", "Lucas Arnau"
]

results = []
for artist in desired_artists:
    artist_lower = artist.lower().strip()
    # Find any artist in DB that contains the requested artist name or viceversa
    mask = df['clean_artist'].str.contains(artist_lower, na=False) | pd.Series([artist_lower in a if isinstance(a, str) else False for a in df['clean_artist']])
    matches = df[mask]
    
    total_songs = len(matches)
    songs_with_lyrics = matches['lyrics'].notna().sum()
    
    results.append({
        'Artista (Demandado)': artist,
        'Canciones en DB': total_songs,
        'Letras Completas': songs_with_lyrics,
        'Estatus': 'OK' if total_songs > 0 and songs_with_lyrics == total_songs else ('Cero Pistas' if total_songs == 0 else 'Faltan Letras')
    })

res_df = pd.DataFrame(results)

# Save markdown report
md_content = "# Reporte de Auditoría Musical (La Edad de Oro)\n\n"
md_content += f"**Artistas solicitados:** {len(desired_artists)}\n\n"
md_content += "### Artistas NO ENCONTRADOS (0 Canciones)\n"
cero = res_df[res_df['Canciones en DB'] == 0]
for _, row in cero.iterrows():
    md_content += f"- ❌ {row['Artista (Demandado)']}\n"

md_content += "\n### Artistas con FALTANTE DE LETRAS (La IA fallará)\n"
faltan = res_df[(res_df['Canciones en DB'] > 0) & (res_df['Letras Completas'] < res_df['Canciones en DB'])]
for _, row in faltan.iterrows():
    md_content += f"- ⚠️ {row['Artista (Demandado)']}: Tiene {row['Canciones en DB']} canciones, pero **SOLO {row['Letras Completas']}** tienen letra.\n"

md_content += "\n### Artistas PERFECTOS (100% Letras)\n"
ok = res_df[res_df['Estatus'] == 'OK']
for _, row in ok.iterrows():
    md_content += f"- ✅ {row['Artista (Demandado)']}: {row['Canciones en DB']} canciones con letras completas.\n"

with open('auditoria_artistas.md', 'w', encoding='utf-8') as f:
    f.write(md_content)
