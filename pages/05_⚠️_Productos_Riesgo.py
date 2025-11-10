# pages/05_⚠️_Productos_Riesgo.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from scipy import stats
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.data_loader import cargar_datos, get_restaurante_color

st.set_page_config(page_title="Productos Riesgo", page_icon="⚠️", layout="wide")

# ==========================================
# ESTILOS
# ==========================================

st.markdown("""
<style>
    .risk-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        text-align: center;
        margin: 0.5rem 0;
    }
    .risk-high {
        border-left: 5px solid #f5576c;
    }
    .risk-medium {
        border-left: 5px solid #FFD93D;
    }
    .risk-low {
        border-left: 5px solid #43e97b;
    }
    .alert-box {
        background: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 0.5rem;
        padding: 1rem;
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

st.title("⚠️ Productos en Riesgo - Análisis de Bajo Performance")
st.markdown("Identificación temprana de productos con tendencia negativa, baja rotación o alta variabilidad")
st.markdown("---")

col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    años = ['Todos'] + sorted(df['año'].unique().tolist(), reverse=True)
    año_sel = st.selectbox("📅 Año", años, index=0)

with col2:
    restaurantes = ['Todos'] + sorted(df['restaurante'].unique().tolist())
    restaurante_sel = st.selectbox("🏪 Restaurante", restaurantes, index=0)

with col3:
    umbral_dias = st.selectbox("📆 Últimos N días", [30, 60, 90], index=1)

st.markdown("---")

# FILTRAR DATOS
df_filtrado = df.copy()

if año_sel != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['año'] == int(año_sel)]

if restaurante_sel != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['restaurante'] == restaurante_sel]

if len(df_filtrado) == 0:
    st.warning("No hay datos para los filtros seleccionados")
    st.stop()

# Obtener últimos N días
fecha_max = df_filtrado['fecha'].max()
fecha_min_reciente = fecha_max - pd.Timedelta(days=umbral_dias)
df_reciente = df_filtrado[df_filtrado['fecha'] >= fecha_min_reciente]

# ==========================================
# CALCULAR INDICADORES DE RIESGO
# ==========================================

productos_riesgo = []

for producto in df_filtrado['producto'].unique():
    df_prod = df_filtrado[df_filtrado['producto'] == producto]
    df_prod_reciente = df_reciente[df_reciente['producto'] == producto]
    
    # Métricas básicas
    ventas_total = df_prod['venta_pesos'].sum()
    ventas_recientes = df_prod_reciente['venta_pesos'].sum()
    dias_total = len(df_prod)
    dias_recientes = len(df_prod_reciente)
    
    if dias_total < 10:  # Muy poco histórico
        continue
    
    # 1. TENDENCIA (regresión lineal)
    ventas_diarias = df_prod.groupby('fecha')['venta_pesos'].sum().reset_index()
    if len(ventas_diarias) >= 5:
        x = np.arange(len(ventas_diarias))
        y = ventas_diarias['venta_pesos'].values
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        tendencia = slope
        r_squared = r_value ** 2
    else:
        tendencia = 0
        r_squared = 0
    
    # 2. VENTAS RECIENTES VS HISTÓRICO
    venta_prom_historico = ventas_total / dias_total
    venta_prom_reciente = ventas_recientes / max(dias_recientes, 1)
    caida_reciente = ((venta_prom_historico - venta_prom_reciente) / venta_prom_historico) * 100 if venta_prom_historico > 0 else 0
    
    # 3. VARIABILIDAD
    std_ventas = df_prod.groupby('fecha')['venta_pesos'].sum().std()
    mean_ventas = df_prod.groupby('fecha')['venta_pesos'].sum().mean()
    cv = (std_ventas / mean_ventas) * 100 if mean_ventas > 0 else 0
    
    # 4. FRECUENCIA DE VENTA
    dias_unicos_venta = df_prod['fecha'].nunique()
    dias_disponibles = df_filtrado['fecha'].nunique()
    frecuencia = (dias_unicos_venta / dias_disponibles) * 100
    
    # 5. DÍAS SIN VENTA (en período reciente)
    dias_sin_venta = umbral_dias - dias_recientes
    
    # CALCULAR SCORE DE RIESGO (0-100, mayor = más riesgo)
    score_riesgo = 0
    
    # Tendencia negativa (0-30 puntos)
    if tendencia < 0:
        score_riesgo += min(abs(tendencia) / 10000, 30)
    
    # Caída reciente (0-25 puntos)
    if caida_reciente > 0:
        score_riesgo += min(caida_reciente / 4, 25)
    
    # Alta variabilidad (0-20 puntos)
    if cv > 50:
        score_riesgo += min((cv - 50) / 5, 20)
    
    # Baja frecuencia (0-15 puntos)
    if frecuencia < 50:
        score_riesgo += min((50 - frecuencia) / 3.33, 15)
    
    # Días sin venta recientes (0-10 puntos)
    if dias_sin_venta > 0:
        score_riesgo += min(dias_sin_venta / 3, 10)
    
    productos_riesgo.append({
        'producto': producto,
        'ventas_total': ventas_total,
        'ventas_recientes': ventas_recientes,
        'venta_prom_historico': venta_prom_historico,
        'venta_prom_reciente': venta_prom_reciente,
        'caida_reciente_%': caida_reciente,
        'tendencia': tendencia,
        'r_squared': r_squared,
        'cv_%': cv,
        'frecuencia_%': frecuencia,
        'dias_sin_venta': dias_sin_venta,
        'score_riesgo': score_riesgo
    })

df_riesgo = pd.DataFrame(productos_riesgo).sort_values('score_riesgo', ascending=False)

# Clasificar nivel de riesgo
def clasificar_riesgo(score):
    if score >= 60:
        return 'Alto'
    elif score >= 30:
        return 'Medio'
    else:
        return 'Bajo'

df_riesgo['nivel_riesgo'] = df_riesgo['score_riesgo'].apply(clasificar_riesgo)

# ==========================================
# RESUMEN DE RIESGOS
# ==========================================

st.header("🚨 Resumen de Alertas")

riesgo_alto = len(df_riesgo[df_riesgo['nivel_riesgo'] == 'Alto'])
riesgo_medio = len(df_riesgo[df_riesgo['nivel_riesgo'] == 'Medio'])
riesgo_bajo = len(df_riesgo[df_riesgo['nivel_riesgo'] == 'Bajo'])

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class='risk-card' style='background: linear-gradient(135deg, #f5576c 0%, #c0392b 100%);'>
        <div style='font-size: 0.9rem; opacity: 0.9;'>🔴 Riesgo Alto</div>
        <div style='font-size: 3rem; font-weight: 800;'>{riesgo_alto}</div>
        <div style='font-size: 0.85rem; opacity: 0.8;'>Requieren atención inmediata</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='risk-card' style='background: linear-gradient(135deg, #FFD93D 0%, #f39c12 100%);'>
        <div style='font-size: 0.9rem; opacity: 0.9;'>🟡 Riesgo Medio</div>
        <div style='font-size: 3rem; font-weight: 800;'>{riesgo_medio}</div>
        <div style='font-size: 0.85rem; opacity: 0.8;'>Monitorear de cerca</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='risk-card' style='background: linear-gradient(135deg, #43e97b 0%, #27ae60 100%);'>
        <div style='font-size: 0.9rem; opacity: 0.9;'>🟢 Riesgo Bajo</div>
        <div style='font-size: 3rem; font-weight: 800;'>{riesgo_bajo}</div>
        <div style='font-size: 0.85rem; opacity: 0.8;'>Situación estable</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    ventas_en_riesgo = df_riesgo[df_riesgo['nivel_riesgo'] == 'Alto']['ventas_total'].sum()
    st.markdown(f"""
    <div class='risk-card' style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);'>
        <div style='font-size: 0.9rem; opacity: 0.9;'>💰 Ventas en Riesgo</div>
        <div style='font-size: 2rem; font-weight: 800;'>${ventas_en_riesgo/1e6:.1f}M</div>
        <div style='font-size: 0.85rem; opacity: 0.8;'>Productos de riesgo alto</div>
    </div>
    """, unsafe_allow_html=True)

# Alert si hay riesgos altos
if riesgo_alto > 0:
    st.markdown(f"""
    <div class='alert-box'>
        <strong>⚠️ ALERTA:</strong> Hay <strong>{riesgo_alto} productos</strong> con riesgo alto. 
        Se recomienda revisar estrategia de precios, disponibilidad o considerar remoción de carta.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# PRODUCTOS DE ALTO RIESGO (TOP 10)
# ==========================================

st.header("🔴 Top 10 Productos de Mayor Riesgo")

top_riesgo = df_riesgo.head(10)

# Gráfico
fig = go.Figure()

colors = ['#f5576c' if r == 'Alto' else '#FFD93D' if r == 'Medio' else '#43e97b' 
          for r in top_riesgo['nivel_riesgo']]

fig.add_trace(go.Bar(
    y=top_riesgo['producto'],
    x=top_riesgo['score_riesgo'],
    orientation='h',
    marker=dict(color=colors),
    text=[f'{s:.0f}' for s in top_riesgo['score_riesgo']],
    textposition='outside'
))

fig.update_layout(
    title='Score de Riesgo por Producto (0-100)',
    xaxis_title='Score de Riesgo',
    yaxis_title='',
    height=500,
    showlegend=False,
    yaxis={'categoryorder': 'total ascending'}
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ==========================================
# ANÁLISIS DETALLADO
# ==========================================

st.header("🔍 Análisis Detallado por Producto")

# Mostrar top 5 de mayor riesgo
for idx, (_, producto) in enumerate(top_riesgo.head(5).iterrows(), 1):
    
    nivel = producto['nivel_riesgo']
    color_nivel = '#f5576c' if nivel == 'Alto' else '#FFD93D' if nivel == 'Medio' else '#43e97b'
    emoji_nivel = '🔴' if nivel == 'Alto' else '🟡' if nivel == 'Medio' else '🟢'
    
    with st.expander(f"{emoji_nivel} #{idx} - {producto['producto']} (Score: {producto['score_riesgo']:.0f})", expanded=(idx == 1)):
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Evolución temporal
            df_prod = df_filtrado[df_filtrado['producto'] == producto['producto']]
            ventas_tiempo = df_prod.groupby('fecha')['venta_pesos'].sum().reset_index()
            
            fig = px.line(
                ventas_tiempo,
                x='fecha',
                y='venta_pesos',
                title='Evolución de Ventas',
                labels={'fecha': 'Fecha', 'venta_pesos': 'Ventas (COP)'}
            )
            
            # Línea de tendencia
            if len(ventas_tiempo) >= 5:
                x_num = np.arange(len(ventas_tiempo))
                y = ventas_tiempo['venta_pesos'].values
                z = np.polyfit(x_num, y, 1)
                p = np.poly1d(z)
                
                fig.add_trace(go.Scatter(
                    x=ventas_tiempo['fecha'],
                    y=p(x_num),
                    mode='lines',
                    name='Tendencia',
                    line=dict(dash='dash', color='red')
                ))
            
            fig.update_traces(line_color=color_nivel, line_width=2, selector=dict(mode='lines'))
            fig.update_layout(height=300, hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**⚠️ Indicadores de Riesgo**")
            
            # Score
            st.markdown(f"""
            <div style='background: {color_nivel}20; padding: 1rem; border-radius: 0.5rem; 
                        margin: 0.5rem 0; border-left: 4px solid {color_nivel};'>
                <div style='color: #666; font-size: 0.85rem;'>Score de Riesgo</div>
                <div style='font-size: 2rem; font-weight: 700; color: {color_nivel};'>
                    {producto['score_riesgo']:.0f}/100
                </div>
                <div style='color: #999; font-size: 0.8rem;'>Nivel: {nivel}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Caída reciente
            if producto['caida_reciente_%'] > 0:
                st.warning(f"📉 Caída reciente: -{producto['caida_reciente_%']:.1f}%")
            
            # Variabilidad
            if producto['cv_%'] > 50:
                st.warning(f"📊 Alta variabilidad: CV = {producto['cv_%']:.0f}%")
            
            # Frecuencia baja
            if producto['frecuencia_%'] < 50:
                st.warning(f"📅 Baja frecuencia: {producto['frecuencia_%']:.0f}%")
            
            # Días sin venta
            if producto['dias_sin_venta'] > 0:
                st.warning(f"⏰ {producto['dias_sin_venta']} días sin venta")
        
        # Métricas comparativas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Venta Prom Histórica",
                f"${producto['venta_prom_historico']:,.0f}",
                None
            )
        
        with col2:
            cambio = producto['venta_prom_reciente'] - producto['venta_prom_historico']
            st.metric(
                f"Venta Prom (últimos {umbral_dias}d)",
                f"${producto['venta_prom_reciente']:,.0f}",
                f"{cambio:+,.0f}"
            )
        
        with col3:
            st.metric(
                "Ventas Totales",
                f"${producto['ventas_total']:,.0f}",
                None
            )
        
        # Recomendaciones específicas
        st.markdown("**💡 Recomendaciones:**")
        
        recomendaciones = []
        
        if producto['score_riesgo'] >= 60:
            recomendaciones.append("🔴 **Crítico:** Evaluar rentabilidad y considerar descontinuar")
        
        if producto['caida_reciente_%'] > 30:
            recomendaciones.append("📉 Implementar promoción o descuento temporal")
        
        if producto['cv_%'] > 70:
            recomendaciones.append("📊 Revisar disponibilidad y consistencia en preparación")
        
        if producto['frecuencia_%'] < 30:
            recomendaciones.append("📅 Considerar cambio de posición en carta o combo")
        
        if producto['dias_sin_venta'] > 15:
            recomendaciones.append("⏰ Verificar disponibilidad de insumos")
        
        if not recomendaciones:
            recomendaciones.append("✅ Monitorear evolución en próximos 30 días")
        
        for rec in recomendaciones:
            st.markdown(f"- {rec}")

st.markdown("---")

# ==========================================
# MATRIZ DE RIESGO
# ==========================================

st.header("📊 Matriz de Riesgo: Caída vs Variabilidad")

fig = px.scatter(
    df_riesgo.head(30),
    x='cv_%',
    y='caida_reciente_%',
    size='ventas_total',
    color='nivel_riesgo',
    hover_name='producto',
    labels={
        'cv_%': 'Coeficiente de Variación (%)',
        'caida_reciente_%': 'Caída Reciente (%)',
        'nivel_riesgo': 'Nivel de Riesgo'
    },
    title='Productos por Caída Reciente vs Variabilidad',
    color_discrete_map={'Alto': '#f5576c', 'Medio': '#FFD93D', 'Bajo': '#43e97b'}
)

# Líneas de referencia
fig.add_hline(y=20, line_dash="dash", line_color="gray", annotation_text="Umbral caída 20%")
fig.add_vline(x=50, line_dash="dash", line_color="gray", annotation_text="Umbral CV 50%")

fig.update_layout(height=500)
st.plotly_chart(fig, use_container_width=True)

# ==========================================
# TABLA RESUMEN
# ==========================================

st.markdown("---")
st.header("📋 Tabla Resumen de Riesgos")

tabla_riesgo = df_riesgo[['producto', 'score_riesgo', 'nivel_riesgo', 'caida_reciente_%', 
                           'cv_%', 'frecuencia_%', 'ventas_total']].head(20)

st.dataframe(
    tabla_riesgo.style.format({
        'score_riesgo': '{:.0f}',
        'caida_reciente_%': '{:.1f}%',
        'cv_%': '{:.0f}%',
        'frecuencia_%': '{:.0f}%',
        'ventas_total': '${:,.0f}'
    }).background_gradient(subset=['score_riesgo'], cmap='Reds'),
    use_container_width=True,
    height=500
)
