import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import base64

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="Skill Matrix Dashboard", 
    layout="wide", 
    page_icon="📊"
)

# --- FUNGSI LOAD LOGO (DIPERBAIKI) ---
@st.cache_data
def get_base64_logo(url):
    try:
        # Menangani link drive agar menjadi direct download link
        if 'drive.google.com' in url:
            file_id = url.split('/')[-2]
            direct_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        else:
            direct_url = url
            
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(direct_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode()
        return None
    except Exception:
        return None

# --- CSS CUSTOM (DIOPTIMALKAN UNTUK LOGO BESAR) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    
    /* Header Header Baru */
    .custom-header {
        background-color: #cbd5e1; 
        padding: 20px 40px;
        border-radius: 15px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 25px;
        border: 1px solid #94a3b8;
    }
    
    .title-text { 
        color: #000000 !important; 
        font-size: 32px; 
        font-weight: 800; 
        margin: 0; 
    }

    /* Ukuran Logo Diperbesar */
    .header-logo {
        height: 150px; /* Ukuran sebelumnya 45px, sekarang 80px */
        width: auto;
        object-fit: contain;
    }

    .section-title {
        background-color: #e2e8f0; 
        color: #000000;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 700;
        margin-bottom: 15px;
        border-left: 5px solid #3b82f6;
    }

    /* Standar Matrix sewa mesin01 */
    div[data-testid="stMetric"] {
        background-color: #f8fafc !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        padding: 15px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Style Tabel agar Rata Kiri & Bersih */
    [data-testid="stDataFrame"] td {
        text-align: left !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOAD DATA ---
@st.cache_data
def load_data():
    try:
        SHEET_URL = "https://docs.google.com/spreadsheets/d/1D2fWEf08Oks6XFvz5KBgHHUjxJiM38Z0/export?format=csv"
        df_raw = pd.read_csv(SHEET_URL)
        df_raw.columns = df_raw.iloc[1] 
        df_clean = df_raw.iloc[2:].reset_index(drop=True)
        SELECTED_COLUMNS = ['SPV', 'Line', 'Name Opt', 'ID NO', 'Style', 'Process Part', 'Name Process (Bahasa)', 'Grade Process', 'Grade Countif', 'Grade Quality', 'Final Grade']
        df_final = df_clean[[c for c in SELECTED_COLUMNS if c in df_clean.columns]].copy()
        df_final = df_final.dropna(subset=['Name Process (Bahasa)'], how='all').reset_index(drop=True)
        return df_final
    except Exception:
        return pd.DataFrame()

# --- RENDER HEADER & LOGO ---
logo_url = "https://drive.google.com/file/d/1oS09AXFGtqWtB7b_llMa4uWFjoK8qwzG/view?usp=sharing"
logo_data = get_base64_logo(logo_url)

logo_html = f'<img src="data:image/png;base64,{logo_data}" class="header-logo">' if logo_data else ""
st.markdown(f'''
    <div class="custom-header">
        <h1 class="title-text">Skill Matrix Dashboard</h1>
        {logo_html}
    </div>
    ''', unsafe_allow_html=True)

try:
    df_display = load_data()
    if not df_display.empty:
        # --- FILTER SECTION ---
        with st.expander("🔍 Filter Pencarian Cepat", expanded=True):
            f1, f2, f3, f4 = st.columns(4)
            with f1: s_name = st.text_input("Nama:")
            with f2: s_id = st.text_input("ID NO:")
            with f3:
                df_display['Line'] = pd.to_numeric(df_display['Line'].ffill(), errors='coerce')
                lines_list = sorted(df_display['Line'].dropna().unique().astype(int))
                sel_line = st.selectbox("Line:", ["Semua"] + [str(l) for l in lines_list])
            with f4:
                spvs = df_display['SPV'].ffill().unique()
                sel_spv = st.selectbox("SPV:", ["Semua"] + sorted([str(s) for s in spvs if pd.notna(s)]))

        # --- LOGIC FILTER ---
        df_logic = df_display.copy()
        df_logic[['SPV', 'Line', 'Name Opt', 'ID NO', 'Final Grade']] = df_logic[['SPV', 'Line', 'Name Opt', 'ID NO', 'Final Grade']].ffill()
        
        mask = pd.Series([True] * len(df_logic))
        if s_name: mask &= df_logic['Name Opt'].str.contains(s_name, case=False, na=False)
        if s_id: mask &= df_logic['ID NO'].astype(str).str.contains(s_id, case=False, na=False)
        if sel_line != "Semua": mask &= df_logic['Line'].astype(str) == str(sel_line)
        if sel_spv != "Semua": mask &= df_logic['SPV'] == sel_spv
        
        df_filt_calc = df_logic[mask.values]
        df_unique = df_filt_calc.drop_duplicates(subset=['ID NO'])
        color_map = {'A':'#10b981','B':'#3b82f6','C':'#f59e0b','D':'#ef4444'}

        if not df_unique.empty:
            st.markdown('<div class="section-title">📊 Analisis Performa</div>', unsafe_allow_html=True)
            
            # --- ROW 1: PIE & METRICS ---
            col_left, col_right = st.columns([1.5, 1])
            with col_left:
                counts = df_unique['Final Grade'].value_counts().reset_index()
                counts.columns = ['Grade', 'Jumlah']
                fig_pie = px.pie(counts, values='Jumlah', names='Grade', hole=0.5, 
                                color='Grade', color_discrete_map=color_map)
                fig_pie.update_traces(textinfo='label+percent+value', textposition='outside')
                fig_pie.update_layout(showlegend=True, height=400, margin=dict(t=20, b=20, l=0, r=0))
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with col_right:
                st.metric("Total Operator", f"{len(df_unique)} Orang")
                st.write("---")
                m_col1, m_col2 = st.columns(2)
                for i, g in enumerate(['A', 'B', 'C', 'D']):
                    count = df_unique[df_unique['Final Grade'] == g].shape[0]
                    target_col = m_col1 if i % 2 == 0 else m_col2
                    target_col.metric(f"Grade {g}", f"{count} Org")

            # --- ROW 2: BAR CHART ---
            st.markdown("<br>", unsafe_allow_html=True)
            line_data = df_unique.groupby(['Line', 'Final Grade']).size().reset_index(name='Count')
            line_total = df_unique.groupby('Line').size().reset_index(name='Total')
            line_data = line_data.merge(line_total, on='Line')
            line_data = line_data.sort_values('Line')
            line_data['Line_Label'] = "Line " + line_data['Line'].astype(int).astype(str)

            fig_bar = px.bar(line_data, x='Line_Label', y='Count', color='Final Grade', 
                            color_discrete_map=color_map, barmode='stack',
                            category_orders={"Line_Label": ["Line " + str(i) for i in lines_list]})
            
            fig_bar.update_layout(height=450, xaxis_title="Area Line", yaxis_title="Jumlah Operator")
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- ROW 3: DETAIL DATA (RATA KIRI) ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">📑 Detail Data ({len(df_filt_calc)} Baris)</div>', unsafe_allow_html=True)
        
        def color_grade(val):
            if val == 'A': return 'background-color: #dcfce7;'
            if val == 'B': return 'background-color: #dbeafe;'
            if val == 'C': return 'background-color: #ffedd5;'
            if val == 'D': return 'background-color: #fee2e2;'
            return ''

        # Menampilkan tabel dengan gaya sewa mesin01
        df_final_view = df_display[mask.values].fillna("")
        styled_df = df_final_view.style.applymap(color_grade, subset=['Final Grade'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
    else:
        st.info("Data tidak ditemukan. Silakan sesuaikan filter.")
        
except Exception as e:
    st.error(f"Terjadi Kesalahan: {e}")

