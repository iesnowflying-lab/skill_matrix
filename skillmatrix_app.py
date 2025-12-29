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

# --- CSS CUSTOM (NAVY HEADER & CONTRAST CONTENT) ---
st.markdown("""
    <style>
    /* Mengatur Judul agar Putih dan Jelas di atas Header Navy */
    .title-text {
        color: #FFFFFF !important;
        font-size: 42px;
        font-weight: 800;
        margin: 0;
        letter-spacing: -1px;
    }

    /* Header Biru Gelap (Navy) khusus agar Logo Putih Snowflying Menjol */
    .custom-header {
        background-color: #1E293B; 
        padding: 20px 45px;
        border-radius: 15px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 30px;
        border: 1px solid #334155;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }

    .logo-img {
        height: 85px; /* Ukuran diperbesar sedikit agar lebih gagah */
        width: auto;
    }

    /* METRIK: Dibuat Terang agar tulisan Hitam Terbaca Jelas */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    [data-testid="stMetricValue"] {
        color: #0F172A !important; /* Angka Hitam Pekat */
        font-weight: 700;
    }

    [data-testid="stMetricLabel"] {
        color: #475569 !important; /* Label Abu Tua */
    }

    /* Menyesuaikan area konten utama */
    .block-container {
        padding-top: 2rem !important;
    }
    
    /* Menghaluskan tampilan Filter Expander */
    .stExpander {
        border-radius: 12px !important;
        background-color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI LOAD DATA ---
@st.cache_data
def load_data():
    try:
        # Link export CSV dari Google Sheets Anda
        SHEET_URL = "https://docs.google.com/spreadsheets/d/1D2fWEf08Oks6XFvz5KBgHHUjxJiM38Z0/export?format=csv"
        df_raw = pd.read_csv(SHEET_URL)
        df_raw.columns = df_raw.iloc[1] 
        df_clean = df_raw.iloc[2:].reset_index(drop=True)
        
        SELECTED_COLUMNS = ['Building', 'SPV', 'Line', 'Name Opt', 'ID NO', 'Style', 'Process Part', 'Name Process (Bahasa)', 'Grade Process', 'Grade Countif', 'Grade Quality', 'Final Grade']
        df_final = df_clean[[c for c in SELECTED_COLUMNS if c in df_clean.columns]].copy()
        df_final = df_final.dropna(subset=['Name Process (Bahasa)'], how='all').reset_index(drop=True)
        return df_final
    except:
        return pd.DataFrame()

# --- HEADER DASHBOARD (DENGAN LOGO BARU ANDA) ---
logo_data = get_base64_logo("https://drive.google.com/file/d/1zfkajHrUyDQ-q4ecPd7iVcK1bCEC3zmT/view?usp=sharing")

st.markdown(f"""
    <div class="custom-header">
        <h1 class="title-text">Skill Matrix Dashboard</h1>
        {"<img src='data:image/png;base64," + logo_data + "' class='logo-img'>" if logo_data else ""}
    </div>
""", unsafe_allow_html=True)

# --- LOGIKA DASHBOARD ---
try:
    df_display = load_data()
    if not df_display.empty:
        # Bagian Filter
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

        # Filter Logic (Filldown agar data line/spv tidak kosong)
        df_logic = df_display.copy()
        cols_fill = ['Building', 'SPV', 'Line', 'Name Opt', 'ID NO', 'Final Grade']
        df_logic[cols_fill] = df_logic[cols_fill].ffill()
        
        mask = pd.Series([True] * len(df_logic))
        if s_name: mask &= df_logic['Name Opt'].str.contains(s_name, case=False, na=False)
        if s_id: mask &= df_logic['ID NO'].astype(str).str.contains(s_id, case=False, na=False)
        if sel_line != "Semua": mask &= df_logic['Line'].astype(str) == sel_line
        if sel_spv != "Semua": mask &= df_logic['SPV'] == sel_spv
        
        df_filt_calc = df_logic[mask.values]

        # Ringkasan Visual
        df_unique = df_filt_calc.drop_duplicates(subset=['ID NO'])
        total = len(df_unique)
        
        if total > 0:
            st.markdown("### 📊 Analisis Performa Grade")
            col_chart, col_metric = st.columns([1.5, 1])
            
            with col_chart:
                counts = df_unique['Final Grade'].value_counts().reset_index()
                counts.columns = ['Grade', 'Jumlah']
                
                # Warna Grade yang konsisten
                grade_colors = {'A':'#10B981','B':'#3B82F6','C':'#F59E0B','D':'#EF4444'}
                
                fig = px.pie(counts, values='Jumlah', names='Grade', hole=0.5)
                fig.update_traces(
                    marker=dict(colors=[grade_colors.get(x, '#636EFA') for x in counts['Grade']]),
                    textinfo='label+percent',
                    textfont_size=14
                )
                fig.update_layout(showlegend=True, height=400, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
                
            with col_metric:
                st.metric("Total Operator", f"{total} Org")
                st.write("---")
                m1, m2 = st.columns(2)
                for i, g in enumerate(['A', 'B', 'C', 'D']):
                    count = df_unique[df_unique['Final Grade'] == g].shape[0]
                    target = m1 if i % 2 == 0 else m2
                    target.metric(f"Grade {g}", f"{count} Org")

        # Tabel Detail
        st.divider()
        st.markdown("### 📑 Detail Data Operator")
        st.dataframe(df_display[mask.values].fillna(""), use_container_width=True, hide_index=True)
        
    else:
        st.error("Koneksi ke Google Sheets gagal atau data kosong.")
except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")
