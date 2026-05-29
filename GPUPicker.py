import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="GPU Picker", layout="wide")

# Load css
def load_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        st.warning(f"CSS file not found: {file_name}")
    
load_css(os.path.join("style", "base.css"))

@st.cache_data
def load_data():
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
    
    all_criteria = [
        "Harga (Cost)", "Memory GB (Benefit)", "GPU Clock (Benefit)", 
        "Memory Clock (Benefit)", "Cores (Benefit)", "Tahun Rilis (Benefit)", "Benchmark (Benefit)"
    ]
    
    default_4_criteria = ["Harga (Cost)", "Memory GB (Benefit)", "Tahun Rilis (Benefit)", "Benchmark (Benefit)"]
    
    
    # nilai pengaturan
    if template == "Gaming":
        t_price, t_mem, t_gclk, t_mclk, t_core, t_year, t_bench = 0.10, 0.15, 0.10, 0.10, 0.10, 0.15, 0.30
        active_defaults = all_criteria
    elif template == "Price to Performance":
        t_price, t_mem, t_gclk, t_mclk, t_core, t_year, t_bench = 0.35, 0.10, 0.0, 0.0, 0.0, 0.20, 0.35
        active_defaults = default_4_criteria
    elif template == "Content Creation":
        t_price, t_mem, t_gclk, t_mclk, t_core, t_year, t_bench = 0.10, 0.25, 0.05, 0.05, 0.20, 0.15, 0.20
        active_defaults = all_criteria
    else:
        t_price, t_mem, t_gclk, t_mclk, t_core, t_year, t_bench = 0.25, 0.10, 0.10, 0.10, 0.10, 0.20, 0.25
        active_defaults = default_4_criteria
        
    st.markdown("#### Bobot Kriteria")
    d_disable = template != "Manual"
    
    active_criteria = st.multiselect(
        "Pilih Kriteria Aktif",
        options=all_criteria,
        default=active_defaults
    )
    
    use_price = "Harga (Cost)" in active_criteria
    use_mem   = "Memory GB (Benefit)" in active_criteria
    use_gclk  = "GPU Clock (Benefit)" in active_criteria
    use_mclk  = "Memory Clock (Benefit)" in active_criteria
    use_core  = "Cores (Benefit)" in active_criteria
    use_year  = "Tahun Rilis (Benefit)" in active_criteria
    use_bench = "Benchmark (Benefit)" in active_criteria

    bar_price = bar_mem = bar_gclk = bar_mclk = bar_core = bar_year = bar_bench = 0.0
    
    if use_price:
        bar_price = st.slider("Bobot Harga", 0.01, 1.00, t_price, 0.01, disabled=d_disable)
    if use_mem:
        bar_mem = st.slider("Bobot Memory GB", 0.01, 1.00, t_mem, 0.01, disabled=d_disable)
    if use_gclk:
        bar_gclk = st.slider("Bobot GPU Clock", 0.01, 1.00, t_gclk, 0.01, disabled=d_disable)
    if use_mclk:
        bar_mclk = st.slider("Bobot Memory Clock", 0.01, 1.00, t_mclk, 0.01, disabled=d_disable)
    if use_core:
        bar_core = st.slider("Bobot Cores", 0.01, 1.00, t_core, 0.01, disabled=d_disable)
    if use_year:
        bar_year = st.slider("Bobot Tahun Rilis", 0.01, 1.00, t_year, 0.01, disabled=d_disable)
    if use_bench:
        bar_bench = st.slider("Bobot Benchmark", 0.01, 1.00, t_bench, 0.01, disabled=d_disable)
    
    # Menghitung bobot W
    bobot_awal = np.array([bar_price, bar_mem, bar_gclk, bar_mclk, bar_core, bar_year, bar_bench])
    
    if np.sum(bobot_awal) == 0:
        st.warning("Silakan aktifkan setidaknya satu kriteria SPK.")
        w = np.zeros_like(bobot_awal)
    else:
        w = bobot_awal / np.sum(bobot_awal)
    
    
# Page 1
if page == "Page 1 - Main Page":
    total_gpu = len(df_all)
    
    hero_section = f"""
    <style>
    @keyframes countUpAnim {{
        from {{ --num: 0; }}
        to {{ --num: {total_gpu}; }}
    }}
    </style>
    <div class="hero-container">
        <div class="hero-col-left">
            <div class="top-left">
                <span class="hero-app-name">GPUPICKER</span>
            </div>
            <div class="bottom-left">
                <div class="brands-reveal">
                    <div class="brands-rotor">
                        <div class="brand-word">Nvidia</div>
                        <div class="brand-word">AMD</div>
                        <div class="brand-word">Intel</div>
                        <div class="brand-word">Nvidia</div> 
                    </div>
                </div>
            </div>
        </div>
        <div class="hero-col-right">
            <div class="top-right">
                <span class="hero-number"></span>
                <span class="hero-text-large">GPU Recorded</span>
            </div>
            <div class="bottom-right">
                <span class="hero-text-large">in Database</span>
            </div>
        </div>
    </div>
    """
    
    st.markdown(hero_section, unsafe_allow_html=True)
    
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

    # 1 - IDENTIFIKASI KRITERIA AKTIF (Filter kolom jika bobot bernilai > 0)
    aktif_idx = [i for i, val in enumerate(bobot_awal) if val > 0]
    
    all_k = np.array([0, 1, 1, 1, 1, 1, 1]) 
    all_cols = ['Price', 'Memory_GB', 'GPU_Clock_MHz', 'Memory_Clock_MHz', 'Cores', 'Release_Year', 'Benchmark_Score']
    all_kriteria_names = ["Price (IDR)", "Memory (GB)", "GPU Clock (MHz)", "Memory Clock (MHz)", "Cores", "Tahun Rilis", "Benchmark Score"]
    
    k = all_k[aktif_idx]
    cols_aktif = [all_cols[i] for i in aktif_idx]
    kriteria_names = [all_kriteria_names[i] for i in aktif_idx]
    w_aktif = w[aktif_idx]
    
    # 2 - MEMBENTUK MATRIKS KEPUTUSAN (X): Hanya mengambil kolom yang aktif
    x = df_eval[cols_aktif].values
    alternatif_names = df_eval['Name'].values

    m, n = x.shape
    
    # 3 - NORMALISASI MATRIKS (R)
    R = np.zeros((m, n)) 
    for j in range(n):
        if k[j] == 1: 
            R[:, j] = x[:, j] / np.max(x[:, j])
        else: 
            R[:, j] = np.min(x[:, j]) / x[:, j]

    # 4 - PERHITUNGAN PREFERENSI (V): Kalikan normalisasi dengan bobot yg aktif
    V = np.sum(w_aktif * R, axis=1)

    # 5 - PERANGKINGAN: Memasukkan nilai V ke dataframe lalu diurutkan
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
        st.dataframe(pd.DataFrame([w_aktif], columns=kriteria_names, index=["Bobot W (Ternormalisasi)"]).style.format("{:.4f}"), use_container_width=True)
        
        st.subheader("5. Hasil Perangkingan Akhir (V)")
        st.latex(r"V_i = \sum_{j=1}^{n} w_j r_{ij}")
        df_v = pd.DataFrame(V, columns=["Nilai V"], index=alternatif_names).sort_values(by="Nilai V", ascending=False)
        st.dataframe(df_v.style.format("{:.5f}"), use_container_width=True)
        
        st.markdown("""
        <div class="viz-dashboard-header">
            <div>
                <div class="viz-header-title">Data Visualizations</div>
                <div class="viz-header-sub">Select charts below to explore results</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        plotly_layout = dict(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(22,22,22,0.8)',
            font=dict(family="Inter, Source Sans Pro, sans-serif", color='#c0c0c0', size=12),
            margin=dict(l=40, r=20, t=50, b=40),
            hoverlabel=dict(bgcolor='#1e1e1e', font_color='#e0e0e0', font_size=12, bordercolor='#333'),
            legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor='#333', font=dict(size=11)),
            xaxis=dict(gridcolor='#2a2a2a', zerolinecolor='#333'),
            yaxis=dict(gridcolor='#2a2a2a', zerolinecolor='#333'),
        )
        
        MFG_COLORS = {'NVIDIA': '#76B900', 'AMD': '#ED1C24', 'Intel': '#0071C5', 'Other': '#888888'}
        
        st.markdown('<div class="viz-control-bar">', unsafe_allow_html=True)
        ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([3, 1, 1])
        
        available_charts = [
            "Top N GPU Ranking",
            "Criteria Weight Distribution",
            "Price vs Benchmark",
            "Radar Comparison (Top 5)",
            "Benchmark by Manufacturer",
            "Memory vs Clock Heatmap",
            "Release Year Trend",
        ]
        
        with ctrl_col1:
            selected_charts = st.multiselect(
                "Choose Visualizations",
                options=available_charts,
                default=["Top N GPU Ranking"],
                help="Pick which charts to display below."
            )
        with ctrl_col2:
            top_n = st.slider("GPUs to show", 5, min(30, len(df_result)), 10, help="Controls ranking charts")
        with ctrl_col3:
            color_mode = st.selectbox("Color by", ["Manufacturer", "Ranking Tier"], help="Color scheme for charts")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if not selected_charts:
            st.info("Select at least one visualization from the dropdown above.")
        
        def get_tier_color(rank):
            if rank <= 3: return '#FFD700'
            elif rank <= 10: return '#C0C0C0'
            elif rank <= 20: return '#CD7F32'
            return '#555555'
        
        def get_color(row, mode):
            if mode == "Manufacturer":
                return MFG_COLORS.get(row.get('Manufacturer', ''), '#888')
            return get_tier_color(row.get('Ranking', 99))
    
        def render_top_n_ranking():
            top = df_result.head(top_n).sort_values(by="Nilai V", ascending=True)
            
            if color_mode == "Manufacturer":
                colors = [MFG_COLORS.get(m, '#888') for m in top['Manufacturer']]
            else:
                colors = [get_tier_color(r) for r in top['Ranking']]
            
            fig = go.Figure(go.Bar(
                x=top['Nilai V'],
                y=top['Name'],
                orientation='h',
                marker=dict(color=colors, line=dict(width=0)),
                text=[f"{v:.4f}" for v in top['Nilai V']],
                textposition='outside',
                textfont=dict(size=10, color='#aaa'),
                hovertemplate='<b>%{y}</b><br>V-Score: %{x:.5f}<br><extra></extra>',
            ))
            
            fig.update_layout(**plotly_layout)
    
            fig.update_layout(
                title=dict(text=f'Top {top_n} GPU by SAW Score', font=dict(size=15, color='#e0e0e0')),
                xaxis_title='SAW Score (V)',
                yaxis=dict(gridcolor='rgba(0,0,0,0)'),
                height=max(350, top_n * 32),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True, key="chart_ranking")
        
        def render_weight_donut():
            fig = go.Figure(go.Pie(
                labels=kriteria_names,
                values=w_aktif,
                hole=0.55,
                marker=dict(
                    colors=px.colors.qualitative.Set3[:len(kriteria_names)],
                    line=dict(color='#1a1a1a', width=2)
                ),
                textinfo='label+percent',
                textfont=dict(size=11, color='#ccc'),
                hovertemplate='<b>%{label}</b><br>Weight: %{value:.4f}<br>Share: %{percent}<extra></extra>',
            ))
            
            fig.update_layout(**plotly_layout)
            
            fig.update_layout(
                title=dict(text='Criteria Weight Distribution', font=dict(size=15, color='#e0e0e0')),
                height=400,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(size=10, color='#aaa')),
                annotations=[dict(text='Weights', x=0.5, y=0.5, font_size=14, font_color='#666', showarrow=False)],
            )
            st.plotly_chart(fig, use_container_width=True, key="chart_donut")
        
        def render_price_vs_benchmark():
            scatter_df = df_result.head(top_n).copy()
            
            fig = px.scatter(
                scatter_df,
                x='Price',
                y='Benchmark_Score',
                size='Memory_GB',
                color='Manufacturer',
                color_discrete_map=MFG_COLORS,
                hover_name='Name',
                hover_data={
                    'Price': ':,.0f',
                    'Benchmark_Score': ':.1f',
                    'Memory_GB': ':.0f',
                    'Ranking': True,
                    'Manufacturer': False,
                },
                size_max=35,
            )

            fig.update_layout(**plotly_layout)
            
            fig.update_layout(
                title=dict(text='Price vs Benchmark (bubble = Memory GB)', font=dict(size=15, color='#e0e0e0')),
                xaxis_title='Price (IDR)',
                yaxis_title='Benchmark Score',
                height=450,
            )
            fig.update_traces(marker=dict(line=dict(width=1, color='#333'), opacity=0.85))
            st.plotly_chart(fig, use_container_width=True, key="chart_scatter")
        
        def render_radar():
            top5 = df_result.head(5)
            radar_cols = [c for c in cols_aktif]
            
            fig = go.Figure()
            
            color_palette = ['#76B900', '#ED1C24', '#0071C5', '#FFD700', '#FF6B9D']
            
            for i, (_, row) in enumerate(top5.iterrows()):
                row_idx = df_eval.index.get_loc(row.name) if row.name in df_eval.index else i
                if row_idx < R.shape[0]:
                    r_vals = [R[row_idx, cols_aktif.index(c)] if c in cols_aktif else 0 for c in radar_cols]
                else:
                    continue
                r_vals_closed = r_vals + [r_vals[0]]
                theta_closed = [kriteria_names[cols_aktif.index(c)] for c in radar_cols] + [kriteria_names[cols_aktif.index(radar_cols[0])]]
                
                clr = color_palette[i % len(color_palette)]
                fig.add_trace(go.Scatterpolar(
                    r=r_vals_closed,
                    theta=theta_closed,
                    name=f"#{int(row['Ranking'])} {row['Name']}",
                    fill='toself',
                    fillcolor=f"rgba({int(clr[1:3],16)},{int(clr[3:5],16)},{int(clr[5:7],16)},0.08)",
                    line=dict(color=clr, width=2),
                    hovertemplate='%{theta}: %{r:.3f}<extra>%{fullData.name}</extra>',
                ))
            
            fig.update_layout(**plotly_layout)
            
            fig.update_layout(
                title=dict(text='Radar Comparison — Top 5 GPUs', font=dict(size=15, color='#e0e0e0')),
                polar=dict(
                    bgcolor='rgba(22,22,22,0.6)',
                    radialaxis=dict(visible=True, range=[0, 1.05], gridcolor='#2a2a2a', linecolor='#333', tickfont=dict(size=9, color='#666')),
                    angularaxis=dict(gridcolor='#2a2a2a', linecolor='#333', tickfont=dict(size=10, color='#aaa')),
                ),
                height=480,
                showlegend=True,
                legend=dict(font=dict(size=10)),
            )
            st.plotly_chart(fig, use_container_width=True, key="chart_radar")
        
        def render_benchmark_box():
            fig = px.box(
                df_result,
                x='Manufacturer',
                y='Benchmark_Score',
                color='Manufacturer',
                color_discrete_map=MFG_COLORS,
                points='all',
                hover_data=['Name', 'Price'],
            )
            
            fig.update_layout(**plotly_layout)
            
            fig.update_layout(
                title=dict(text='Benchmark Distribution by Manufacturer', font=dict(size=15, color='#e0e0e0')),
                xaxis_title='',
                yaxis_title='Benchmark Score',
                height=420,
                showlegend=False,
            )
            fig.update_traces(marker=dict(size=5, opacity=0.6), jitter=0.3)
            st.plotly_chart(fig, use_container_width=True, key="chart_box")
        
        def render_mem_clock_heatmap():
            fig = px.scatter(
                df_result.head(top_n),
                x='Memory_GB',
                y='GPU_Clock_MHz',
                color='Nilai V',
                color_continuous_scale=['#1a1a2e', '#16213e', '#0f3460', '#e94560', '#FFD700'],
                hover_name='Name',
                hover_data={
                    'Memory_GB': ':.0f',
                    'GPU_Clock_MHz': ':.0f',
                    'Nilai V': ':.4f',
                    'Manufacturer': True,
                },
                size='Benchmark_Score',
                size_max=30,
            )
            
            fig.update_layout(**plotly_layout)
            
            fig.update_layout(
                title=dict(text='Memory vs GPU Clock (color = V-Score)', font=dict(size=15, color='#e0e0e0')),
                xaxis_title='Memory (GB)',
                yaxis_title='GPU Clock (MHz)',
                height=420,
                coloraxis_colorbar=dict(
                    title=dict(text='V-Score', font=dict(size=11, color='#aaa')), 
                    tickfont=dict(size=10, color='#aaa')
                ),
            )
            fig.update_traces(marker=dict(line=dict(width=1, color='#333'), opacity=0.85))
            st.plotly_chart(fig, use_container_width=True, key="chart_heatmap")
        
        def render_year_trend():
            trend = df_result.groupby('Release_Year').agg(
                Avg_Benchmark=('Benchmark_Score', 'mean'),
                Count=('Name', 'count'),
                Avg_V=('Nilai V', 'mean'),
            ).reset_index()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=trend['Release_Year'],
                y=trend['Avg_Benchmark'],
                mode='lines+markers',
                name='Avg Benchmark',
                line=dict(color='#76B900', width=2.5, shape='spline'),
                marker=dict(size=trend['Count'] * 2 + 4, color='#76B900', line=dict(width=1, color='#333')),
                hovertemplate='<b>Year %{x:.0f}</b><br>Avg Benchmark: %{y:.1f}<br>GPUs: %{marker.size}<extra></extra>',
            ))
            fig.add_trace(go.Bar(
                x=trend['Release_Year'],
                y=trend['Count'],
                name='GPU Count',
                marker=dict(color='rgba(118,185,0,0.15)', line=dict(width=0)),
                yaxis='y2',
                hovertemplate='Year %{x:.0f}<br>Count: %{y}<extra></extra>',
            ))
            
            fig.update_layout(**plotly_layout)
            
            fig.update_layout(
                title=dict(text='Benchmark Trend by Release Year', font=dict(size=15, color='#e0e0e0')),
                xaxis_title='Release Year',
                yaxis=dict(title='Avg Benchmark Score', gridcolor='#2a2a2a', zerolinecolor='#333'),
                yaxis2=dict(title=dict(text='GPU Count', font=dict(color='#555')), overlaying='y', side='right', showgrid=False, tickfont=dict(color='#555')),
                height=400,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig, use_container_width=True, key="chart_trend")
        
        chart_dispatch = {
            "Top N GPU Ranking": render_top_n_ranking,
            "Criteria Weight Distribution": render_weight_donut,
            "Price vs Benchmark": render_price_vs_benchmark,
            "Radar Comparison (Top 5)": render_radar,
            "Benchmark by Manufacturer": render_benchmark_box,
            "Memory vs Clock Heatmap": render_mem_clock_heatmap,
            "Release Year Trend": render_year_trend,
        }
        
        if selected_charts:
            for i in range(0, len(selected_charts), 2):
                pair = selected_charts[i:i+2]
                if len(pair) == 2:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        with st.container(border=True):
                            chart_dispatch[pair[0]]()
                    with col_b:
                        with st.container(border=True):
                            chart_dispatch[pair[1]]()
                else:
                    with st.container(border=True):
                        chart_dispatch[pair[0]]()


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

        # inject css
        st.markdown(f"""
        <style>
            :root {{
                --mfg-color: {mfg_color};
                --mfg-bg: {mfg_bg};
                --mfg-border: {mfg_color}44;
            }}
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
                
                logo_img  = f'<a class="ub-site" href="{ub_url}" target="_blank" style="color: white; text-decoration: none;">UserBenchmark.com</a>'
                
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