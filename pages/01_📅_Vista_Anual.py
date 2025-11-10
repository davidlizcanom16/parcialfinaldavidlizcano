# pages/01_📅_Vista_Anual.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.data_loader import cargar_datos, get_restaurante_color, formatear_numero
from utils.metrics import calcular_metricas_anuales

st.set_page_config(page_title="Vista Anual", page_icon="📅", layout="wide")

# ==========================================
# ESTILOS
# ==========================================

st.markdown("""
<style>
    .big-metric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 1rem;
        text-align: center;
        margin: 1rem 0;
    }
    .big-metric-value {
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
    }
    .big-metric-label {
        font-size: 1rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .highlight-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 5px solid #FF6B6B;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CARGAR DATOS
# ==========================================

df = cargar_datos()

if df is None:
    st.error("❌ Error cargando datos")
    st.stop()

# ==========================================
# HEADER Y FILTROS
# ==========================================

st.title("📅 Vista Anual - Resumen Ejecutivo")
st.markdown("---")

# FILTROS PRINCIPALES
col1, col2, col3 = st.columns([2, 2, 2])

with col1:
    años_disponibles = sorted(df['año'].unique(), reverse=True)
    año_seleccionado = st.selectbox(
        "📅 Selecciona el año",
        años_disponibles,
        index=0
    )

with col2:
    restaurantes = ['Todos'] + sorted(df['restaurante'].unique().tolist())
    restaurante_sel = st.selectbox(
        "🏪 Selecciona restaurante",
        restaurantes,
        index=0
    )

with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    if restaurante_sel != 'Todos':
        color = get_restaurante_color(restaurante_sel)
        st.markdown(f"""
        <div style='background: {color}; color: white; padding: 0.5rem 1rem; 
                    border-radius: 0.5rem; text-align: center; font-weight: 700;'>
            📍 {restaurante_sel}
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# FILTRAR DATOS
if restaurante_sel == 'Todos':
    df_filtrado = df[df['año'] == año_seleccionado]
else:
    df_filtrado = df[(df['año'] == año_seleccionado) & (df['restaurante'] == restaurante_sel)]

if len(df_filtrado) == 0:
    st.warning(f"No hay datos para {restaurante_sel} en {año_seleccionado}")
    st.stop()

# ==========================================
# MÉTRICAS ANUALES
# ==========================================

st.header(f"📊 Indicadores Clave {año_seleccionado}")

ventas_totales = df_filtrado['venta_pesos'].sum()
unidades_totales = df_filtrado['cantidad_vendida_diaria'].sum()
dias_operacion = df_filtrado['fecha'].nunique()
productos_activos = df_filtrado['producto'].nunique()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class='big-metric' style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);'>
        <div class='big-metric-label'>💰 Ventas Totales</div>
        <div class='big-metric-value'>${ventas_totales/1e6:.1f}M</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='big-metric' style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);'>
        <div class='big-metric-label'>📦 Unidades Vendidas</div>
        <div class='big-metric-value'>{unidades_totales:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='big-metric' style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);'>
        <div class='big-metric-label'>📅 Días Operación</div>
        <div class='big-metric-value'>{dias_operacion}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class='big-metric' style='background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);'>
        <div class='big-metric-label'>🍽️ Productos Activos</div>
        <div class='big-metric-value'>{productos_activos}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# ANÁLISIS MENSUAL
# ==========================================

st.header("📈 Tendencia Mensual")

ventas_mes = df_filtrado.groupby(['mes', 'mes_nombre'])['venta_pesos'].sum().reset_index()
ventas_mes = ventas_mes.sort_values('mes')

fig = px.bar(
    ventas_mes,
    x='mes_nombre',
    y='venta_pesos',
    title=f'Ventas Mensuales {año_seleccionado}',
    labels={'mes_nombre': 'Mes', 'venta_pesos': 'Ventas (COP)'},
    color='venta_pesos',
    color_continuous_scale='Viridis'
)

# Marcar mejor y peor mes
if len(ventas_mes) > 0:
    mejor_idx = ventas_mes['venta_pesos'].idxmax()
    peor_idx = ventas_mes['venta_pesos'].idxmin()
    
    fig.add_annotation(
        x=ventas_mes.loc[mejor_idx, 'mes_nombre'],
        y=ventas_mes.loc[mejor_idx, 'venta_pesos'],
        text="🏆 Mejor Mes",
        showarrow=True,
        arrowhead=2,
        bgcolor="#43e97b",
        font=dict(color="white")
    )
    
    fig.add_annotation(
        x=ventas_mes.loc[peor_idx, 'mes_nombre'],
        y=ventas_mes.loc[peor_idx, 'venta_pesos'],
        text="⚠️ Peor Mes",
        showarrow=True,
        arrowhead=2,
        bgcolor="#f5576c",
        font=dict(color="white")
    )

fig.update_layout(height=500, showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# ==========================================
# COMPARATIVA RESTAURANTES (SOLO SI ES "TODOS")
# ==========================================

if restaurante_sel == 'Todos':
    st.markdown("---")
    st.header("🏆 Comparativa entre Restaurantes")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        ventas_rest_mes = df_filtrado.groupby(['mes_nombre', 'restaurante'])['venta_pesos'].sum().reset_index()
        
        fig = px.line(
            ventas_rest_mes,
            x='mes_nombre',
            y='venta_pesos',
            color='restaurante',
            title='Evolución Mensual por Restaurante',
            labels={'mes_nombre': 'Mes', 'venta_pesos': 'Ventas (COP)', 'restaurante': 'Restaurante'},
            markers=True,
            color_discrete_map={r: get_restaurante_color(r) for r in df['restaurante'].unique()}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        ventas_rest = df_filtrado.groupby('restaurante')['venta_pesos'].sum().sort_values(ascending=False)
        
        st.subheader("Ranking Anual")
        
        for i, (rest, venta) in enumerate(ventas_rest.items(), 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            porcentaje = (venta / ventas_rest.sum()) * 100
            color = get_restaurante_color(rest)
            
            st.markdown(f"""
            <div style='background: {color}20; padding: 1rem; border-radius: 0.5rem; margin-bottom: 0.5rem; border-left: 4px solid {color};'>
                <div style='font-size: 1.5rem;'>{emoji} <strong>{rest}</strong></div>
                <div style='font-size: 1.3rem; font-weight: 700; color: {color};'>${venta:,.0f}</div>
                <div style='font-size: 0.9rem; color: #666;'>{porcentaje:.1f}% del total</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# ANÁLISIS DE DÍAS
# ==========================================

st.header("📆 Análisis por Día de la Semana")

dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
dias_esp = {
    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
    'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
}

ventas_dia = df_filtrado.groupby('dia_semana')['venta_pesos'].sum()
ventas_dia = ventas_dia.reindex(dias_orden)
ventas_dia.index = [dias_esp[d] for d in ventas_dia.index]

col1, col2 = st.columns([3, 2])

with col1:
    fig = px.bar(
        x=ventas_dia.index,
        y=ventas_dia.values,
        title='Ventas por Día de la Semana',
        labels={'x': 'Día', 'y': 'Ventas (COP)'},
        color=ventas_dia.values,
        color_continuous_scale='RdYlGn'
    )
    fig.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    mejor_dia = ventas_dia.idxmax()
    peor_dia = ventas_dia.idxmin()
    
    st.markdown(f"""
    <div class='highlight-box' style='border-left-color: #43e97b;'>
        <h4>🏆 Mejor Día: {mejor_dia}</h4>
        <p style='font-size: 1.5rem; font-weight: 700; color: #43e97b;'>${ventas_dia[mejor_dia]:,.0f}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class='highlight-box' style='border-left-color: #f5576c;'>
        <h4>⚠️ Peor Día: {peor_dia}</h4>
        <p style='font-size: 1.5rem; font-weight: 700; color: #f5576c;'>${ventas_dia[peor_dia]:,.0f}</p>
    </div>
    """, unsafe_allow_html=True)
    
    diferencia = ((ventas_dia[mejor_dia] - ventas_dia[peor_dia]) / ventas_dia[peor_dia]) * 100
    st.info(f"💡 **Insight:** {mejor_dia} vende **{diferencia:.0f}%** más que {peor_dia}")

st.markdown("---")

# ==========================================
# TOP PRODUCTOS DEL AÑO
# ==========================================

st.header("⭐ Top 10 Productos del Año")

top_productos = df_filtrado.groupby('producto').agg({
    'venta_pesos': 'sum',
    'cantidad_vendida_diaria': 'sum'
}).sort_values('venta_pesos', ascending=False).head(10)

fig = go.Figure(go.Bar(
    y=top_productos.index,
    x=top_productos['venta_pesos'],
    orientation='h',
    marker=dict(
        color=top_productos['venta_pesos'],
        colorscale='Viridis',
        showscale=True
    ),
    text=[f'${v:,.0f}' for v in top_productos['venta_pesos']],
    textposition='outside'
))

fig.update_layout(
    title='Top 10 Productos por Ventas',
    xaxis_title='Ventas (COP)',
    yaxis_title='',
    height=500,
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================
# RESUMEN EJECUTIVO
# ==========================================

st.markdown("---")
st.header("📋 Resumen Ejecutivo")

col1, col2, col3 = st.columns(3)

ventas_promedio_dia = df_filtrado.groupby('fecha')['venta_pesos'].sum().mean()
producto_estrella = df_filtrado.groupby('producto')['venta_pesos'].sum().idxmax()
ticket_promedio = ventas_totales / unidades_totales if unidades_totales > 0 else 0

with col1:
    st.markdown(f"""
    <div class='highlight-box'>
        <h4>💰 Promedio de Venta Diaria</h4>
        <p style='font-size: 2rem; font-weight: 700;'>${ventas_promedio_dia:,.0f}</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='highlight-box' style='border-left-color: #4ECDC4;'>
        <h4>🏆 Producto Estrella</h4>
        <p style='font-size: 1.2rem; font-weight: 700;'>{producto_estrella}</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='highlight-box' style='border-left-color: #FFD93D;'>
        <h4>🎫 Ticket Promedio</h4>
        <p style='font-size: 2rem; font-weight: 700;'>${ticket_promedio:,.0f}</p>
    </div>
    """, unsafe_allow_html=True)
