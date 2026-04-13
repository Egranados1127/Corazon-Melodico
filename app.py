import streamlit as st
import requests
import pandas as pd
from db import init_db, get_songs, get_active_requests_count, add_request, get_queue, mark_song_played, insert_songs_bulk, get_bar_info, login_user, get_top_songs, get_played_history, mark_song_pending_download, reject_and_delete_song, get_download_backlog, get_table_alerts, update_bar_identity
from ui_components import apply_custom_css
import time

try:
    from streamlit_mic_recorder import speech_to_text
except ImportError:
    speech_to_text = None

st.set_page_config(page_title="MelodicSaaS | Software para Bares", page_icon="🤖", layout="centered", initial_sidebar_state="collapsed")
init_db()

query_params = st.query_params
url_bar_id = query_params.get("bar", None)
mesa_param = query_params.get("mesa", None)

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.query_params.clear()

# =======================================================
# 1. RUTA VISTA CLIENTE (MESA ESCANEÓ SU PROPIO QR)
# =======================================================
if mesa_param and url_bar_id:
    bar_data = get_bar_info(url_bar_id)
    if not bar_data:
        st.error("Código QR Inválido. Universo inactivo.")
        st.stop()
        
    bar_name, primary_c, secondary_c, logo_url = bar_data
    apply_custom_css(primary_c, secondary_c, logo_url)
    mesa_id = f"Mesa {mesa_param}"
    
    col1, col2 = st.columns([4, 1])
    with col1:
        if logo_url:
            st.markdown(f"<img src='{logo_url}' style='max-height: 60px; margin-bottom: 10px;' />", unsafe_allow_html=True)
        else:
            st.title(bar_name)
    with col2:
        if st.button("⬅️"):
            st.query_params.clear()
            st.rerun()

    st.markdown(f"#### 📍 {mesa_id} | Catálogo Exclusivo")
    st.divider()

    active_requests = get_active_requests_count(url_bar_id, mesa_id)
    
    alerts_df = get_table_alerts(url_bar_id, mesa_id)
    if not alerts_df.empty:
        for _, alert in alerts_df.iterrows():
            if alert['status'] == 'pending_download':
                st.warning(f"📻 El DJ está buscando o descargando **{alert['title']}** ({alert['artist']}) para ti. ¡No gasta tu cupo!")
            elif alert['status'] == 'rejected':
                st.error(f"❌ **{alert['title']}** ({alert['artist']}) fue eliminada por el DJ (Música fuera de contexto para este negocio). Se te devolvió tu cupo.")
    
    songs_df = get_songs(url_bar_id)
    if songs_df.empty:
        st.info("El DJ de este bar aún no ha subido el catálogo.")
        st.stop()
        
    q_df = get_queue(url_bar_id)
    if not q_df.empty:
        st.markdown("<p style='font-size: 0.85em; color: #a0a0a0; margin-bottom: 5px; font-weight: bold;'>⏳ Próximas Peticiones:</p>", unsafe_allow_html=True)
        tags_html = ""
        for idx, row in q_df.iterrows():
            tags_html += f"<span style='background-color: {secondary_c}22; color: {secondary_c}; border: 1px solid {secondary_c}55; padding: 4px 10px; border-radius: 15px; font-size: 0.8em; display: inline-block; margin: 0 5px 5px 0; font-weight: bold;'>#{idx+1} {row['title']}</span>"
        st.markdown(f"<div>{tags_html}</div><br>", unsafe_allow_html=True)

    if active_requests >= 3:
        st.error("⏳ Límite de 3 pedidos activos alcanzado. Espera tu turno mágico para pedir más.")
    else:
        # =================================================
        # UI: Layout de Búsqueda Premium 
        # =================================================
        
        # Zona Mágica (Hero Central)
        st.markdown("<div class='magic-text' style='margin-top:15px;'>✨ LA MAGIA ESTÁ AQUÍ 👇</div>", unsafe_allow_html=True)
        
        if "stt_key" not in st.session_state:
            st.session_state.stt_key = "STT_0"
        if "voice_memory" not in st.session_state:
            st.session_state.voice_memory = ""
            
        # Centrar el botón del micrófono usando columnas vacías a los lados
        col_m1, col_m2, col_m3 = st.columns([1, 2, 1])
        with col_m2:
            text_from_voice = ""
            if speech_to_text:
                text_from_voice = speech_to_text(language='es-ES', start_prompt="🎙️ TÓCAME Y CANTA UN PEDACITO", stop_prompt="⏳ TE ESTOY ESCUCHANDO...", just_once=True, key=st.session_state.stt_key)
                st.markdown("<p style='font-size:0.7em; color:#888; text-align:center; margin-top:-5px;'><i>Filtro Inteligente: Acerca el celular</i></p>", unsafe_allow_html=True)
                
            if text_from_voice:
                st.session_state.voice_memory = text_from_voice

            if st.session_state.voice_memory:
                if st.button("❌ Borrar Búsqueda por Voz", use_container_width=True):
                    st.session_state.voice_memory = ""
                    st.session_state.stt_key += "X"
                    st.rerun()
        
        st.markdown("<p style='text-align:center; color:#A0A0A0; font-size:0.85em; margin-bottom: 2px;'>o usa el catálogo tradicional:</p>", unsafe_allow_html=True)
        
        # Zona Tradicional (Lado a lado)
        col_search, col_artist = st.columns(2)
        with col_search:
            search_text = st.text_input("🔍 Nombre o Disco...", label_visibility="collapsed", placeholder="🔍 Título o disco...")
        with col_artist:
            artistas = ["Explorar Artista..."] + sorted(songs_df['artist'].unique().tolist())
            selected_artist = st.selectbox("🎤 Filtrar Artista:", artistas, label_visibility="collapsed")
            
        search = st.session_state.voice_memory if st.session_state.voice_memory else search_text
            
        if search:
            exact_matches = songs_df[
                songs_df['title'].str.contains(search, case=False) | 
                songs_df['artist'].str.contains(search, case=False)
            ]
            
            semantic_matches = pd.DataFrame()
            # La Inteligencia Semántica SOLO se activa al cantar (Micrófono)
            if st.session_state.voice_memory and 'lyrics' in songs_df.columns:
                valid_lyrics_df = songs_df.dropna(subset=['lyrics'])
                if not valid_lyrics_df.empty and len(search) >= 4:
                    try:
                        from sklearn.feature_extraction.text import TfidfVectorizer
                        from sklearn.metrics.pairwise import cosine_similarity
                        vectorizer = TfidfVectorizer()
                        tfidf_matrix = vectorizer.fit_transform(valid_lyrics_df['lyrics'])
                        query_vec = vectorizer.transform([search])
                        sims = cosine_similarity(query_vec, tfidf_matrix).flatten()
                        top_indices = sims.argsort()[-5:][::-1]
                        found_semantic = [valid_lyrics_df.iloc[idx] for idx in top_indices if sims[idx] > 0.03]
                        if found_semantic:
                            semantic_matches = pd.DataFrame(found_semantic)
                    except:
                        pass
            
            filtered_df = pd.concat([exact_matches, semantic_matches]).drop_duplicates(subset=['id']).head(15)
        elif selected_artist != "Elige un Artista...":
            filtered_df = songs_df[songs_df['artist'] == selected_artist]
        else:
            filtered_df = pd.DataFrame()
            
        if not filtered_df.empty:
            for _, row in filtered_df.iterrows():
                snippet_html = ""
                # Si es búsqueda por voz, obligatoriamente mostramos la estrofa
                if st.session_state.voice_memory and 'lyrics' in row and pd.notna(row['lyrics']) and row['lyrics']:
                    lyrics_lower = row['lyrics'].lower()
                    search_lower = st.session_state.voice_memory.lower()
                    
                    if search_lower in lyrics_lower:
                        idx = lyrics_lower.find(search_lower)
                        start = max(0, idx - 40)
                        end = min(len(row['lyrics']), idx + len(st.session_state.voice_memory) + 40)
                        texto_cortado = row['lyrics'][start:end].replace('\n', ' / ')
                        snippet_html = f"<br><span style='color:inherit; font-size:0.85em; font-style:italic; opacity:0.8;'>«...{texto_cortado}...»</span>"
                    else:
                        # Como la IA Vectorial lo encontró por similitud (sin coincidencia literal exacta)
                        # Mostramos obligatoriamente las primeras líneas de la canción
                        texto_cortado = row['lyrics'][:80].replace('\n', ' / ')
                        snippet_html = f"<br><span style='color:inherit; font-size:0.85em; font-style:italic; opacity:0.8;'>«{texto_cortado}...»</span>"

                cols = st.columns([3, 1])
                with cols[0]:
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(90deg, {primary_c}33 0%, transparent 100%);
                        border-radius: 8px;
                        padding: 12px;
                        border-left: 3px solid {secondary_c};
                        margin-bottom: 5px;
                    ">
                        <div style="font-size:1.15em; font-weight:900; color:#ffffff; letter-spacing:0.5px;">{row['title']}</div>
                        <div style="font-size:0.85em; color:{secondary_c}; font-weight:bold; margin-top:2px;">🎤 {row['artist']}</div>
                        <div style="font-size:0.8em; color:#A0A0A0; font-style:italic;">💿 {row['album'] if row['album'] else 'Sencillo'}</div>
                        {snippet_html}
                    </div>
                    """, unsafe_allow_html=True)
                with cols[1]:
                    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                    if st.button("Pedir ✨", key=f"req_{row['id']}", use_container_width=True):
                        add_request(url_bar_id, row['id'], mesa_id)
                        st.balloons()
                        time.sleep(1.5)
                        st.rerun()
                st.markdown("<br>", unsafe_allow_html=True)

    st.divider()
    with st.expander("✅ Historial de la Mesa (Ya Sonaron)"):
        h_df = get_played_history(url_bar_id, limit=30)
        if h_df.empty:
            st.info("La noche apenas comienza.")
        else:
            for idx, row in h_df.iterrows():
                st.markdown(f"""
                <div style="background: linear-gradient(90deg, {primary_c}40 0%, transparent 100%);
                            padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid {secondary_c}; opacity: 0.85;">
                    <div style="font-size:1.1em; font-weight:bold; color:#fff; display:flex; justify-content:space-between;">
                        <span>{row['title']}</span>
                        <span style="font-size:0.7em; color:{secondary_c};">♪</span>
                    </div>
                    <div style="font-size:0.85em; color:{secondary_c}; margin-top:2px;">🎤 {row['artist']}</div>
                    <div style="font-size:0.75em; color:#fff; background:{primary_c}; padding:2px 8px; border-radius:10px; display:inline-block; margin-top:5px; opacity:0.8;">❤️ Por: {row['table_id']}</div>
                </div>
                """, unsafe_allow_html=True)

# =======================================================
# 2. PORTAL CERRADO PARA DJ (LOGIN AL UNIVERSO)
# =======================================================
else:
    # SI NO HAY DUEÑO LOGEADO, MOSTRAR LOGIN PRIVADO
    if "admin_logged_in" not in st.session_state:
        apply_custom_css("#121212", "#E0E0E0")
        
        st.markdown("<h1 style='text-align:center;'>MelodicSaaS | Portal Propietarios</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#A0A0A0;'>Inicia Sesión en el Universo Privado de tu Bar</p><br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                user = st.text_input("Usuario")
                pwd = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Ingresar a Mi Negocio"):
                    login_data = login_user(user, pwd)
                    if login_data:
                        st.session_state.admin_logged_in = True
                        st.session_state.admin_bar_id = login_data[0]
                        st.session_state.admin_bar_name = login_data[1]
                        st.session_state.admin_primary = login_data[2]
                        st.session_state.admin_secondary = login_data[3]
                        st.session_state.admin_logo_url = login_data[4]
                        st.success("¡Autenticado con éxito!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Credenciales Inválidas.")
        
        st.info("💡 **Ayuda Demo:**\n- Usuario: `romantico` (Clave `123`) para ver tu clásico Corazón Melódico.\n- Usuario: `rock` (Clave `123`) para simular la privacidad de un Pub distinto.")
    
    # SI EL DUEÑO ESTÁ LOGEADO, MUESTRA SU PANEL (VISTA DJ)
    else:
        bar_id = st.session_state.admin_bar_id
        bar_name = st.session_state.admin_bar_name
        primary_c = st.session_state.admin_primary
        secondary_c = st.session_state.admin_secondary
        logo_url = st.session_state.admin_logo_url
        apply_custom_css(primary_c, secondary_c, logo_url)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if logo_url:
                st.markdown(f"<img src='{logo_url}' style='max-height: 80px; margin-bottom: 10px;' />", unsafe_allow_html=True)
            else:
                st.title(f"🎧 Portal del DJ: {bar_name}")
        with col2:
            if st.button("Cerrar Sesión (Cambiar Universo)"):
                logout()
                st.rerun()

        st.success(f"Estás dentro de tu propio universo de datos. Tus canciones y pedidos son 100% privados a tu negocio.")
        st.info(f"👉 **Enlace para tus clientes (Imprime el QR):** `URL/?bar={bar_id}&mesa=X`")
        
        if st.button("Simulador de Escaneo de tu QR por un local (Mesa 10)"):
            st.query_params["bar"] = bar_id
            st.query_params["mesa"] = "10"
            st.rerun()

        st.divider()
        
        with st.expander("⚙️ Ajustes de Identidad Visual (Tu Marca)"):
            st.markdown("<p style='color:#bbb;'>Personaliza los colores y el Logo de tu Bar para que tus clientes se sientan en casa al escanear.</p>", unsafe_allow_html=True)
            col_cc1, col_cc2 = st.columns(2)
            with col_cc1:
                new_primary = st.color_picker("Color Primario (Fondos)", primary_c)
            with col_cc2:
                new_secondary = st.color_picker("Color Secundario (Brillo/Neón)", secondary_c)
            
            uploaded_logo = st.file_uploader("Sube o arrastra el Logo de tu Bar", type=["png", "jpg", "jpeg", "webp"])
            
            if st.button("Guardar Identidad Visible"):
                final_logo = logo_url
                if uploaded_logo is not None:
                    import base64
                    encoded = base64.b64encode(uploaded_logo.read()).decode()
                    mime_type = uploaded_logo.type
                    final_logo = f"data:{mime_type};base64,{encoded}"
                
                update_bar_identity(bar_id, new_primary, new_secondary, final_logo)
                
                st.session_state.admin_primary = new_primary
                st.session_state.admin_secondary = new_secondary
                st.session_state.admin_logo_url = final_logo
                
                st.success("¡Identidad visual aplicada inmediatamente!")
                time.sleep(1)
                st.rerun()

        st.divider()
        
        # TABLERO DE MEMORIA (TOP DISCOS)
        st.subheader("🏆 Histórico Mensual: El Playlist de Oro")
        st.markdown("<p style='color:#A0A0A0; font-size: 0.9em; margin-top:-10px;'>Las 4 canciones que más facturan en tu bar.</p>", unsafe_allow_html=True)
        top_df = get_top_songs(bar_id, limit=4)
        if not top_df.empty:
            for i, (_, row) in enumerate(top_df.iterrows()):
                st.markdown(f"""
                <div style="background: linear-gradient(145deg, {primary_c}1A 0%, #111111 100%);
                            border-left: 4px solid {secondary_c};
                            border-radius: 12px;
                            padding: 15px 20px;
                            margin-bottom: 12px;
                            box-shadow: 0px 5px 15px rgba(0,0,0,0.5);
                            display: flex;
                            align-items: center;
                            position: relative;
                            overflow: hidden;
                            transition: transform 0.2s;">
                    <div style="font-size: 3.5em; color: {secondary_c}; opacity: 0.15; position: absolute; right: 20px; top: -10px; font-weight:900; font-style:italic;">#{i+1}</div>
                    <div style="flex: 1; z-index:2;">
                        <h3 style="margin:0; font-size:1.3em; color:#fff; text-shadow: 0 0 10px {secondary_c}40;">{row['title']}</h3>
                        <p style="margin:2px 0 8px 0; color:#ccc; font-size:0.9em;">{row['artist']}</p>
                        <span style="background: {secondary_c}; color: #000; padding: 3px 10px; border-radius: 20px; font-weight: bold; font-size: 0.75em; text-transform:uppercase; letter-spacing:1px;">🔥 Sonada {row['total_requests']} veces</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Aún no tienes historial suficiente para calcular los Top.")
            
        st.divider()
        st.subheader("Cola de Peticiones en Vivo")
        queue_df = get_queue(bar_id)
        if queue_df.empty:
            st.markdown("La cola del DJ de tu bar está vacía por ahora.")
        else:
            for idx, row in queue_df.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class="glass-card">
                        <h2 style="margin-top:0;">#{idx + 1} - {row['title']}</h2>
                        <p><b>Artista:</b> {row['artist']} | <b>Mesas Pidieron:</b> {row['requesting_tables']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    cols_act = st.columns(3)
                    with cols_act[0]:
                        if st.button(f"🎧 Sonando", key=f"play_{row['song_id']}", use_container_width=True):
                            mark_song_played(bar_id, row['song_id'])
                            st.rerun()
                    with cols_act[1]:
                        if st.button(f"⬇️ Pend. Descarga", key=f"pdl_{row['song_id']}", use_container_width=True):
                            mark_song_pending_download(bar_id, row['song_id'])
                            st.rerun()
                    with cols_act[2]:
                        if st.button(f"❌ Borrar Catálogo", key=f"rej_{row['song_id']}", use_container_width=True):
                            reject_and_delete_song(bar_id, row['song_id'])
                            st.rerun()

        st.divider()
        st.subheader("📦 Backlog: Pendientes por Descargar")
        st.markdown("<p style='color:#A0A0A0; font-size: 0.9em; margin-top:-10px;'>Las apartaste porque no las tenías en tu PC local/Spotify.</p>", unsafe_allow_html=True)
        backlog_df = get_download_backlog(bar_id)
        if backlog_df.empty:
            st.markdown("Estás al día.")
        else:
            for idx, row in backlog_df.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div style="border: 1px dashed {secondary_c}; padding: 10px; margin-bottom:5px; border-radius: 8px;">
                        <h4 style="margin:0;">{row['title']} - {row['artist']}</h4>
                        <p style="margin:0; font-size:0.8em; color:#ccc;">Pidieron: {row['requesting_tables']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"✅ Ya la descargué (Marcar Sonada)", key=f"res_{row['song_id']}", use_container_width=True):
                        mark_song_played(bar_id, row['song_id'])
                        st.rerun()
