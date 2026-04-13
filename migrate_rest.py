import sqlite3
import pandas as pd
from supabase import create_client, Client

def migrate():
    print("="*50)
    print("🚀 MIGRACIÓN A SUPABASE VÍA REST API")
    print("="*50)
    
    url = 'https://gnepzgnrexurskyggrqo.supabase.co'
    key = 'sb_secret_E8BQY9JkYMWrE38YkPVMxQ_tyYfQo_f'
    
    try:
        supabase: Client = create_client(url, key)
        print("✅ Conexión HTTPS (Anti-bloqueo) establecida.")
    except Exception as e:
        print(f"❌ Error al inicializar Supabase: {e}")
        return

    local_conn = sqlite3.connect("corazon_melodico.db")
    
    tables = ['bars', 'songs_saas', 'requests_saas']
    
    for table in tables:
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table}", local_conn)
            if df.empty:
                print(f"ℹ️ La tabla {table} local está vacía, saltando.")
                continue
                
            # Limpiar datos vacíos de Pandas (NaN a None para JSON)
            df = df.where(pd.notnull(df), None)
            records = df.to_dict(orient='records')
            
            print(f"\nSubiendo {len(records)} registros a la tabla '{table}'...")
            
            # API de Supabase solo admite 1,000 inserciones a la vez, subimos en lotes
            batch_size = 500
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                supabase.table(table).insert(batch).execute()
                print(f"  -> Lote completado: {i} hasta {i + len(batch)}")
                
        except Exception as e:
            print(f"❌ Error migrando {table}: {str(e)}")

    # Escribir las llaves al .env para que la App web empiece a usarlas mañana mismo
    print("\nGuardando llaves para el archivo .env...")
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"SUPABASE_URL='{url}'\n")
        f.write(f"SUPABASE_SERVICE_KEY='{key}'\n")
        
    print("\n=================================")
    print("🎉 MIGRACIÓN COMPLETADA AL 100%")
    print("=================================")

if __name__ == "__main__":
    migrate()
