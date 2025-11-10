# pages/02_📆_Vista_Mensual.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.data_loader import cargar_datos, get_restaurante_color

st.set_page_config(page_title="Vista Mensual", page_icon="📆", layout="wide")

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

st.title("📆 Vista Mensual - Análisis Detallado")
st.markdown("---")

col1, col2, col3, col4 = st.columns([1, 1, 2, 1])

with col1:
    años = sorted(df['año'].unique(), reverse=True)
    año_sel = st.selectbox("📅 Año", años, index=0)

with col2:
    meses_disponibles = sorted(df[df['año'] == año_sel]['mes'].unique(), reverse=True)
    mes_sel = st.selectbox("📆 Mes", meses_disponibles, index=0)

with col3:
    restaurantes = ['Todos'] + sorted(df['restaurante'].unique().tolist())
    restaurante_sel = st.selectbox("🏪 Restaurante", restaurantes, index=0)

with col4:
    if restaurante_sel != 'Todos':
        color = get_restaurante_color(restaurante_sel)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='background: {color}; color: white; padding: 0.5rem 1rem; 
                    border-radius: 0.5rem; text-align: center; font-weight: 700;'>
            📍 {restaurante_sel}
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# FILTRAR DATOS
if restaurante_sel == 'Todos':
    df_mes = df[(df['año'] == año_sel) & (df['mes'] == mes_sel)]
else:
    df_mes = df[(df['año'] == año_sel) & (df['mes'] == mes_sel) & (df['restaurante'] == restaurante_sel)]

if len(df_mes) == 0:
    st.warning(f"No hay datos para {restaurante_sel} en este mes")
    st.stop()

# Mes anterior para comparación
if mes_sel > 1:
    df_mes_anterior = df[(df['año'] == año_sel) & (df['mes'] == mes_sel - 1)]
    if restaurante_sel != 'Todos':
        df_mes_anterior = df_mes_anterior[df_mes_anterior['restaurante'] == restaurante_sel]
else:
    df_mes_anterior = df[(df['año'] == año_sel - 1) & (df['mes'] == 12)]
    if restaurante_sel != 'Todos':
        df_mes_anterior = df_mes_anterior[df_mes_anterior['restaurante'] == restaurante_sel]

# ==========================================
# MÉTRICAS
# ==========================================

meses_nombres = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

st.header(f"📊 {meses_nombres[mes_sel]} {año_sel}")

ventas_mes = df_mes['venta_pesos'].sum()
ventas_anterior = df_mes_anterior['venta_pesos'].sum()
cambio = ((ventas_mes - ventas_anterior) / ventas_anterior * 100) if ventas_anterior > 0 else 0

dias_operacion = df_mes['fecha'].nunique()
ventas_prom_dia = df_mes.groupby('fecha')['venta_pesos'].sum().mean()

# Mejor día semana
mejor_dia_sem = df_mes.groupby('dia_semana')['venta_pesos'].sum().idxmax()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "💰 Ventas del Mes",
        f"${ventas_mes:,.0f}",
        f"{cambio:+.1f}% vs mes anterior"
    )

with col2:
    st.metric(
        "📅 Días Operación",
        dias_operacion,
        None
    )

with col3:
    st.metric(
        "📈 Venta Prom/Día",
        f"${ventas_prom_dia:,.0f}",
        None
    )

with col4:
    st.metric(
        "🏆 Mejor Día Semana",
        mejor_dia_sem,
        None
    )

st.markdown("---")

# ==========================================
# EVOLUCIÓN DIARIA
# ==========================================

st.header("📈 Evolución Diaria del Mes")

ventas_diarias = df_mes.groupby('fecha')['venta_pesos'].sum().reset_index()

fig = px.line(
    ventas_diarias,
    x='fecha',
    y='venta_pesos',
    title=f'Ventas Diarias - {meses_nombres[mes_sel]} {año_sel}',
    labels={'fecha': 'Fecha', 'venta_pesos': 'Ventas (COP)'},
    markers=True
)

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

mejor_fecha = ventas_diarias.loc[ventas_diarias['venta_pesos'].idxmax(), 'fecha']
peor_fecha = ventas_diarias.loc[ventas_diarias['venta_pesos'].idxmin(), 'fecha']
venta_mejor = ventas_diarias['venta_pesos'].max()
venta_peor = ventas_diarias['venta_pesos'].min()

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); 
                color: white; padding: 1.5rem; border-radius: 1rem; text-align: center;'>
        <h3>🏆 Mejor Día</h3>
        <p style='font-size: 1.2rem; margin: 0;'>{mejor_fecha.strftime('%d de %B')}</p>
        <p style='font-size: 2rem; font-weight: 700; margin: 0.5rem 0;'>${venta_mejor:,.0f}</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
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
# PERFORMANCE POR RESTAURANTE (SOLO SI "TODOS")
# ==========================================

if restaurante_sel == 'Todos':
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

top_5 = df_mes.groupby('producto')['venta_pesos'].sum().nlargest(5)

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
