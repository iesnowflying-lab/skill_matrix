import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import base64

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Skill Matrix Dashboard", layout="wide", page_icon="📊")

# --- FUNGSI LOAD LOGO ---
@st.cache_data
def get_base64_logo(url):
    try:
        file_id = url.split('/')[-2]
        direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        response = requests.get(direct_url, timeout=10)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode()
        return None
    except Exception:
        return None

# --- CSS MODERN DARK ENTERPRISE (Saran: Rounded Corners & Soft Contrast) ---
st.markdown("""
    <style>
    /* Mengatur Background Utama */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Header Berwarna dengan Border Bawah */
    .custom-header {
        background-color: #161b22;
        padding: 25px 40px;
        border-radius: 20px; /* Saran No. 2: Rounded Corners */
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 30px;
        border: 1px solid #30363d;
    }

    .title-text {
        color: #f0f6fc;
        font-size: 48px;
        font-weight: 800;
        margin: 0;
        letter-spacing: -1.5px;
    }

    .logo-img {
        height: 80px;
        width: auto;
        border-radius: 10px;
    }

    /* Kartu Metrik Modern (Soft Dark Mode) */
    div[data-testid="stMetric"] {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 18px; /* Saran No. 2: Rounded Corners */
        border: 1px solid #374151;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    
    [data-testid="stMetricValue"] {
        color: #38bdf8 !important; /* Warna Biru Muda Modern */
        font-weight: 700;
        font-size: 2rem !important;
    }

    [data-testid="stMetricLabel"] {
        color: #9ca3af !important;
        font-size: 1rem !important;
    }

    /* Merapikan Filter Expander */
    .streamlit-expanderHeader {
        background-color: #161b22 !important;
        border-radius: 12px !important;
        border: 1px solid #30363d !important;
    }
    
    .stDataFrame {
        border-radius: 15px;
        overflow: hidden;
    }

    /* Menghilangkan padding atas bawaan Streamlit */
    .block-container {
        padding-top: 2rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI LOAD DATA ---
@st.cache_data
def load_data():
    try:
        SHEET_URL = "https://docs.google.com/spreadsheets/d/1D2fWEf08Oks6XFvz5KBgHHUjxJiM38Z0/export?format=csv"
        df_raw = pd.read_csv(SHEET_URL)
        df_raw.columns = df_raw.iloc[1] 
        df_clean = df_raw.iloc[2:].reset_index(drop=True)
        SELECTED_COLUMNS = ['Building', 'SPV', 'Line', 'Name Opt', 'ID NO', 'Style', 'Process Part', 'Name Process (Bahasa)', 'Grade Process', 'Grade Countif', 'Grade Quality', 'Final Grade']
        df_final = df_clean[[c for c in SELECTED_COLUMNS if c in df_clean.columns]].copy()
        df_final = df_final.dropna(subset=['Name Process (Bahasa)'], how='all').reset_index(drop=True)
        return df_final
    except Exception:
        return pd.DataFrame()

# --- HEADER DASHBOARD ---
logo_data = get_base64_logo("https://drive.google.com/file/d/1zfkajHrUyDQ-q4ecPd7iVcK1bCEC3zmT/view?usp=sharing")

st.markdown(f"""
    <div class="custom-header">
        <h1 class="title-text">Skill Matrix Dashboard</h1>
        {"<img src='data:image/png;base64," + logo_data + "' class='logo-img'>" if logo_data else ""}
    </div>
""", unsafe_allow_html=True)

# --- LOGIKA UTAMA ---
try:
    df_display = load_data()
    if not df_display.empty:
        # Filter Section
        with st.expander("🔍 Filter Pencarian Cepat", expanded=True):
            f1, f2, f3, f4 = st.columns(4)
            with f1: s_name = st.text_input("Nama:")
            with f2: s_id = st.text_input("ID NO:")
            with f3:
                lines = df_display['Line'].ffill().unique()
                sel_line = st.selectbox("Line:", ["Semua"] + sorted([str(l) for l in lines if pd.notna(l)]))
            with f4:
                spvs = df_display['SPV'].ffill().unique()
                sel_spv = st.selectbox("SPV:", ["Semua"] + sorted([str(s) for s in spvs if pd.notna(s)]))

        # Logic Filter
        df_logic = df_display.copy()
        cols_fill = ['Building', 'SPV', 'Line', 'Name Opt', 'ID NO', 'Final Grade']
        df_logic[cols_fill] = df_logic[cols_fill].ffill()
        mask = pd.Series([True] * len(df_logic))
        if s_name: mask &= df_logic['Name Opt'].str.contains(s_name, case=False, na=False)
        if s_id: mask &= df_logic['ID NO'].astype(str).str.contains(s_id, case=False, na=False)
        if sel_line != "Semua": mask &= df_logic['Line'].astype(str) == sel_line
        if sel_spv != "Semua": mask &= df_logic['SPV'] == sel_spv
        df_filt_calc = df_logic[mask.values]

        # Visualization Section
        df_unique = df_filt_calc.drop_duplicates(subset=['ID NO'])
        total = len(df_unique)
        
        if total > 0:
            st.markdown("### 📊 Performa Grade Operator")
            
            col_left, col_right = st.columns([1.6, 1])
            
            with col_left:
                counts = df_unique['Final Grade'].value_counts().reset_index()
                counts.columns = ['Grade', 'Jumlah']
                counts['Label'] = "Grade " + counts['Grade'].astype(str)
                
                # Warna modern yang lebih teduh
                color_map = {'A':'#10b981','B':'#3b82f6','C':'#f59e0b','D':'#ef4444'}
                
                fig = px.pie(counts, values='Jumlah', names='Label', hole=0.6,
                             color='Grade', color_discrete_map=color_map)
                
                fig.update_traces(
                    textinfo='label+percent+value', 
                    textfont_size=14,
                    marker=dict(line=dict(color='#0e1117', width=2))
                )
                
                fig.update_layout(
                    showlegend=False, 
                    height=450, 
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=10, b=10, l=0, r=0)
                )
                st.plotly_chart(fig, use_container_width=True)
                
            with col_right:
                st.metric("Total Operator", f"{total} Org")
                st.write("") # Spacer
                
                m_col1, m_col2 = st.columns(2)
                grades = ['A', 'B', 'C', 'D']
                for i, g in enumerate(grades):
                    count = df_unique[df_unique['Final Grade'] == g].shape[0]
                    target_col = m_col1 if i % 2 == 0 else m_col2
                    target_col.metric(f"Grade {g}", f"{count} Org")

        st.divider()
        st.markdown(f"### 📑 Detail Data ({len(df_filt_calc)} Baris)")
        st.dataframe(df_display[mask.values].fillna(""), use_container_width=True, hide_index=True)
    else:
        st.error("Data tidak ditemukan. Periksa kembali filter atau koneksi spreadsheet.")
except Exception as e:
    st.error(f"Terjadi kesalahan teknis: {e}")