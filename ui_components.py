import streamlit as st

def apply_custom_css(primary="#4A0E0E", secondary="#D4AF37", logo_url=None):
    bg_css = "background-color: #121212;"
    if logo_url:
        bg_css = f"""
            background-color: #121212;
            background-image: radial-gradient(circle at center, rgba(18, 18, 18, 0.75) 0%, rgba(18, 18, 18, 0.92) 100%), url('{logo_url}');
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center center;
            background-attachment: fixed;
        """
        
    st.markdown(f"""
        <style>
        .block-container {{
            padding-top: 2rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            padding-bottom: 2rem !important;
        }}
        
        @keyframes magicPulse {{
            0% {{ transform: scale(1); text-shadow: 0 0 5px {secondary}; }}
            50% {{ transform: scale(1.05); text-shadow: 0 0 15px {secondary}, 0 0 25px #ffffff; }}
            100% {{ transform: scale(1); text-shadow: 0 0 5px {secondary}; }}
        }}
        
        .magic-text {{
            text-align: center;
            font-size: 1.1em;
            font-weight: 900;
            color: {secondary};
            margin-bottom: 5px;
            animation: magicPulse 2s infinite;
        }}
        
        iframe {{
            transform: scale(1.6) !important;
            transform-origin: top center !important;
            margin-bottom: 25px !important;
        }}

        .stApp {{
            {bg_css}
            color: #E0E0E0;
        }}
        
        .glass-card {{
            background: {primary}40;
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border-radius: 12px;
            border: 1px solid {secondary}66;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
            transition: transform 0.3s ease;
        }}
        .glass-card:hover {{
            transform: translateY(-2px);
        }}
        
        h1, h2, h3, h4, h5 {{
            color: {secondary} !important;
            font-family: 'Georgia', serif;
            letter-spacing: 1px;
        }}
        
        .stButton>button {{
            background: linear-gradient(135deg, {primary}, #111111) !important;
            color: {secondary} !important;
            border: 1px solid {secondary} !important;
            border-radius: 8px !important;
            font-weight: bold;
            box-shadow: 2px 4px 10px rgba(0,0,0,0.5) !important;
            transition: all 0.3s ease-in-out !important;
            width: 100%;
        }}
        
        .stButton>button:hover {{
            background: linear-gradient(135deg, {secondary}, #444444) !important;
            color: #121212 !important;
            border: 1px solid {primary} !important;
            transform: scale(1.03) !important;
            box-shadow: 2px 6px 15px {secondary}66 !important;
        }}

        .stTextInput>div>div>input {{
            background-color: rgba(255, 255, 255, 0.05) !important;
            color: #E0E0E0 !important;
            border: 1px solid #777777 !important;
            border-radius: 8px;
        }}
        
        #MainMenu {{visibility: hidden;}}
        header {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        
        hr {{
            border-bottom: 1px solid {secondary}4D !important;
        }}
        </style>
    """, unsafe_allow_html=True)
