# app.py
import streamlit as st
import pandas as pd
from utils.data_loader import cargar_datos

# ==========================================
# CONFIGURACIÓN
# ==========================================

st.set_page_config(
    page_title="Sistema de Gestión de Demanda",
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
        font-size: 4rem;
        font-weight: 900;
        background: linear-gradient(120deg, #FF6B6B 0%, #4ECDC4 50%, #FFD93D 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin: 2rem 0;
        animation: fadeIn 1s;
    }
    
    .subtitle {
        font-size: 1.5rem;
        color: #7f8c8d;
        text-align: center;
        margin-bottom: 3rem;
    }
    
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.3s, box-shadow 0.3s;
        height: 100%;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .feature-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
    
    .feature-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    
    .feature-desc {
        font-size: 1rem;
        color: #7f8c8d;
        line-height: 1.6;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR - INFO DEL SISTEMA
# ==========================================

df = cargar_datos()

with st.sidebar:
    st.title("🍽️ Sistema de Gestión")
    st.markdown("---")
    
    if df is not None:
        st.header("📊 Datos del Sistema")
        
        st.metric("Restaurantes", df['restaurante'].nunique())
        st.metric("Productos", df['producto'].nunique())
        st.metric("Período", f"{df['fecha'].min().date()} a {df['fecha'].max().date()}")
        
        st.markdown("---")
        
        st.info("""
        **💡 Navegación:**
        
        Usa el menú superior para acceder a:
        - 📊 **Dashboard:** Análisis operativo
        - 🎯 **Predictor:** IA para pronósticos
        """)
    
    st.markdown("---")
    st.caption("v1.0.0 | Barranquilla 2024")

# ==========================================
# CONTENIDO PRINCIPAL
# ==========================================

st.markdown("<h1 class='main-title'>🍽️ Sistema Inteligente de Gestión de Demanda</h1>", unsafe_allow_html=True)

st.markdown("""
<div class='subtitle'>
    Plataforma integral para análisis y predicción de ventas en restaurantes
</div>
""", unsafe_allow_html=True)

# ==========================================
# FEATURES
# ==========================================

st.markdown("## ✨ Funcionalidades")
st.markdown("")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class='feature-card'>
        <div class='feature-icon'>📊</div>
        <div class='feature-title'>Dashboard Operativo</div>
        <div class='feature-desc'>
            Visualiza el desempeño de tus restaurantes en tiempo real. 
            Analiza ventas, tendencias y KPIs clave para tomar decisiones informadas.
            <br><br>
            <b>Incluye:</b>
            <ul style='text-align: left; display: inline-block;'>
                <li>KPIs en tiempo real</li>
                <li>Comparativas por restaurante</li>
                <li>Análisis de tendencias</li>
                <li>Top productos</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    
    if st.button("📊 Ir al Dashboard", use_container_width=True, type="primary"):
        st.switch_page("pages/1_📊_Dashboard.py")

with col2:
    st.markdown("""
    <div class='feature-card'>
        <div class='feature-icon'>🎯</div>
        <div class='feature-title'>Predictor Inteligente</div>
        <div class='feature-desc'>
            Pronósticos precisos con Machine Learning (XGBoost). 
            Predice la demanda futura con intervalos de confianza y alertas automáticas.
            <br><br>
            <b>Incluye:</b>
            <ul style='text-align: left; display: inline-block;'>
                <li>Predicción hasta 60 días</li>
                <li>Intervalos de confianza 95%</li>
                <li>Alertas inteligentes</li>
                <li>Tuning automático</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    
    if st.button("🎯 Ir al Predictor", use_container_width=True, type="primary"):
        st.switch_page("pages/2_🎯_Predictor.py")

st.markdown("---")

# ==========================================
# ESTADÍSTICAS RÁPIDAS
# ==========================================

if df is not None:
    st.markdown("## 📈 Vista Rápida del Sistema")
    st.markdown("")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        ventas_totales = df['venta_pesos'].sum()
        st.metric(
            "💰 Ventas Totales",
            f"${ventas_totales/1e6:.1f}M",
            help="Ventas acumuladas en todo el período"
        )
    
    with col2:
        unidades_totales = df['cantidad_vendida_diaria'].sum()
        st.metric(
            "📦 Unidades Vendidas",
            f"{unidades_totales:,.0f}",
            help="Total de productos vendidos"
        )
    
    with col3:
        venta_promedio_dia = df.groupby('fecha')['venta_pesos'].sum().mean()
        st.metric(
            "📊 Venta Prom/Día",
            f"${venta_promedio_dia/1e3:.0f}K",
            help="Promedio de ventas diarias"
        )
    
    with col4:
        productos_activos = df['producto'].nunique()
        st.metric(
            "🍽️ Productos Activos",
            productos_activos,
            help="Cantidad de productos en catálogo"
        )
    
    st.markdown("---")
    
    # Distribución por restaurante
    st.markdown("### 🏪 Distribución por Restaurante")
    
    from utils.data_loader import get_restaurante_color
    
    col1, col2, col3 = st.columns(3)
    
    for idx, restaurante in enumerate(df['restaurante'].unique()):
        df_rest = df[df['restaurante'] == restaurante]
        ventas = df_rest['venta_pesos'].sum()
        unidades = df_rest['cantidad_vendida_diaria'].sum()
        color = get_restaurante_color(restaurante)
        
        with [col1, col2, col3][idx]:
            st.markdown(f"""
            <div style='
                background: {color}15; 
                padding: 1.5rem; 
                border-radius: 1rem; 
                border-left: 5px solid {color};
                text-align: center;
            '>
                <div style='font-size: 1.2rem; font-weight: 700; color: {color}; margin-bottom: 0.5rem;'>
                    {restaurante}
                </div>
                <div style='font-size: 1.8rem; font-weight: 700; color: #2c3e50; margin-bottom: 0.3rem;'>
                    ${ventas/1e6:.1f}M
                </div>
                <div style='font-size: 0.9rem; color: #7f8c8d;'>
                    {unidades:,.0f} unidades
                </div>
            </div>
            """, unsafe_allow_html=True)

else:
    st.warning("⚠️ No se pudieron cargar los datos del sistema")

st.markdown("---")

# ==========================================
# FOOTER
# ==========================================

st.markdown("""
<div style='text-align: center; color: #95a5a6; margin-top: 3rem; padding: 2rem;'>
    <p><b>Sistema de Gestión de Demanda</b></p>
    <p>Desarrollado con ❤️ usando Streamlit + XGBoost</p>
    <p>Barranquilla, Colombia • 2024</p>
</div>
""", unsafe_allow_html=True)
