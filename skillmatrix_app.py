import streamlit as st
import pandas as pd
import plotly.express as px

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="Skill Matrix Dashboard", 
    layout="wide", 
    page_icon="📊"
)

# --- CSS CUSTOM (TAMPILAN BERSIH TANPA LOGO) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    
    .custom-header {
        background-color: #cbd5e1; 
        padding: 20px 40px;
        border-radius: 15px;
        margin-bottom: 25px;
        border: 1px solid #94a3b8;
        text-align: center; /* Judul di tengah karena tidak ada logo */
    }
    
    .title-text { 
        color: #000000 !important; 
        font-size: 35px; 
        font-weight: 800; 
        margin: 0;
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
    </style>
    """, unsafe_allow_html=True)

# --- TAMPILKAN HEADER (JUDUL SAJA) ---
st.markdown(f'''
    <div class="custom-header">
        <div class="title-text">📊 Skill Matrix Dashboard</div>
    </div>
    ''', unsafe_allow_html=True)

# --- LOAD DATA ---
@st.cache_data
def load_data():
    try:
        # URL Spreadsheet kamu
        SHEET_URL = "https://docs.google.com/spreadsheets/d/1D2fWEf08Oks6XFvz5KBgHHUjxJiM38Z0/export?format=csv"
        df_raw = pd.read_csv(SHEET_URL)
        
        # Header ada di baris ke-1 (index 1)
        df_raw.columns = df_raw.iloc[1] 
        df_clean = df_raw.iloc[2:].reset_index(drop=True)
        
        # Pilih kolom yang diperlukan
        SELECTED_COLUMNS = ['SPV', 'Line', 'Name Opt', 'ID NO', 'Style', 'Process Part', 'Name Process (Bahasa)', 'Grade Process', 'Grade Countif', 'Grade Quality', 'Final Grade']
        df_final = df_clean[[c for c in SELECTED_COLUMNS if c in df_clean.columns]].copy()
        
        # Hapus baris kosong
        df_final = df_final.dropna(subset=['Name Process (Bahasa)'], how='all').reset_index(drop=True)
        return df_final
    except Exception as e:
        st.error(f"Gagal memuat data dari Google Sheets: {e}")
        return pd.DataFrame()

try:
    df_display = load_data()
    
    if not df_display.empty:
        # --- FILTER PENCARIAN ---
        with st.expander("🔍 Filter Pencarian Cepat", expanded=True):
            f1, f2, f3, f4 = st.columns(4)
            with f1: s_name = st.text_input("Nama Operator:")
            with f2: s_id = st.text_input("ID NO:")
            with f3:
                df_display['Line'] = pd.to_numeric(df_display['Line'].ffill(), errors='coerce')
                lines_list = sorted(df_display['Line'].dropna().unique().astype(int))
                sel_line = st.selectbox("Pilih Line:", ["Semua"] + [str(l) for l in lines_list])
            with f4:
                spvs = df_display['SPV'].ffill().unique()
                sel_spv = st.selectbox("Pilih SPV:", ["Semua"] + sorted([str(s) for s in spvs if pd.notna(s)]))

        # --- LOGIKA FILTERING ---
        df_logic = df_display.copy()
        # Isi data yang kosong akibat merge cells (Forward Fill)
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
            
            # --- ROW 1: METRICS & PIE CHART ---
            col_left, col_right = st.columns([1.5, 1])
            
            with col_left:
                counts = df_unique['Final Grade'].value_counts().reset_index()
                counts.columns = ['Grade', 'Jumlah']
                total_op = counts['Jumlah'].sum()
                counts['Label'] = counts.apply(lambda x: f"Grade {x['Grade']}: {x['Jumlah']} Org ({(x['Jumlah']/total_op*100):.1f}%)", axis=1)
                
                fig_pie = px.pie(counts, values='Jumlah', names='Grade', hole=0.5, 
                                color='Grade', color_discrete_map=color_map,
                                title="Distribusi Grade Operator")
                fig_pie.update_traces(textinfo='text', text=counts['Label'])
                fig_pie.update_layout(showlegend=False, height=450)
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with col_right:
                st.metric("Total Operator Terfilter", f"{len(df_unique)} Orang")
                st.write("---")
                m1, m2 = st.columns(2)
                grades = ['A', 'B', 'C', 'D']
                for i, g in enumerate(grades):
                    count = df_unique[df_unique['Final Grade'] == g].shape[0]
                    target = m1 if i % 2 == 0 else m2
                    target.metric(f"Grade {g}", f"{count} Org")

            # --- ROW 2: DETAIL TABEL ---
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f'<div class="section-title">📑 Detail Data ({len(df_filt_calc)} Proses)</div>', unsafe_allow_html=True)
            
            # Pewarnaan baris tabel berdasarkan Grade
            def color_grade(val):
                if val == 'A': return 'background-color: #dcfce7;'
                if val == 'B': return 'background-color: #dbeafe;'
                if val == 'C': return 'background-color: #ffedd5;'
                if val == 'D': return 'background-color: #fee2e2;'
                return ''

            df_final_view = df_filt_calc.fillna("")
            st.dataframe(
                df_final_view.style.applymap(color_grade, subset=['Final Grade']), 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.warning("Data tidak ditemukan untuk filter tersebut.")
            
    else:
        st.info("Menunggu data dari Google Sheets...")

except Exception as e:
    st.error(f"Terjadi kesalahan sistem: {e}")
