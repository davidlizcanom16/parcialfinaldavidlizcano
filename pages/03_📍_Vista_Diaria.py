# pages/03_📍_Vista_Diaria.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.data_loader import cargar_datos, get_restaurante_color
from utils.metrics import calcular_metricas_diarias

st.set_page_config(page_title="Vista Diaria", page_icon="📍", layout="wide")

# ==========================================
# CARGAR DATOS
# ==========================================

df = cargar_datos()

if df is None:
    st.error("❌ Error cargando datos")
    st.stop()

# ==========================================
# HEADER
# ==========================================

st.title("📍 Vista Diaria - Análisis del Día")
st.markdown("---")

# ==========================================
# SELECTOR DE FECHA
# ==========================================

col1, col2 = st.columns([1, 3])

with col1:
    fecha_min = df['fecha'].min().date()
    fecha_max = df['fecha'].max().date()
    
    fecha_sel = st.date_input(
        "Selecciona una fecha",
        value=fecha_max,
        min_value=fecha_min,
        max_value=fecha_max
    )

st.markdown("---")

# ==========================================
# MÉTRICAS DIARIAS
# ==========================================

metricas = calcular_metricas_diarias(df, fecha_sel)

if metricas is None:
    st.warning(f"No hay datos para {fecha_sel}")
    st.stop()

# Info de la fecha
dia_semana_esp = {
    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
    'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
}

dia_nombre = pd.to_datetime(fecha_sel).day_name()
st.subheader(f"📅 {dia_semana_esp[dia_nombre]}, {fecha_sel.strftime('%d de %B de %Y')}")

if metricas['tiene_evento']:
    st.success("🎉 **Día con evento especial**")

# KPIs del día
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "💰 Ventas del Día",
        f"${metricas['ventas_totales']:,.0f}",
        f"{metricas['vs_promedio_dia_similar']:+.1f}% vs promedio"
    )

with col2:
    st.metric(
        "📦 Unidades Vendidas",
        f"{metricas['unidades_vendidas']:,.0f}",
        None
    )

with col3:
    st.metric(
        "🍽️ Productos Vendidos",
        metricas['productos_vendidos'],
        None
    )

with col4:
    st.metric(
        "🎫 Ticket Promedio",
        f"${metricas['ticket_promedio']:,.0f}",
        None
    )

st.markdown("---")

# ==========================================
# VENTAS POR RESTAURANTE
# ==========================================

st.header("🏪 Ventas por Restaurante")

df_dia = df[df['fecha'] == pd.to_datetime(fecha_sel)]
ventas_rest = df_dia.groupby('restaurante')['venta_pesos'].sum().sort_values(ascending=False)

col1, col2 = st.columns([2, 1])

with col1:
    fig = go.Figure(go.Bar(
        x=ventas_rest.index,
        y=ventas_rest.values,
        marker=dict(
            color=[get_restaurante_color(r) for r in ventas_rest.index]
        ),
        text=[f'${v:,.0f}' for v in ventas_rest.values],
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Ventas por Restaurante',
        xaxis_title='',
        yaxis_title='Ventas (COP)',
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Detalle")
    
    for rest, venta in ventas_rest.items():
        porcentaje = (venta / ventas_rest.sum()) * 100
        color = get_restaurante_color(rest)
        
        emoji = "🥇" if rest == ventas_rest.index[0] else "🥈" if rest == ventas_rest.index[1] else "🥉"
        
        st.markdown(f"""
        <div style='background: {color}20; padding: 1rem; border-radius: 0.5rem; 
                    margin-bottom: 0.5rem; border-left: 4px solid {color};'>
            <div style='font-size: 1.2rem;'>{emoji} <strong>{rest}</strong></div>
            <div style='font-size: 1.5rem; font-weight: 700;'>${venta:,.0f}</div>
            <div style='font-size: 0.9rem; color: #666;'>{porcentaje:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# PRODUCTOS DEL DÍA
# ==========================================

st.header("📋 Productos Vendidos")

productos_dia = df_dia.groupby('producto').agg({
    'cantidad_vendida_diaria': 'sum',
    'venta_pesos': 'sum'
}).sort_values('venta_pesos', ascending=False)

col1, col2 = st.columns(2)

with col1:
    st.subheader("🏆 Top 5 por Ventas")
    
    top_5_ventas = productos_dia.head(5)
    
    for i, (producto, row) in enumerate(top_5_ventas.iterrows(), 1):
        st.markdown(f"""
        <div style='background: #f8f9fa; padding: 0.8rem; border-radius: 0.5rem; 
                    margin-bottom: 0.5rem; border-left: 4px solid #667eea;'>
            <div style='font-weight: 600;'>{i}. {producto}</div>
            <div style='font-size: 1.2rem; font-weight: 700; color: #667eea;'>${row['venta_pesos']:,.0f}</div>
            <div style='font-size: 0.85rem; color: #666;'>{row['cantidad_vendida_diaria']:.0f} unidades</div>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.subheader("📦 Top 5 por Cantidad")
    
    top_5_cantidad = productos_dia.sort_values('cantidad_vendida_diaria', ascending=False).head(5)
    
    for i, (producto, row) in enumerate(top_5_cantidad.iterrows(), 1):
        st.markdown(f"""
        <div style='background: #f8f9fa; padding: 0.8rem; border-radius: 0.5rem; 
                    margin-bottom: 0.5rem; border-left: 4px solid #4ECDC4;'>
            <div style='font-weight: 600;'>{i}. {producto}</div>
            <div style='font-size: 1.2rem; font-weight: 700; color: #4ECDC4;'>{row['cantidad_vendida_diaria']:.0f} unidades</div>
            <div style='font-size: 0.85rem; color: #666;'>${row['venta_pesos']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# COMPARACIÓN CON DÍAS SIMILARES
# ==========================================

st.header("📊 Comparación con Días Similares")

# Últimos 4 días del mismo día de semana
df_mismo_dia = df[df['dia_semana'] == dia_nombre].copy()
df_mismo_dia = df_mismo_dia.sort_values('fecha', ascending=False).head(5)

ventas_mismo_dia = df_mismo_dia.groupby('fecha')['venta_pesos'].sum().sort_index()

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=ventas_mismo_dia.index,
    y=ventas_mismo_dia.values,
    mode='lines+markers',
    name='Ventas',
    line=dict(color='#667eea', width=3),
    marker=dict(size=10)
))

# Marcar el día seleccionado
if pd.to_datetime(fecha_sel) in ventas_mismo_dia.index:
    venta_sel = ventas_mismo_dia[pd.to_datetime(fecha_sel)]
    fig.add_trace(go.Scatter(
        x=[pd.to_datetime(fecha_sel)],
        y=[venta_sel],
        mode='markers',
        name='Día Seleccionado',
        marker=dict(size=15, color='#f5576c', symbol='star')
    ))

fig.update_layout(
    title=f'Últimos {dia_semana_esp[dia_nombre]}s',
    xaxis_title='Fecha',
    yaxis_title='Ventas (COP)',
    height=400,
    hovermode='x unified'
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================
# INSIGHT
# ==========================================

promedio_similares = ventas_mismo_dia.mean()
diferencia = metricas['ventas_totales'] - promedio_similares
porcentaje_dif = (diferencia / promedio_similares) * 100

if porcentaje_dif > 10:
    st.success(f"""
    💡 **Excelente día:** Las ventas fueron **{porcentaje_dif:.1f}% superiores** al promedio 
    de otros {dia_semana_esp[dia_nombre]}s (${promedio_similares:,.0f})
    """)
elif porcentaje_dif < -10:
    st.warning(f"""
    ⚠️ **Día bajo:** Las ventas fueron **{abs(porcentaje_dif):.1f}% inferiores** al promedio 
    de otros {dia_semana_esp[dia_nombre]}s (${promedio_similares:,.0f})
    """)
else:
    st.info(f"""
    📊 **Día normal:** Las ventas estuvieron cerca del promedio de otros {dia_semana_esp[dia_nombre]}s 
    (${promedio_similares:,.0f})
    """)
