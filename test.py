import pandas as pd
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json

url = 'https://gnepzgnrexurskyggrqo.supabase.co/rest/v1/songs_saas?select=id,title,lyrics'
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

df = pd.DataFrame(all_data).dropna(subset=['lyrics'])
vectorizer = TfidfVectorizer(strip_accents='unicode')
tfidf = vectorizer.fit_transform(df['lyrics'])
q = vectorizer.transform(['el agua pasada no mueve molinos'])
sims = cosine_similarity(q, tfidf).flatten()
top = sims.argsort()[-10:][::-1]

with open('test_sims.txt', 'w', encoding='utf-8') as f:
    for i in top:
        f.write(f"{df.iloc[i]['title']}: {sims[i]}\n")
