# pages/02_📆_Vista_Mensual.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.data_loader import cargar_datos, get_restaurante_color
from utils.metrics import calcular_metricas_mensuales

st.set_page_config(page_title="Vista Mensual", page_icon="📆", layout="wide")

# ==========================================
# ESTILOS
# ==========================================

st.markdown("""
<style>
    .month-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 1rem;
        text-align: center;
    }
    .delta-positive {
        color: #43e97b;
        font-size: 1.5rem;
        font-weight: 700;
    }
    .delta-negative {
        color: #f5576c;
        font-size: 1.5rem;
        font-weight: 700;
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
# HEADER
# ==========================================

st.title("📆 Vista Mensual - Análisis Detallado")
st.markdown("---")

# ==========================================
# SELECTORES
# ==========================================

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    años = sorted(df['año'].unique(), reverse=True)
    año_sel = st.selectbox("Año", años, index=0)

with col2:
    meses_disponibles = sorted(df[df['año'] == año_sel]['mes'].unique(), reverse=True)
    mes_sel = st.selectbox("Mes", meses_disponibles, index=0)

st.markdown("---")

# ==========================================
# MÉTRICAS MENSUALES
# ==========================================

metricas = calcular_metricas_mensuales(df, año_sel, mes_sel)

if metricas is None:
    st.warning("No hay datos para este mes")
    st.stop()

# Nombre del mes
meses_nombres = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

st.header(f"📊 {meses_nombres[mes_sel]} {año_sel}")

# KPIs con comparación
col1, col2, col3, col4 = st.columns(4)

with col1:
    cambio = metricas['cambio_vs_anterior']
    delta_class = 'delta-positive' if cambio > 0 else 'delta-negative'
    emoji = "📈" if cambio > 0 else "📉"
    
    st.metric(
        "💰 Ventas del Mes",
        f"${metricas['ventas_totales']:,.0f}",
        f"{cambio:+.1f}% vs mes anterior"
    )

with col2:
    st.metric(
        "📅 Días Operación",
        metricas['dias_operacion'],
        None
    )

with col3:
    st.metric(
        "📈 Venta Prom/Día",
        f"${metricas['ventas_promedio_dia']:,.0f}",
        None
    )

with col4:
    st.metric(
        "🏆 Mejor Día Semana",
        metricas['mejor_dia_semana'],
        None
    )

st.markdown("---")

# ==========================================
# EVOLUCIÓN DIARIA
# ==========================================

st.header("📈 Evolución Diaria del Mes")

df_mes = df[(df['año'] == año_sel) & (df['mes'] == mes_sel)]
ventas_diarias = df_mes.groupby('fecha')['venta_pesos'].sum().reset_index()

fig = px.line(
    ventas_diarias,
    x='fecha',
    y='venta_pesos',
    title=f'Ventas Diarias - {meses_nombres[mes_sel]} {año_sel}',
    labels={'fecha': 'Fecha', 'venta_pesos': 'Ventas (COP)'},
    markers=True
)

# Línea de promedio
promedio = ventas_diarias['venta_pesos'].mean()
fig.add_hline(
    y=promedio,
    line_dash="dash",
    line_color="red",
    annotation_text=f"Promedio: ${promedio:,.0f}",
    annotation_position="right"
)

fig.update_traces(line_color='#667eea', line_width=3)
fig.update_layout(height=400, hovermode='x unified')
st.plotly_chart(fig, use_container_width=True)

# ==========================================
# MEJORES Y PEORES DÍAS
# ==========================================

col1, col2 = st.columns(2)

with col1:
    mejor_fecha = metricas['mejor_dia']
    venta_mejor = ventas_diarias[ventas_diarias['fecha'] == mejor_fecha]['venta_pesos'].values[0]
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); 
                color: white; padding: 1.5rem; border-radius: 1rem; text-align: center;'>
        <h3>🏆 Mejor Día</h3>
        <p style='font-size: 1.2rem; margin: 0;'>{mejor_fecha.strftime('%d de %B')}</p>
        <p style='font-size: 2rem; font-weight: 700; margin: 0.5rem 0;'>${venta_mejor:,.0f}</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    peor_fecha = metricas['peor_dia']
    venta_peor = ventas_diarias[ventas_diarias['fecha'] == peor_fecha]['venta_pesos'].values[0]
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                color: white; padding: 1.5rem; border-radius: 1rem; text-align: center;'>
        <h3>⚠️ Día Más Bajo</h3>
        <p style='font-size: 1.2rem; margin: 0;'>{peor_fecha.strftime('%d de %B')}</p>
        <p style='font-size: 2rem; font-weight: 700; margin: 0.5rem 0;'>${venta_peor:,.0f}</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# PERFORMANCE POR RESTAURANTE
# ==========================================

st.header("🏪 Performance por Restaurante")

ventas_rest = df_mes.groupby('restaurante')['venta_pesos'].sum().sort_values(ascending=False)

col1, col2 = st.columns([2, 1])

with col1:
    fig = px.pie(
        values=ventas_rest.values,
        names=ventas_rest.index,
        title='Distribución de Ventas por Restaurante',
        color=ventas_rest.index,
        color_discrete_map={r: get_restaurante_color(r) for r in ventas_rest.index},
        hole=0.4
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Ventas del Mes")
    for rest, venta in ventas_rest.items():
        color = get_restaurante_color(rest)
        porcentaje = (venta / ventas_rest.sum()) * 100
        
        st.markdown(f"""
        <div style='background: {color}20; padding: 1rem; border-radius: 0.5rem; 
                    margin-bottom: 0.5rem; border-left: 4px solid {color};'>
            <div style='font-weight: 600;'>{rest}</div>
            <div style='font-size: 1.3rem; font-weight: 700;'>${venta:,.0f}</div>
            <div style='font-size: 0.9rem; color: #666;'>{porcentaje:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# TOP 5 PRODUCTOS DEL MES
# ==========================================

st.header("⭐ Top 5 Productos del Mes")

top_5 = metricas['top_3_productos'].head(5)

fig = go.Figure(go.Bar(
    x=top_5.values,
    y=top_5.index,
    orientation='h',
    marker=dict(
        color=top_5.values,
        colorscale='Plasma',
        showscale=False
    ),
    text=[f'${v:,.0f}' for v in top_5.values],
    textposition='outside'
))

fig.update_layout(
    title='',
    xaxis_title='Ventas (COP)',
    yaxis_title='',
    height=350,
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================
# INSIGHTS
# ==========================================

st.markdown("---")
st.header("💡 Insights del Mes")

col1, col2 = st.columns(2)

with col1:
    # Análisis de fines de semana
    ventas_fds = df_mes[df_mes['es_fin_semana'] == 1]['venta_pesos'].sum()
    ventas_semana = df_mes[df_mes['es_fin_semana'] == 0]['venta_pesos'].sum()
    
    if ventas_semana > 0:
        ratio_fds = (ventas_fds / ventas_semana) * 100
        
        st.info(f"""
        **📅 Fin de Semana vs Semana**
        
        - Ventas fin de semana: ${ventas_fds:,.0f}
        - Ventas entre semana: ${ventas_semana:,.0f}
        - Ratio: {ratio_fds:.1f}%
        """)

with col2:
    # Variabilidad
    std_ventas = ventas_diarias['venta_pesos'].std()
    cv = (std_ventas / ventas_diarias['venta_pesos'].mean()) * 100
    
    if cv < 20:
        estabilidad = "🟢 Muy Estable"
    elif cv < 40:
        estabilidad = "🟡 Moderada"
    else:
        estabilidad = "🔴 Alta Variabilidad"
    
    st.info(f"""
    **📊 Estabilidad de Ventas**
    
    - Desviación estándar: ${std_ventas:,.0f}
    - Coeficiente de variación: {cv:.1f}%
    - Estado: {estabilidad}
    """)
