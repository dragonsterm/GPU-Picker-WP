import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="GPU Picker", layout="wide")

@st.cache_data
def load_data():
    file_path = os.path.join("Data", "dataset.csv")
    df = pd.read_csv(file_path)
    return df

def get_manufacturer(name):
    name_lower = str(name).lower()
    if 'radeon' in name_lower or 'rx ' in name_lower:
        return 'AMD'
    elif 'geforce' in name_lower or 'rtx' in name_lower or 'gtx' in name_lower or 'gt ' in name_lower:
        return 'NVIDIA'
    elif 'arc' in name_lower or 'intel' in name_lower:
        return 'Intel'
    return 'Other'

def preprocess_data(df):
    df_eval = df.copy()
    df_eval['Memory_GB'] = df_eval['Memory'].str.extract(r'(\d+)').astype(float)
    df_eval['GPU_Clock_MHz'] = df_eval['GPU Clock'].str.extract(r'(\d+)').astype(float)
    df_eval['Memory_Clock_MHz'] = df_eval['Memory Clock'].str.extract(r'(\d+)').astype(float)
    df_eval['Cores'] = df_eval['Cores / TMUs / ROPs'].str.extract(r'^(\d+)').astype(float)
    df_eval['Price'] = df_eval['Average Price (IDR)'].astype(float)
    df_eval['Release_Year'] = df_eval['Release Date'].str.extract(r'(\d{4})').astype(float)
    df_eval['Benchmark_Score'] = df_eval['Benchmark'].astype(float)
    
    df_eval['Manufacturer'] = df_eval['Name'].apply(get_manufacturer)
    
    df_eval = df_eval.dropna(subset=['Memory_GB', 'GPU_Clock_MHz', 'Memory_Clock_MHz', 'Cores', 'Price', 'Release_Year', 'Benchmark_Score'])
    return df_eval

df_raw = load_data()
df_all = preprocess_data(df_raw)

# sidebar
with st.sidebar:
    st.header("GPU Picker")
    page = st.selectbox("Navigations", [
        "Page 1 - Main Page", 
        "Page 2 - SAW", 
        "Page 3 - Result & Recommendation"
    ])
    
    st.divider()
    st.markdown("### Pengaturan SPK")
    
    # Budget untuk spk
    max_budget = st.number_input(
        "Max Budget (IDR)", 
        min_value=1_000_000, 
        max_value=100_000_000, 
        value=15_000_000, 
        step=500_000,
        help="Hanya GPU di bawah budget ini yang akan dievaluasi oleh sistem rekomendasi."
    )
    
    template = st.selectbox("Pilih Template Preferensi", ["Manual", "Gaming", "Budget (Price to Performance)", "Content Creation"])
    
    # nilai pengaturan
    if template == "Gaming":
        t_price, t_mem, t_gclk, t_mclk, t_core, t_year, t_bench = 0.10, 0.15, 0.10, 0.10, 0.10, 0.15, 0.30
    elif template == "Budget (Price to Performance)":
        t_price, t_mem, t_gclk, t_mclk, t_core, t_year, t_bench = 0.25, 0.05, 0.05, 0.05, 0.05, 0.20, 0.35
    elif template == "Content Creation":
        t_price, t_mem, t_gclk, t_mclk, t_core, t_year, t_bench = 0.10, 0.25, 0.05, 0.05, 0.20, 0.15, 0.20
    else:
        t_price, t_mem, t_gclk, t_mclk, t_core, t_year, t_bench = 0.15, 0.10, 0.10, 0.10, 0.10, 0.15, 0.30
        
    st.markdown("#### Bobot Kriteria")
    d_disable = template != "Manual"
    
    bar_price = st.slider("Harga (Cost)", min_value=0.01, max_value=1.00, value=t_price, step=0.01, disabled=d_disable)
    bar_mem = st.slider("Memory GB (Benefit)", min_value=0.01, max_value=1.00, value=t_mem, step=0.01, disabled=d_disable)
    bar_gclk = st.slider("GPU Clock (Benefit)", min_value=0.01, max_value=1.00, value=t_gclk, step=0.01, disabled=d_disable)
    bar_mclk = st.slider("Memory Clock (Benefit)", min_value=0.01, max_value=1.00, value=t_mclk, step=0.01, disabled=d_disable)
    bar_core = st.slider("Cores (Benefit)", min_value=0.01, max_value=1.00, value=t_core, step=0.01, disabled=d_disable)
    bar_year = st.slider("Tahun Rilis (Benefit)", min_value=0.01, max_value=1.00, value=t_year, step=0.01, disabled=d_disable)
    bar_bench = st.slider("Benchmark (Benefit)", min_value=0.01, max_value=1.00, value=t_bench, step=0.01, disabled=d_disable)
    
    # Menghitung bobot W
    bobot_awal = np.array([bar_price, bar_mem, bar_gclk, bar_mclk, bar_core, bar_year, bar_bench])
    w = bobot_awal / np.sum(bobot_awal)
    
# Page 1
if page == "Page 1 - Main Page":
    st.title("Explore GPU Database")
    st.write("Telusuri seluruh database GPU secara bebas menggunakan fungsionalitas pencarian di bawah ini.")
    
    # Search Container 
    with st.container(border=True):
        st.markdown("#### Filter Pencarian")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            search_name = st.text_input("Cari Nama GPU", placeholder="contoh: RTX 4070")
        with col2:
            max_price = st.slider(
                "Maksimal Harga (IDR)", 
                min_value=int(df_all['Price'].min()), 
                max_value=int(df_all['Price'].max()), 
                value=int(df_all['Price'].max()),
                step=500_000
            )
        with col3:
            min_year = st.slider(
                "Minimal Tahun Rilis", 
                min_value=int(df_all['Release_Year'].min()), 
                max_value=int(df_all['Release_Year'].max()), 
                value=int(df_all['Release_Year'].min())
            )
        
        # opsi advanced options
        with st.expander("Advanced Options"):
            adv_col1, adv_col2 = st.columns([1, 2])
            
            with adv_col1:
                manufacturer_list = df_all['Manufacturer'].unique().tolist()
                selected_manufacturers = st.multiselect("Pilih Produsen", manufacturer_list, default=manufacturer_list)
                
            with adv_col2:
                spec_col1, spec_col2, spec_col3 = st.columns(3)
                with spec_col1:
                    min_mem = st.slider(
                        "Minimal Memory (GB)", 
                        min_value=int(df_all['Memory_GB'].min()), 
                        max_value=int(df_all['Memory_GB'].max()), 
                        value=int(df_all['Memory_GB'].min())
                    )
                with spec_col2:
                    min_clock = st.slider(
                        "Minimal GPU Clock (MHz)", 
                        min_value=int(df_all['GPU_Clock_MHz'].min()), 
                        max_value=int(df_all['GPU_Clock_MHz'].max()), 
                        value=int(df_all['GPU_Clock_MHz'].min())
                    )
                with spec_col3:
                    min_bench = st.slider(
                        "Minimal Score Benchmark", 
                        min_value=float(df_all['Benchmark_Score'].min()), 
                        max_value=float(df_all['Benchmark_Score'].max()), 
                        value=float(df_all['Benchmark_Score'].min())
                    )
        
    # Filter pencarian
    df_display = df_all[
        (df_all['Name'].str.contains(search_name, case=False, na=False)) &
        (df_all['Manufacturer'].isin(selected_manufacturers)) &
        (df_all['Price'] <= max_price) &
        (df_all['Release_Year'] >= min_year) &
        (df_all['Memory_GB'] >= min_mem) &
        (df_all['GPU_Clock_MHz'] >= min_clock) &
        (df_all['Benchmark_Score'] >= min_bench)
    ]
    
    st.markdown(f"Menampilkan **{len(df_display)}** dari total **{len(df_all)}** GPU dalam dataset:")
    st.data_editor(
        df_display[['Name', 'Image_URL', 'Release Date', 'Manufacturer', 'Bus', 'Memory', 'GPU Clock', 'Memory Clock', 'Cores / TMUs / ROPs', 'Benchmark', 'Average Price (IDR)']],
        column_config={
            "Image_URL": st.column_config.ImageColumn("Visual", help="Gambar GPU"),
            "Average Price (IDR)": st.column_config.NumberColumn("Harga (IDR)", format="Rp %d"),
            "Benchmark": st.column_config.NumberColumn("Score", format="%.1f")
        },
        use_container_width=True,
        hide_index=True,
        disabled=True
    )

# page 2 dab 3 - spk saw
else:
    # Filter Dataset untuk SPK berdasar max budget dan bechmark score
    df_eval = df_all[(df_all['Price'] <= max_budget) & (df_all['Benchmark_Score'] > 0)].copy()

    if df_eval.empty:
        st.error(f"Tidak ada GPU valid yang ditemukan di bawah budget Rp. {max_budget:,}. Silakan tambah Max Budget pada Sidebar.")
        st.stop()

    k = np.array([0, 1, 1, 1, 1, 1, 1]) 
    x = df_eval[['Price', 'Memory_GB', 'GPU_Clock_MHz', 'Memory_Clock_MHz', 'Cores', 'Release_Year', 'Benchmark_Score']].values
    kriteria_names = ["Price (IDR)", "Memory (GB)", "GPU Clock (MHz)", "Memory Clock (MHz)", "Cores", "Tahun Rilis", "Benchmark Score"]
    alternatif_names = df_eval['Name'].values

    m, n = x.shape
    R = np.zeros((m, n)) 
    for j in range(n):
        if k[j] == 1: 
            R[:, j] = x[:, j] / np.max(x[:, j])
        else: 
            R[:, j] = np.min(x[:, j]) / x[:, j]

    V = np.sum(w * R, axis=1)

    # DataFrame
    df_result = df_eval.copy()
    df_result['Nilai V'] = V
    df_result['Ranking'] = df_result['Nilai V'].rank(ascending=False).astype(int)
    df_result = df_result.sort_values("Ranking").reset_index(drop=True)

    # Page 2 Perhitungan SAW
    if page == "Page 2 - SAW":
        st.title("Metode Simple Additive Weighting (SAW)")
        st.write("Menampilkan matriks normalisasi SAW hanya untuk GPU yang lolos validasi budget.")
        
        st.subheader("1. Inisialisasi Matriks Awal (x)")
        st.dataframe(pd.DataFrame(x, columns=kriteria_names, index=alternatif_names), use_container_width=True)
        
        st.subheader("2. Matriks Keputusan Berdasarkan Atribut (k)")
        st.write("Keterangan: Harga di-set 0 (Cost), Selain itu (Tahun Rilis, Core, Benchmark) di-set 1 (Benefit)")
        df_k = pd.DataFrame([k], columns=kriteria_names, index=["Atribut (0=Biaya, 1=Keuntungan)"])
        st.dataframe(df_k, use_container_width=True)
        
        st.subheader("3. Normalisasi Matriks (R)")
        st.dataframe(pd.DataFrame(R, columns=kriteria_names, index=alternatif_names).style.format("{:.4f}"), use_container_width=True)
        
        st.subheader("4. Bobot (w)")
        st.dataframe(pd.DataFrame([w], columns=kriteria_names, index=["Bobot W (Ternormalisasi)"]).style.format("{:.4f}"), use_container_width=True)
        
        st.subheader("5. Hasil Perangkingan Akhir (V)")
        df_v = pd.DataFrame(V, columns=["Nilai V"], index=alternatif_names).sort_values(by="Nilai V", ascending=False)
        st.dataframe(df_v.style.format("{:.5f}"), use_container_width=True)

    # Page 3 hasil dan rekomendasi
    elif page == "Page 3 - Result & Recommendation":
        st.title("Rekomendasi GPU Terbaik")
        
        best_gpu = df_result.iloc[0]
        
        st.success(f"Berikut adalah pilihan terbaik di bawah batas budget yang Anda tetapkan: **{best_gpu['Name']}**")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            if pd.notna(best_gpu['Image_URL']):
                st.image(best_gpu['Image_URL'], use_column_width=True)
            st.metric(label="Total Skor (Nilai V)", value=f"{best_gpu['Nilai V']:.4f}")
            
        with col2:
            st.subheader("Spesifikasi Utama:")
            st.write(f"- Price: Rp. {int(best_gpu['Price']):,}")
            st.write(f"- Benchmark Score: {best_gpu['Benchmark']}")
            st.write(f"- Release Year: {int(best_gpu['Release_Year'])} ({best_gpu['Release Date']})")
            st.write(f"- Manufacturer: {best_gpu['Manufacturer']}")
            st.write(f"- Memory: {best_gpu['Memory']}")
            st.write(f"- GPU Clock Speed: {best_gpu['GPU Clock']}")
            st.write(f"- Cores / TMUs / ROPs: {best_gpu['Cores / TMUs / ROPs']}")
            st.write(f"- Bus: {best_gpu['Bus']}")
        
        st.divider()
        st.subheader("Pilihan Alternatif (Ranking 2 - 5)")
        st.write("Alternatif terbaik selanjutnya untuk budget Anda:")
        
        alternatives = df_result.iloc[1:5][['Ranking', 'Name', 'Image_URL', 'Release_Year', 'Memory', 'Cores / TMUs / ROPs', 'Benchmark', 'Average Price (IDR)', 'Nilai V']]
        st.data_editor(
            alternatives,
            column_config={
                "Image_URL": st.column_config.ImageColumn("Visual"),
                "Release_Year": st.column_config.NumberColumn("Tahun", format="%d"),
                "Benchmark": st.column_config.NumberColumn("Score", format="%.1f"),
                "Average Price (IDR)": st.column_config.NumberColumn("Harga", format="Rp %d")
            },
            use_container_width=True,
            hide_index=True,
            disabled=True
        )