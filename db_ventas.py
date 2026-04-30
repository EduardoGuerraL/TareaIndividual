import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px

# --- Configuración de la página ---
st.set_page_config(page_title="Dashboard Logística RM", layout="wide")

# --- 1. Carga de datos--
@st.cache_data
def load_data():
    # Usamos el dataset que entregaste
    df = pd.read_excel('dataset_tarea_ind.xlsx')
    
    # Limpieza express (la misma que ya validamos)
    cols_fix = ['venta_neta', 'lat', 'lng', 'kms_dist', 'lat_cd', 'lng_cd']
    for col in cols_fix:
        df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
    
    df['fecha_compra'] = pd.to_datetime(df['fecha_compra'], format='%d-%m-%y')
    df['comuna'] = df['comuna'].str.strip().str.title()
    return df

df = load_data()

# --- 2. Sidebar / Filtros ---
st.sidebar.header("Filtros de Exploración")

# Filtro por Canal
canales = df['canal'].unique().tolist()
canal_selected = st.sidebar.multiselect("Selecciona Canal", canales, default=canales)

# Filtro por Centro de Distribución
cds = df['centro_dist'].unique().tolist()
cd_selected = st.sidebar.multiselect("Centro de Distribución", cds, default=cds)

# Slider de Distancia (Kms de entrega)
min_km, max_km = int(df['kms_dist'].min()), int(df['kms_dist'].max())
dist_range = st.sidebar.slider("Rango de Distancia (Kms)", min_km, max_km, (min_km, max_km))

# Aplicar Filtros
df_filtered = df[
    (df['canal'].isin(canal_selected)) &
    (df['centro_dist'].isin(cd_selected)) &
    (df['kms_dist'].between(dist_range[0], dist_range[1]))
]

# --- 3. Layout del Dashboard ---
st.title("Dashboard de Red Logística y Ventas")
st.markdown("Analiza el comportamiento de entregas en la Región Metropolitana.")

# Fila 1: KPIs
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Venta Total", f"${df_filtered['venta_neta'].sum():,.0f}")
with col2:
    st.metric("Ticket Promedio", f"${df_filtered['venta_neta'].mean():,.0f}")
with col3:
    st.metric("Total Pedidos", len(df_filtered))

st.divider()

# Fila 2: Gráfico y Mapa
col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("Ventas por Canal")
    fig_canal = px.bar(df_filtered.groupby('canal')['venta_neta'].sum().reset_index(), 
                       x='canal', y='venta_neta', color='canal',
                       labels={'venta_neta': 'Venta Total ($)', 'canal': 'Canal'})
    st.plotly_chart(fig_canal, use_container_width=True)
    
    st.info(f"Mostrando una muestra de {min(500, len(df_filtered))} puntos en el mapa para optimizar carga.")

with col_right:
    st.subheader("Distribución Territorial")
    
    # Crear el mapa base
    m = folium.Map(location=[-33.45, -70.66], zoom_start=10, tiles='cartodbpositron')
    
    # Capa de puntos de entrega (Muestra de 500 para no laggear el navegador)
    # Mostramos los puntos filtrados
    muestra = df_filtered.sample(min(500, len(df_filtered)))
    for _, r in muestra.iterrows():
        folium.CircleMarker(
            location=[r['lat'], r['lng']],
            radius=3,
            color='blue' if r['canal'] == 'App' else 'orange',
            fill=True,
            popup=f"Venta: ${r['venta_neta']:.0f} | Comuna: {r['comuna']}"
        ).add_to(m)
    
    # Capa de Centros de Distribución (Marcadores fijos)
    cds_info = df_filtered.drop_duplicates(subset=['centro_dist'])
    for _, r in cds_info.iterrows():
        folium.Marker(
            location=[r['lat_cd'], r['lng_cd']],
            popup=f"BODEGA: {r['centro_dist']}",
            icon=folium.Icon(color='red', icon='home')
        ).add_to(m)
    
    # Desplegar mapa con streamlit-folium
    st_folium(m, width=800, height=500, returned_objects=[])


