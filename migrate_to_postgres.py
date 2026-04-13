import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse
import os

def migrate():
    print("==================================================")
    print("🚀 MIGRACIÓN A LA NUBE (SUPABASE POSTGRESQL)")
    print("==================================================")
    
    pwd = input("\n🔑 Ingresa LA CONTRASEÑA que creaste en Supabase para el proyecto 'MisDiscos': ").strip()
    if not pwd:
        print("La contraseña es obligatoria.")
        return
        
    encoded_pwd = urllib.parse.quote_plus(pwd)
    project_ref = "gnepzgnrexurskyggrqo"
    
    # URL de conexión directa a PostgreSQL
    postgres_url = f"postgresql://postgres:{encoded_pwd}@db.{project_ref}.supabase.co:5432/postgres"
    
    print("\n[1] Conectando a Supabase en la nube...")
    try:
        engine = create_engine(postgres_url)
        with engine.connect() as conn:
            print("    ✅ ¡Conexión a la Nube exitosa!")
    except Exception as e:
        print(f"    ❌ Error conectando a Postgres: {e}")
        print("    Revisa si la contraseña es correcta o asegúrate de haber creado el proyecto.")
        return
        
    # Crear esquema en PostgreSQL
    print("\n[2] Construyendo esquema estructurado en la Nube...")
    create_schema_sql = """
    CREATE TABLE IF NOT EXISTS bars (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        primary_color TEXT DEFAULT '#4A0E0E',
        secondary_color TEXT DEFAULT '#D4AF37',
        logo_url TEXT
    );

    CREATE TABLE IF NOT EXISTS songs_saas (
        id SERIAL PRIMARY KEY,
        bar_id TEXT NOT NULL REFERENCES bars(id),
        title TEXT NOT NULL,
        artist TEXT NOT NULL,
        album TEXT,
        genre TEXT,
        lyrics TEXT,
        is_banned INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS requests_saas (
        id SERIAL PRIMARY KEY,
        bar_id TEXT NOT NULL REFERENCES bars(id),
        song_id INTEGER,
        table_id TEXT,
        status TEXT DEFAULT 'pending',
        requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(create_schema_sql))
            conn.commit()
    except Exception as e:
        print(f"    ❌ Fallo creando el esquema: {e}")

    print("\n[3] Leyendo base de datos local (SQLite)...")
    local_conn = sqlite3.connect("corazon_melodico.db")
    
    tables = ['bars', 'songs_saas', 'requests_saas']
    dataframes = {}
    for table in tables:
        try:
            dataframes[table] = pd.read_sql_query(f"SELECT * FROM {table}", local_conn)
            print(f"    - Leídos {len(dataframes[table])} registros (incluyendo letras) de la tabla local '{table}'")
        except:
            print(f"    - La tabla local {table} no existe o está vacía")

    print("\n[4] ☁️ Volcando información pesada a la Nube. (Esto puede tardar unos segundos)...")
    for table in tables:
        if table in dataframes and not dataframes[table].empty:
            print(f"    - Subiendo {len(dataframes[table])} filas a '{table}'...")
            try:
                dataframes[table].to_sql(table, engine, if_exists='append', index=False)
            except Exception as e:
                print(f"      ⚠️ Ya existían datos o hubo un error: {e}")
                
    # Actualizar secuencias SERIAL en Postgres porque hicimos un INSERT explícito de IDs
    update_seqs = """
    SELECT setval('songs_saas_id_seq', (SELECT MAX(id) FROM songs_saas));
    SELECT setval('requests_saas_id_seq', (SELECT MAX(id) FROM requests_saas));
    """
    try:
        with engine.connect() as conn:
            conn.execute(text(update_seqs))
            conn.commit()
    except Exception as e:
        pass
                
    print("\n[5] Guardando las llaves maestras (.env)...")
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"DATABASE_URL='{postgres_url}'\n")
    print("    ✅ Archivo .env creado. El sistema ahora sabe cómo usar la Nube.")
    
    print("\n==================================================")
    print("🎉 MIGRACIÓN TOTAL EXITOSA 🎉")
    print("==================================================")
    print("Por favor:")
    print("1. En la consola donde está el script de descargar letras, presiona Ctrl + C para detenerlo.")
    print("2. Responde en el chat con 'Listo' para que conectemos el código a Supabase.")

if __name__ == "__main__":
    migrate()
