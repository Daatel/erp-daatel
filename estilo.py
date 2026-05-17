import streamlit as st

def carregar_estilo():
    st.markdown("""
    <style>
        .stTextInput label p, .stSelectbox label p, .stNumberInput label p, .stDateInput label p {
            color: #01743d !important;
            font-weight: 600 !important;
        }
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
            border-color: #01743d40 !important;
        }
        h1, h2, h3 {
            color: #292d77 !important;
        }
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border-left: 5px solid #01743d;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .daatel-footer {
            position: fixed;
            bottom: 10px;
            right: 15px;
            color: #666666;
            font-size: 11px;
            font-weight: 500;
            z-index: 9999;
            background-color: rgba(255, 255, 255, 0.7);
            padding: 2px 8px;
            border-radius: 4px;
        }
    </style>
    <div class="daatel-footer notranslate" translate="no">
        <span style="display: block; font-size: 9px; text-align: left; opacity: 0.7; margin-bottom: -2px; letter-spacing: 0.5px;">Powered by</span>
        Daatel : Wisdom into Tech
    </div>
    """, unsafe_allow_html=True)
