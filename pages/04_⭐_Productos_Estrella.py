# pages/04_⭐_Productos_Estrella.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.data_loader import cargar_datos, get_restaurante_color
from utils.metrics import calcular_top_productos

st.set_page_config(page_title="Productos Estrella", page_icon="⭐", layout="wide")

# ==========================================
# ESTILOS
# ==========================================

st.markdown("""
<style>
    .star-card {
        background: linear-gradient(135deg, #FFD93D 0%, #FF6B6B 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        text-align: center;
        margin: 0.5rem 0;
    }
    .star-value {
        font-size: 2rem;
        font-weight: 800;
    }
    .star-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .product-card {
        background: white;
        padding: 1.5rem;
        border-radius: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 5px solid #FFD93D;
    }
    .metric-row {
        display: flex;
        justify-content: space-between;
        margin: 0.5rem 0;
        padding: 0.5rem;
        background: #f8f9fa;
        border-radius: 0.5rem;
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

st.title("⭐ Productos Estrella - Top Performers")
st.markdown("Análisis de los productos con mejor desempeño en ventas, consistencia y crecimiento")
st.markdown("---")

col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    años = ['Todos'] + sorted(df['año'].unique().tolist(), reverse=True)
    año_sel = st.selectbox("📅 Año", años, index=0)

with col2:
    restaurantes = ['Todos'] + sorted(df['restaurante'].unique().tolist())
    restaurante_sel = st.selectbox("🏪 Restaurante", restaurantes, index=0)

with col3:
    top_n = st.selectbox("🔢 Top N", [5, 10, 15, 20], index=1)

st.markdown("---")

# FILTRAR DATOS
df_filtrado = df.copy()

if año_sel != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['año'] == int(año_sel)]

if restaurante_sel != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['restaurante'] == restaurante_sel]
    color_principal = get_restaurante_color(restaurante_sel)
else:
    color_principal = '#FFD93D'

if len(df_filtrado) == 0:
    st.warning("No hay datos para los filtros seleccionados")
    st.stop()

# ==========================================
# CALCULAR MÉTRICAS DE PRODUCTOS
# ==========================================

# Agrupar por producto
productos_metricas = df_filtrado.groupby('producto').agg({
    'venta_pesos': ['sum', 'mean', 'std'],
    'cantidad_vendida_diaria': ['sum', 'mean'],
    'fecha': 'count'
}).reset_index()

productos_metricas.columns = ['producto', 'ventas_totales', 'venta_promedio', 'venta_std', 
                               'unidades_totales', 'unidad_promedio', 'dias_venta']

# Calcular métricas adicionales
productos_metricas['ticket_promedio'] = productos_metricas['ventas_totales'] / productos_metricas['unidades_totales']
productos_metricas['consistencia'] = 1 / (1 + productos_metricas['venta_std'])
productos_metricas['frecuencia'] = productos_metricas['dias_venta'] / df_filtrado['fecha'].nunique()

# Score compuesto (ventas + consistencia + frecuencia)
productos_metricas['score'] = (
    (productos_metricas['ventas_totales'] / productos_metricas['ventas_totales'].max()) * 40 +
    (productos_metricas['consistencia'] / productos_metricas['consistencia'].max()) * 30 +
    (productos_metricas['frecuencia'] / productos_metricas['frecuencia'].max()) * 30
)

# Top N productos
top_productos = productos_metricas.nlargest(top_n, 'score')

# ==========================================
# RESUMEN EJECUTIVO
# ==========================================

st.header("📊 Resumen Ejecutivo")

col1, col2, col3, col4 = st.columns(4)

with col1:
    ventas_top = top_productos['ventas_totales'].sum()
    st.markdown(f"""
    <div class='star-card' style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);'>
        <div class='star-label'>💰 Ventas Top {top_n}</div>
        <div class='star-value'>${ventas_top/1e6:.1f}M</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    participacion = (ventas_top / df_filtrado['venta_pesos'].sum()) * 100
    st.markdown(f"""
    <div class='star-card' style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);'>
        <div class='star-label'>📈 % del Total</div>
        <div class='star-value'>{participacion:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    unidades_top = top_productos['unidades_totales'].sum()
    st.markdown(f"""
    <div class='star-card' style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);'>
        <div class='star-label'>📦 Unidades</div>
        <div class='star-value'>{unidades_top:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    ticket_prom_top = top_productos['ticket_promedio'].mean()
    st.markdown(f"""
    <div class='star-card' style='background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);'>
        <div class='star-label'>🎫 Ticket Prom</div>
        <div class='star-value'>${ticket_prom_top/1e3:.0f}K</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# RANKING DE PRODUCTOS
# ==========================================

st.header(f"🏆 Top {top_n} Productos Estrella")

# Gráfico principal
fig = go.Figure()

fig.add_trace(go.Bar(
    y=top_productos['producto'],
    x=top_productos['ventas_totales'],
    orientation='h',
    marker=dict(
        color=top_productos['score'],
        colorscale='Viridis',
        showscale=True,
        colorbar=dict(title="Score")
    ),
    text=[f'${v/1e6:.1f}M' for v in top_productos['ventas_totales']],
    textposition='outside',
    hovertemplate='<b>%{y}</b><br>Ventas: $%{x:,.0f}<extra></extra>'
))

fig.update_layout(
    title=f'Top {top_n} por Ventas Totales',
    xaxis_title='Ventas (COP)',
    yaxis_title='',
    height=max(400, top_n * 40),
    showlegend=False,
    yaxis={'categoryorder': 'total ascending'}
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================
# ANÁLISIS MULTIDIMENSIONAL
# ==========================================

st.markdown("---")
st.header("📊 Análisis Multidimensional")

# Scatter plot: Ventas vs Frecuencia
fig = px.scatter(
    top_productos,
    x='frecuencia',
    y='ventas_totales',
    size='unidades_totales',
    color='score',
    hover_name='producto',
    labels={
        'frecuencia': 'Frecuencia de Venta (% días)',
        'ventas_totales': 'Ventas Totales (COP)',
        'score': 'Score'
    },
    title='Ventas vs Frecuencia (tamaño = unidades)',
    color_continuous_scale='Viridis'
)

fig.update_traces(marker=dict(line=dict(width=2, color='white')))
fig.update_layout(height=500)
st.plotly_chart(fig, use_container_width=True)

# Insight
productos_alto_valor = top_productos[top_productos['ticket_promedio'] > top_productos['ticket_promedio'].median()]
st.info(f"""
💡 **Insight:** {len(productos_alto_valor)} de los top {top_n} productos tienen ticket promedio 
superior a ${top_productos['ticket_promedio'].median():,.0f}. Estos son productos **premium** 
que generan alto valor por venta.
""")

st.markdown("---")

# ==========================================
# DETALLE POR PRODUCTO (TOP 5)
# ==========================================

st.header("🔍 Análisis Detallado - Top 5")

for idx, (_, producto) in enumerate(top_productos.head(5).iterrows(), 1):
    
    # Datos del producto
    df_producto = df_filtrado[df_filtrado['producto'] == producto['producto']]
    
    with st.expander(f"{'🥇' if idx == 1 else '🥈' if idx == 2 else '🥉' if idx == 3 else '⭐'} #{idx} - {producto['producto']}", expanded=(idx <= 2)):
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Evolución temporal
            ventas_tiempo = df_producto.groupby('fecha')['venta_pesos'].sum().reset_index()
            
            fig = px.line(
                ventas_tiempo,
                x='fecha',
                y='venta_pesos',
                title=f'Evolución de Ventas',
                labels={'fecha': 'Fecha', 'venta_pesos': 'Ventas (COP)'}
            )
            
            # Línea de promedio
            promedio = ventas_tiempo['venta_pesos'].mean()
            fig.add_hline(
                y=promedio,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Promedio: ${promedio:,.0f}"
            )
            
            fig.update_traces(line_color=color_principal, line_width=2)
            fig.update_layout(height=300, hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Métricas clave
            st.markdown("**📊 Métricas Clave**")
            
            st.markdown(f"""
            <div style='background: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;'>
                <div style='color: #666; font-size: 0.85rem;'>💰 Ventas Totales</div>
                <div style='font-size: 1.5rem; font-weight: 700; color: {color_principal};'>
                    ${producto['ventas_totales']:,.0f}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='background: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;'>
                <div style='color: #666; font-size: 0.85rem;'>📦 Unidades Vendidas</div>
                <div style='font-size: 1.5rem; font-weight: 700;'>{producto['unidades_totales']:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='background: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;'>
                <div style='color: #666; font-size: 0.85rem;'>🎫 Ticket Promedio</div>
                <div style='font-size: 1.5rem; font-weight: 700;'>${producto['ticket_promedio']:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='background: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;'>
                <div style='color: #666; font-size: 0.85rem;'>📅 Frecuencia</div>
                <div style='font-size: 1.5rem; font-weight: 700;'>{producto['frecuencia']*100:.0f}%</div>
                <div style='color: #999; font-size: 0.75rem;'>{producto['dias_venta']} días</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Distribución por día de semana
        col1, col2 = st.columns(2)
        
        with col1:
            ventas_dia_semana = df_producto.groupby('dia_semana')['venta_pesos'].sum()
            dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            ventas_dia_semana = ventas_dia_semana.reindex(dias_orden, fill_value=0)
            
            dias_esp = {
                'Monday': 'Lun', 'Tuesday': 'Mar', 'Wednesday': 'Mié',
                'Thursday': 'Jue', 'Friday': 'Vie', 'Saturday': 'Sáb', 'Sunday': 'Dom'
            }
            ventas_dia_semana.index = [dias_esp[d] for d in ventas_dia_semana.index]
            
            fig = px.bar(
                x=ventas_dia_semana.index,
                y=ventas_dia_semana.values,
                title='Ventas por Día Semana',
                labels={'x': '', 'y': 'Ventas (COP)'},
                color=ventas_dia_semana.values,
                color_continuous_scale='Viridis'
            )
            fig.update_layout(height=250, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Por restaurante (si aplica)
            if restaurante_sel == 'Todos':
                ventas_rest = df_producto.groupby('restaurante')['venta_pesos'].sum()
                
                fig = px.pie(
                    values=ventas_rest.values,
                    names=ventas_rest.index,
                    title='Distribución por Restaurante',
                    color=ventas_rest.index,
                    color_discrete_map={r: get_restaurante_color(r) for r in ventas_rest.index}
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=250, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                # Si es un solo restaurante, mostrar distribución mensual
                ventas_mes = df_producto.groupby('mes')['venta_pesos'].sum().sort_index()
                
                fig = px.bar(
                    x=ventas_mes.index,
                    y=ventas_mes.values,
                    title='Ventas por Mes',
                    labels={'x': 'Mes', 'y': 'Ventas (COP)'}
                )
                fig.update_layout(height=250, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ==========================================
# RECOMENDACIONES
# ==========================================

st.header("💡 Recomendaciones Estratégicas")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div style='background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); 
                color: white; padding: 1.5rem; border-radius: 1rem;'>
        <h3>✅ Acciones Recomendadas</h3>
        <ul>
            <li>Asegurar disponibilidad constante de productos estrella</li>
            <li>Considerar promociones en días de menor venta</li>
            <li>Destacar estos productos en carta y menús</li>
            <li>Capacitar staff en upselling de productos top</li>
            <li>Analizar márgenes para optimizar rentabilidad</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # Producto con mayor potencial
    producto_potencial = top_productos.iloc[0]
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 1.5rem; border-radius: 1rem;'>
        <h3>🎯 Producto Estrella #1</h3>
        <h2>{producto_potencial['producto']}</h2>
        <div style='font-size: 1.5rem; margin: 1rem 0;'>
            ${producto_potencial['ventas_totales']:,.0f}
        </div>
        <div style='opacity: 0.9;'>
            • {producto_potencial['unidades_totales']:.0f} unidades vendidas<br>
            • Score: {producto_potencial['score']:.1f}/100<br>
            • Frecuencia: {producto_potencial['frecuencia']*100:.0f}% días
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# TABLA RESUMEN
# ==========================================

st.markdown("---")
st.header("📋 Tabla Resumen Completa")

tabla_resumen = top_productos[['producto', 'ventas_totales', 'unidades_totales', 
                                 'ticket_promedio', 'frecuencia', 'score']].copy()
tabla_resumen['frecuencia'] = tabla_resumen['frecuencia'] * 100

st.dataframe(
    tabla_resumen.style.format({
        'ventas_totales': '${:,.0f}',
        'unidades_totales': '{:,.0f}',
        'ticket_promedio': '${:,.0f}',
        'frecuencia': '{:.0f}%',
        'score': '{:.1f}'
    }).background_gradient(subset=['score'], cmap='Greens'),
    use_container_width=True,
    height=400
)
