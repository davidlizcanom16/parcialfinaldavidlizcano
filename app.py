# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data_loader import cargar_datos, get_restaurante_color

# ==========================================
# CONFIGURACIÓN
# ==========================================

st.set_page_config(
    page_title="Dashboard Operativo",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# ESTILOS
# ==========================================

st.markdown("""
<style>
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(120deg, #FF6B6B 0%, #4ECDC4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #FF6B6B;
        margin-bottom: 1rem;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2c3e50;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #7f8c8d;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CARGAR DATOS
# ==========================================

df = cargar_datos()

if df is None:
    st.error("❌ No se pudieron cargar los datos. Verifica la carpeta /data/")
    st.stop()

# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:
    st.title("🍽️ Dashboard")
    st.markdown("---")
    
    st.header("📊 Información General")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Restaurantes", df['restaurante'].nunique())
    with col2:
        st.metric("Productos", df['producto'].nunique())
    
    st.metric("Período", f"{df['fecha'].min().date()} a {df['fecha'].max().date()}")
    st.metric("Total Días", df['fecha'].nunique())
    
    st.markdown("---")
    
    st.header("🎨 Vista Rápida")
    
    for restaurante in df['restaurante'].unique():
        df_rest = df[df['restaurante'] == restaurante]
        ventas = df_rest['venta_pesos'].sum()
        color = get_restaurante_color(restaurante)
        
        st.markdown(f"""
        <div style='background: {color}20; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid {color}; margin-bottom: 0.5rem;'>
            <div style='font-weight: 600; color: {color};'>{restaurante}</div>
            <div style='font-size: 1.2rem; font-weight: 700;'>${ventas:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# CONTENIDO PRINCIPAL
# ==========================================

st.markdown("<h1 class='main-title'>🍽️ Dashboard Operativo</h1>", unsafe_allow_html=True)

st.markdown("""
<div style='text-align: center; font-size: 1.2rem; color: #7f8c8d; margin-bottom: 2rem;'>
    Análisis inteligente de ventas para restaurantes de Barranquilla
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# KPIs
col1, col2, col3, col4 = st.columns(4)

with col1:
    ventas_totales = df['venta_pesos'].sum()
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>💰 Ventas Totales</div>
        <div class='metric-value'>${ventas_totales/1e6:.1f}M</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    unidades_totales = df['cantidad_vendida_diaria'].sum()
    st.markdown(f"""
    <div class='metric-card' style='border-left-color: #4ECDC4;'>
        <div class='metric-label'>📦 Unidades Vendidas</div>
        <div class='metric-value'>{unidades_totales:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    ticket_promedio = df.groupby('fecha')['venta_pesos'].sum().mean()
    st.markdown(f"""
    <div class='metric-card' style='border-left-color: #FFD93D;'>
        <div class='metric-label'>🎫 Venta Prom/Día</div>
        <div class='metric-value'>${ticket_promedio/1e3:.1f}K</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    dias_operacion = df['fecha'].nunique()
    st.markdown(f"""
    <div class='metric-card' style='border-left-color: #95E1D3;'>
        <div class='metric-label'>📅 Días Operación</div>
        <div class='metric-value'>{dias_operacion}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Comparativa
st.header("🏆 Performance por Restaurante")

import plotly.express as px

ventas_rest = df.groupby('restaurante')['venta_pesos'].sum().sort_values(ascending=False)

fig = px.bar(
    x=ventas_rest.index,
    y=ventas_rest.values,
    labels={'x': 'Restaurante', 'y': 'Ventas Totales (COP)'},
    title='Ventas por Restaurante',
    color=ventas_rest.index,
    color_discrete_map={r: get_restaurante_color(r) for r in ventas_rest.index}
)
fig.update_layout(showlegend=False, height=400)
st.plotly_chart(fig, use_container_width=True)
