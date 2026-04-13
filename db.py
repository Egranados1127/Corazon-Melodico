import os
import pandas as pd
from datetime import datetime, timezone
import numpy as np
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")

# Si por alguna razón no detecta el archivo .env en producción
if not url or not key:
    try:
        import streamlit as st
        # Para Streamlit Cloud usa secrets
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_SERVICE_KEY"]
    except:
        pass

if url and key:
    supabase: Client = create_client(url, key)

def init_db():
    # Database is fully handled by Supabase in the Cloud now
    pass

def login_user(username, password):
    res = supabase.table('bars').select('id, name, primary_color, secondary_color, logo_url').eq('username', username).eq('password', password).execute()
    data = res.data
    if data:
        row = data[0]
        return (row['id'], row['name'], row['primary_color'], row['secondary_color'], row['logo_url'])
    return None

def get_bar_info(bar_id):
    res = supabase.table('bars').select('name, primary_color, secondary_color, logo_url').eq('id', bar_id).execute()
    data = res.data
    if data:
        row = data[0]
        return (row['name'], row['primary_color'], row['secondary_color'], row['logo_url'])
    return None

def get_songs(bar_id):
    res = supabase.table('songs_saas').select('*').eq('bar_id', bar_id).eq('is_banned', 0).order('title').execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=['id', 'bar_id', 'title', 'artist', 'album', 'genre', 'lyrics', 'is_banned'])

def get_active_requests_count(bar_id, table_id):
    res = supabase.table('requests_saas').select('id', count='exact').eq('bar_id', bar_id).eq('table_id', table_id).eq('status', 'pending').execute()
    return res.count

def add_request(bar_id, song_id, table_id):
    try:
        # Prevenir colisiones de IDs (Sequences fallando en Postgres tras migrar SQLite via REST)
        res = supabase.table('requests_saas').select('id').order('id', desc=True).limit(1).execute()
        next_id = res.data[0]['id'] + 1 if res.data else 1
        
        supabase.table('requests_saas').insert({
            'id': next_id,
            'bar_id': bar_id,
            'song_id': int(song_id),
            'table_id': table_id
        }).execute()
    except Exception:
        supabase.table('requests_saas').insert({
            'bar_id': bar_id,
            'song_id': int(song_id),
            'table_id': table_id
        }).execute()

def get_top_songs(bar_id, limit=4):
    res = supabase.table('requests_saas').select('*, songs_saas(title, artist)').eq('bar_id', bar_id).execute()
    data = res.data
    if not data:
        return pd.DataFrame(columns=['title', 'artist', 'total_requests'])
    
    records = []
    for r in data:
        s = r.get('songs_saas')
        if s:
            records.append({'title': s['title'], 'artist': s['artist']})
            
    if not records:
        return pd.DataFrame(columns=['title', 'artist', 'total_requests'])
        
    df = pd.DataFrame(records)
    grouped = df.groupby(['title', 'artist']).size().reset_index(name='total_requests')
    return grouped.sort_values(by='total_requests', ascending=False).head(limit)

def get_played_history(bar_id, limit=20):
    res = supabase.table('requests_saas').select('*, songs_saas(title, artist)').eq('bar_id', bar_id).eq('status', 'played').order('requested_at', desc=True).limit(limit).execute()
    data = res.data
    if not data:
        return pd.DataFrame(columns=['title', 'artist', 'table_id', 'requested_at'])
        
    records = []
    for r in data:
        s = r.get('songs_saas')
        if s:
            records.append({
                'title': s['title'],
                'artist': s['artist'],
                'table_id': r['table_id'],
                'requested_at': r['requested_at']
            })
    return pd.DataFrame(records)

def get_queue(bar_id):
    res = supabase.table('requests_saas').select('*').eq('bar_id', bar_id).eq('status', 'pending').execute()
    data = res.data
    if not data:
        return pd.DataFrame()
        
    songs_res = supabase.table('songs_saas').select('*').eq('bar_id', bar_id).execute()
    songs_dict = {s['id']: s for s in songs_res.data}
        
    records = []
    for row in data:
        s = songs_dict.get(row['song_id'])
        if s:
            records.append({
                'song_id': s['id'],
                'title': s['title'],
                'artist': s['artist'],
                'lyrics': s['lyrics'],
                'table_id': row['table_id'],
                'requested_at': row['requested_at']
            })
            
    if not records:
        return pd.DataFrame()
        
    df = pd.DataFrame(records)
    grouped = df.copy()
    grouped.fillna({'lyrics': ''}, inplace=True)
    grouped = grouped.groupby(['song_id', 'title', 'artist']).agg(
        total_requests=('table_id', 'count'),
        requesting_tables=('table_id', lambda x: ','.join(x.unique())),
        oldest_request_time=('requested_at', 'min'),
        lyrics=('lyrics', 'first')
    ).reset_index()
    
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    grouped['oldest_request_time'] = pd.to_datetime(grouped['oldest_request_time'], errors='coerce', utc=True).dt.tz_localize(None)
    grouped['minutes_waiting'] = (now - grouped['oldest_request_time']).dt.total_seconds() / 60.0
    grouped['minutes_waiting'] = grouped['minutes_waiting'].clip(lower=0) 
    grouped['score'] = (grouped['total_requests'] * 10) + (np.log1p(grouped['minutes_waiting']) * 5)
    
    return grouped.sort_values(by='score', ascending=False)

def mark_song_played(bar_id, song_id):
    # in_ is correct syntax for python client
    supabase.table('requests_saas').update({'status': 'played'}).eq('bar_id', bar_id).eq('song_id', song_id).in_('status', ['pending', 'pending_download']).execute()

def mark_song_pending_download(bar_id, song_id):
    supabase.table('requests_saas').update({'status': 'pending_download'}).eq('bar_id', bar_id).eq('song_id', song_id).eq('status', 'pending').execute()

def reject_and_delete_song(bar_id, song_id):
    try:
        supabase.table('requests_saas').update({'status': 'rejected'}).eq('bar_id', bar_id).eq('song_id', song_id).eq('status', 'pending').execute()
        supabase.table('songs_saas').update({'is_banned': 1}).eq('bar_id', bar_id).eq('id', song_id).execute()
    except:
        pass

def get_table_alerts(bar_id, table_id):
    res = supabase.table('requests_saas').select('*, songs_saas(title, artist)').eq('bar_id', bar_id).eq('table_id', table_id).in_('status', ['pending_download', 'rejected']).execute()
    data = res.data
    if not data:
        return pd.DataFrame(columns=['title', 'artist', 'status'])
        
    records = []
    for r in data:
        s = r.get('songs_saas')
        if s:
            records.append({'title': s['title'], 'artist': s['artist'], 'status': r['status']})
            
    if not records:
        return pd.DataFrame(columns=['title', 'artist', 'status'])
        
    df = pd.DataFrame(records)
    return df.drop_duplicates()

def get_download_backlog(bar_id):
    res = supabase.table('requests_saas').select('*, songs_saas(title, artist)').eq('bar_id', bar_id).eq('status', 'pending_download').execute()
    data = res.data
    if not data: return pd.DataFrame()
    
    records = []
    for r in data:
        s = r.get('songs_saas')
        if s:
            records.append({
                'song_id': r['song_id'],
                'title': s['title'],
                'artist': s['artist'],
                'table_id': r['table_id']
            })
    if not records: return pd.DataFrame()
    df = pd.DataFrame(records)
    
    grouped = df.groupby(['song_id', 'title', 'artist']).agg(
        total_requests=('table_id', 'count'),
        requesting_tables=('table_id', lambda x: ','.join(pd.Series(x).unique()))
    ).reset_index()
    return grouped

def insert_songs_bulk(bar_id, songs_list):
    batch = []
    for s in songs_list:
        batch.append({'bar_id': bar_id, 'title': s[0], 'artist': s[1], 'album': s[2], 'genre': s[3]})
        if len(batch) >= 500:
            supabase.table('songs_saas').insert(batch).execute()
            batch = []
    if batch:
        supabase.table('songs_saas').insert(batch).execute()

def update_bar_identity(bar_id, primary, secondary, logo_url):
    supabase.table('bars').update({'primary_color': primary, 'secondary_color': secondary, 'logo_url': logo_url}).eq('id', bar_id).execute()
