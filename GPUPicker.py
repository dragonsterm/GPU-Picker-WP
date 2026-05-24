import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="GPU Picker", layout="wide")

st.markdown("""
    <style>
        /* Warna background Tag */
        span[data-baseweb="tag"]:has(span[title="NVIDIA"]) { background-color: #76B900 !important; }
        span[data-baseweb="tag"]:has(span[title="AMD"]) { background-color: #ED1C24 !important; }
        span[data-baseweb="tag"]:has(span[title="Intel"]) { background-color: #0071C5 !important; }
        
        /* Merubah warna text dan icon silang (X) menjadi putih agar kontras */
        span[data-baseweb="tag"]:has(span[title="NVIDIA"]) *,
        span[data-baseweb="tag"]:has(span[title="AMD"]) *,
        span[data-baseweb="tag"]:has(span[title="Intel"]) * {
            color: white !important;
        }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    # Try both with and without Data/ subfolder
    for candidate in [os.path.join("Data", "dataset.csv"), "dataset.csv"]:
        if os.path.exists(candidate):
            return pd.read_csv(candidate)
    raise FileNotFoundError("dataset.csv not found")

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
    
    template = st.selectbox("Pilih Template Preferensi", ["Manual", "Gaming", "Price to Performance", "Content Creation"])
    
    # nilai pengaturan
    if template == "Gaming":
        t_price, t_mem, t_gclk, t_mclk, t_core, t_year, t_bench = 0.10, 0.15, 0.10, 0.10, 0.10, 0.15, 0.30
    elif template == "Price to Performance":
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
        st.markdown("#### Search")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            search_name = st.text_input("Search GPU Name", placeholder="example: RTX 4070")
        with col2:
            max_price = st.slider(
                "Price Range (IDR)", 
                min_value=int(df_all['Price'].min()), 
                max_value=int(df_all['Price'].max()), 
                value=int(df_all['Price'].max()),
                step=500_000
            )
        with col3:
            max_year = st.slider(
                "Release Year Range", 
                min_value=int(df_all['Release_Year'].min()), 
                max_value=int(df_all['Release_Year'].max()), 
                value=int(df_all['Release_Year'].max())
            )
        
        # opsi advanced options
        with st.expander("Advanced Options"):
            adv_col1, adv_col2 = st.columns([1, 2])
            
            with adv_col1:
                manufacturer_list = df_all['Manufacturer'].unique().tolist()
                selected_manufacturers = st.multiselect("Chose Manufacturers", manufacturer_list, default=manufacturer_list)
                
            with adv_col2:
                spec_col1, spec_col2, spec_col3 = st.columns(3)
                with spec_col1:
                    min_mem = st.slider(
                        "Minimum Memory (GB)", 
                        min_value=int(df_all['Memory_GB'].min()), 
                        max_value=int(df_all['Memory_GB'].max()), 
                        value=int(df_all['Memory_GB'].min())
                    )
                with spec_col2:
                    min_clock = st.slider(
                        "Minimum GPU Clock (MHz)", 
                        min_value=int(df_all['GPU_Clock_MHz'].min()), 
                        max_value=int(df_all['GPU_Clock_MHz'].max()), 
                        value=int(df_all['GPU_Clock_MHz'].min())
                    )
                with spec_col3:
                    min_bench = st.slider(
                        "Minimum Score Benchmark", 
                        min_value=float(df_all['Benchmark_Score'].min()), 
                        max_value=float(df_all['Benchmark_Score'].max()), 
                        value=float(df_all['Benchmark_Score'].min())
                    )
        
    # Filter pencarian
    df_display = df_all[
        (df_all['Name'].str.contains(search_name, case=False, na=False)) &
        (df_all['Manufacturer'].isin(selected_manufacturers)) &
        (df_all['Price'] <= max_price) &
        (df_all['Release_Year'] <= max_year) &
        (df_all['Memory_GB'] >= min_mem) &
        (df_all['GPU_Clock_MHz'] >= min_clock) &
        (df_all['Benchmark_Score'] >= min_bench)
    ]
    
    st.markdown(f"Displaying **{len(df_display)}** of **{len(df_all)}** Total GPU inside the dataset:")
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

    # Dataframe
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
        st.latex(r"""
        r_{ij} = 
        \begin{cases} 
        \frac{x_{ij}}{\max_i x_{ij}} & \text{jika } j \text{ adalah atribut benefit (keuntungan)} \\ 
        \frac{\min_i x_{ij}}{x_{ij}} & \text{jika } j \text{ adalah atribut cost (biaya)} 
        \end{cases}
        """)
        st.dataframe(pd.DataFrame(R, columns=kriteria_names, index=alternatif_names).style.format("{:.4f}"), use_container_width=True)
        
        st.subheader("4. Bobot (w)")
        st.dataframe(pd.DataFrame([w], columns=kriteria_names, index=["Bobot W (Ternormalisasi)"]).style.format("{:.4f}"), use_container_width=True)
        
        st.subheader("5. Hasil Perangkingan Akhir (V)")
        st.latex(r"V_i = \sum_{j=1}^{n} w_j r_{ij}")
        df_v = pd.DataFrame(V, columns=["Nilai V"], index=alternatif_names).sort_values(by="Nilai V", ascending=False)
        st.dataframe(df_v.style.format("{:.5f}"), use_container_width=True)

    # Page 3 hasil dan rekomendasi
    elif page == "Page 3 - Result & Recommendation":
        import base64

        def load_asset_b64(paths, mime):
            for p in paths:
                if os.path.exists(p):
                    with open(p, 'rb') as f:
                        return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"
            return None

        gif_b64  = load_asset_b64(
            [os.path.join("Asset", "ubmlogo-60-loop.gif"), "ubmlogo-60-loop.gif",
             "/mnt/user-data/uploads/ubmlogo-60-loop.gif"], "image/gif")
        logo_b64 = load_asset_b64(
            [os.path.join("Asset", "UserBenchmarkLogo.png"), "UserBenchmarkLogo.png",
             "/mnt/user-data/uploads/UserBenchmarkLogo.png"], "image/png")

        # Benchmark csv
        @st.cache_data
        def load_userbenchmark():
            for candidate in [os.path.join("Data", "Used Data", "GPU_UserBenchmarks.csv"), os.path.join("Data", "GPU_UserBenchmarks.csv"), "GPU_UserBenchmarks.csv"]:
                if os.path.exists(candidate):
                    ub_path = candidate
                    break
            else:
                return pd.DataFrame()
            try:
                ub = pd.read_csv(ub_path)
                ub = ub[ub['URL'].notna() & (ub['URL'].str.strip() != '')]
                return ub
            except Exception:
                return pd.DataFrame()

        def find_userbenchmark_url(gpu_name, ub_df):
            if ub_df.empty:
                return None, None, None
            name_lower = str(gpu_name).lower()
            clean = name_lower.replace('geforce ', '').replace('radeon ', '').replace('intel arc ', 'arc ')
            best_score = 0
            best_row = None
            for _, row in ub_df.iterrows():
                model = str(row.get('Model', '')).lower()
                tokens = [t for t in clean.split() if len(t) > 1]
                score = sum(1 for t in tokens if t in model)
                if score > best_score:
                    best_score = score
                    best_row = row
            if best_row is not None and best_score >= 2:
                return best_row.get('Rank'), best_row.get('Benchmark'), best_row.get('URL')
            return None, None, None

        ub_df    = load_userbenchmark()
        best_gpu = df_result.iloc[0]

        mfg = best_gpu['Manufacturer']
        if mfg == 'NVIDIA':   mfg_color, mfg_bg = "#76B900", "#76B90018"
        elif mfg == 'AMD':    mfg_color, mfg_bg = "#ED1C24", "#ED1C2418"
        elif mfg == 'Intel':  mfg_color, mfg_bg = "#0071C5", "#0071C518"
        else:                 mfg_color, mfg_bg = "#888888", "#88888818"

        ub_rank, ub_bench, ub_url = find_userbenchmark_url(best_gpu['Name'], ub_df)

        # css
        st.markdown(f"""
        <style>
            /* Use Streamlit's own font stack — no external imports */
            .p3-root {{ font-family: "Source Sans Pro", sans-serif; }}

            .p3-header {{
                font-size: 1.75rem;
                font-weight: 700;
                color: #fafafa;
                margin-bottom: 0.15rem;
            }}
            .p3-sub {{
                font-size: 0.82rem;
                color: #888;
                margin-bottom: 1.4rem;
            }}

            /* Winner card */
            .winner-card {{
                background: #161616;
                border: 1px solid #272727;
                border-left: 4px solid {mfg_color};
                border-radius: 10px;
                padding: 1.5rem 1.8rem;
                margin-bottom: 0.8rem;
            }}
            .gpu-name {{
                font-size: 1.6rem;
                font-weight: 700;
                color: #fff;
                margin-bottom: 0.25rem;
            }}
            .mfg-badge {{
                display: inline-block;
                background: {mfg_color};
                color: #fff;
                font-size: 0.7rem;
                font-weight: 700;
                letter-spacing: 0.12em;
                padding: 2px 10px;
                border-radius: 3px;
                margin-bottom: 1.1rem;
                text-transform: uppercase;
                box-shadow: none !important;
                text-shadow: none !important;
            }}
            .spec-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(185px, 1fr));
                gap: 0.6rem;
            }}
            .spec-item {{
                background: #1d1d1d;
                border: 1px solid #2a2a2a;
                border-radius: 7px;
                padding: 0.6rem 0.85rem;
            }}
            .spec-label {{
                font-size: 0.65rem;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #666;
                margin-bottom: 0.15rem;
            }}
            .spec-value {{
                font-size: 0.95rem;
                font-weight: 600;
                color: #e0e0e0;
            }}

            /* SAW score */
            .score-box {{
                background: {mfg_bg};
                border: 1px solid {mfg_color}44;
                border-radius: 9px;
                padding: 0.9rem 1rem;
                text-align: center;
                margin-top: 0.75rem;
            }}
            .score-lbl {{ font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.1em; color: #777; margin-bottom: 0.2rem; }}
            .score-val {{ font-size: 2.2rem; font-weight: 700; color: {mfg_color}; line-height: 1; }}

            /* UserBenchmark badge — mimics official style */
            .ub-badge {{
                background: #111;
                border: 1px solid #2a2a2a;
                border-radius: 9px;
                padding: 0.85rem 1rem;
                margin-top: 0.75rem;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 0.3rem;
            }}
            .ub-row {{
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            .ub-site {{
                font-size: 1.05rem;
                font-weight: 700;
                color: #fff;
                text-decoration: none;
            }}
            .ub-site:hover {{
                text-decoration: underline;
            }}
            .ub-stat {{
                font-size: 0.78rem;
                color: #888;
            }}
            .ub-stat strong {{ color: #bbb; }}

            /* Alt section */
            .alt-section-title {{
                font-size: 0.75rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.12em;
                color: #888;
                margin: 1.6rem 0 0.7rem 0;
                padding-bottom: 0.4rem;
                border-bottom: 1px solid #222;
            }}
            .alt-card {{
                background: #141414;
                border: 1px solid #222;
                border-radius: 9px;
                padding: 0.75rem 1rem;
                display: flex;
                align-items: center;
                gap: 0.9rem;
                margin-bottom: 0.55rem;
            }}
            .alt-card:hover {{ border-color: #383838; }}
            .alt-rank {{
                font-size: 1.3rem;
                font-weight: 700;
                color: #3a3a3a;
                min-width: 30px;
                text-align: center;
            }}
            .alt-gpu-img {{
                width: 72px;
                height: 46px;
                object-fit: contain;
                border-radius: 4px;
                background: #1a1a1a;
                flex-shrink: 0;
            }}
            .alt-gpu-img-placeholder {{
                width: 72px;
                height: 46px;
                background: #1e1e1e;
                border-radius: 4px;
                flex-shrink: 0;
            }}
            .alt-name {{ font-size: 0.92rem; font-weight: 600; color: #ddd; }}
            .alt-meta {{ font-size: 0.72rem; color: #666; margin-top: 2px; }}
            .alt-ub-gif {{
                width: 36px;
                height: 36px;
                object-fit: contain;
                flex-shrink: 0;
                cursor: pointer;
                opacity: 0.85;
                transition: opacity 0.2s;
            }}
            .alt-ub-gif:hover {{ opacity: 1; }}
            .alt-score {{ font-size: 0.9rem; font-weight: 700; color: #aaa; white-space: nowrap; }}
            .alt-price {{ font-size: 0.75rem; color: #999; white-space: nowrap; }}
            .alt-bench {{ font-size: 0.72rem; color: #666; }}
        </style>
        <div class="p3-root">
        <div class="p3-header">GPU Recommendation</div>
        <div class="p3-sub">GPU yang paling sesuai berdasarkan Max Budget</div>
        </div>
        """, unsafe_allow_html=True)

        img_col, info_col = st.columns([1, 2], gap="large")

        with img_col:
            if pd.notna(best_gpu.get('Image_URL')):
                st.image(best_gpu['Image_URL'], use_container_width=True)

            # score box
            st.markdown(f"""
            <div class="score-box">
                <div class="score-lbl">SAW Score (Nilai V)</div>
                <div class="score-val">{best_gpu['Nilai V']:.4f}</div>
            </div>
            """, unsafe_allow_html=True)

            # UserBenchmark container
            if ub_url:
                rank_str  = f"GPU Rank <strong>#{int(ub_rank)}</strong>" if ub_rank and not pd.isna(ub_rank) else ""
                bench_str = f"Average Benchmark: <strong>{float(ub_bench):.1f}%</strong>" if ub_bench and not pd.isna(ub_bench) else ""
                stat_line = " &nbsp;&bull;&nbsp; ".join(filter(None, [rank_str, bench_str]))
                gif_img   = f'<img src="{gif_b64}" width="44" height="44" style="object-fit:contain;">' if gif_b64 else ""
                logo_img  = f'<a class="ub-site" href="{ub_url}" target="_blank">UserBenchmark.com</a>'
                st.markdown(f"""
                <div class="ub-badge">
                    <div class="ub-row">
                        {gif_img}
                        {logo_img}
                    </div>
                    <div class="ub-stat">{stat_line}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                gif_img  = f'<img src="{gif_b64}" width="36" height="36" style="object-fit:contain; opacity:0.8;">' if gif_b64 else ""
                logo_img = '<span class="ub-site" style="opacity:0.8;">UserBenchmark.com</span>'
                st.markdown(f"""
                <div class="ub-badge">
                    <div class="ub-row">{gif_img} {logo_img}</div>
                    <div class="ub-stat" style="color:#aaa;">No matching entry found</div>
                </div>
                """, unsafe_allow_html=True)

        with info_col:
            st.markdown(f"""
            <div class="winner-card">
                <div class="gpu-name">{best_gpu['Name']}</div>
                <div class="mfg-badge">{mfg}</div>
                <div class="spec-grid">
                    <div class="spec-item">
                        <div class="spec-label">Price</div>
                        <div class="spec-value">Rp {int(best_gpu['Price']):,}</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">Benchmark Score</div>
                        <div class="spec-value">{best_gpu['Benchmark']}</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">Release Date</div>
                        <div class="spec-value">{best_gpu['Release Date']}</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">Memory</div>
                        <div class="spec-value">{best_gpu['Memory']}</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">GPU Clock</div>
                        <div class="spec-value">{best_gpu['GPU Clock']}</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">Cores / TMUs / ROPs</div>
                        <div class="spec-value">{best_gpu['Cores / TMUs / ROPs']}</div>
                    </div>
                    <div class="spec-item">
                        <div class="spec-label">Bus Interface</div>
                        <div class="spec-value">{best_gpu['Bus']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Alternative 
        st.markdown('<div class="alt-section-title">Alternative Options &mdash; Rank 2 to 5</div>', unsafe_allow_html=True)

        for _, row in df_result.iloc[1:5].iterrows():
            alt_mfg = row['Manufacturer']
            if alt_mfg == 'NVIDIA':  alt_color = "#76B900"
            elif alt_mfg == 'AMD':   alt_color = "#ED1C24"
            elif alt_mfg == 'Intel': alt_color = "#0071C5"
            else:                    alt_color = "#888"

            _, _, alt_ub_url = find_userbenchmark_url(row['Name'], ub_df)

            # Gpu picture from dataset
            img_url = row.get('Image_URL', '')
            if pd.notna(img_url) and str(img_url).strip():
                gpu_img_html = f'<img src="{img_url}" class="alt-gpu-img" />'
            else:
                gpu_img_html = '<div class="alt-gpu-img-placeholder"></div>'
                
            if alt_ub_url and logo_b64:
                ub_logo_html = f'<a href="{alt_ub_url}" target="_blank" style="margin-left: 6px;"><img src="{logo_b64}" height="14" style="object-fit:contain; vertical-align:middle;" title="View on UserBenchmark" /></a>'
            elif alt_ub_url:
                ub_logo_html = f'<a href="{alt_ub_url}" target="_blank" style="margin-left: 6px; color:#fff; font-size:0.72rem; text-decoration:none;">[UB]</a>'
            else:
                ub_logo_html = ''

            st.markdown(f"""
            <div class="alt-card">
                <div class="alt-rank">#{int(row['Ranking'])}</div>
                {gpu_img_html}
                <div style="min-width:46px;">
                    <span style="background:{alt_color}; color:#fff; font-size:0.6rem; font-weight:700; letter-spacing:0.1em; padding:2px 7px; border-radius:3px; text-transform:uppercase; box-shadow: none !important; text-shadow: none !important;">{alt_mfg}</span>
                </div>
                <div style="flex:1; min-width:0;">
                    <div class="alt-name">{row['Name']}{ub_logo_html}</div>
                    <div class="alt-meta">{row['Memory']} &nbsp;&bull;&nbsp; {int(row['Release_Year'])}</div>
                </div>
                <div style="text-align:right; flex-shrink:0;">
                    <div class="alt-score">V: {row['Nilai V']:.4f}</div>
                    <div class="alt-price">Rp {int(row['Average Price (IDR)']):,}</div>
                    <div class="alt-bench">Score: {row['Benchmark']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)