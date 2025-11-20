"""
Predictor Inteligente - XGBoost con Intervalos de Confianza
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Imports de tu estructura
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.data_loader import cargar_datos
from utils.feature_engineering import create_all_features, get_feature_columns
from utils.model_trainer import XGBoostPredictor, calculate_metrics, generate_alerts

# ==========================================
# CONFIGURACIÓN
# ==========================================

st.set_page_config(
    page_title="Predictor Inteligente",
    page_icon="🎯",
    layout="wide"
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
    
    .alert-warning {
        background: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .alert-info {
        background: #d1ecf1;
        border-left: 5px solid #17a2b8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .alert-success {
        background: #d4edda;
        border-left: 5px solid #28a745;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CARGAR DATOS
# ==========================================

@st.cache_data
def load_data():
    """Cargar datos consolidados"""
    return cargar_datos()

df_all = load_data()

if df_all is None:
    st.error("❌ No se pudieron cargar los datos")
    st.stop()

# ==========================================
# HEADER
# ==========================================

st.markdown("<h1 class='main-title'>🎯 Predictor Inteligente de Demanda</h1>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; font-size: 1.2rem; color: #7f8c8d; margin-bottom: 2rem;'>
    Predicción con XGBoost + Intervalos de Confianza + Alertas Automáticas
</div>
""", unsafe_allow_html=True)

st.divider()

# ==========================================
# SIDEBAR - CONFIGURACIÓN
# ==========================================

st.sidebar.header("⚙️ Configuración del Predictor")

# Verificar columnas disponibles
columnas_posibles = ['producto', 'descripcion_producto', 'nombre_producto', 'codigo_producto']
columna_producto = None

for col in columnas_posibles:
    if col in df_all.columns:
        columna_producto = col
        break

if columna_producto is None:
    st.error("❌ No se encontró una columna de productos")
    st.info(f"Columnas disponibles: {', '.join(df_all.columns)}")
    st.stop()

# Selección de restaurante
restaurante = st.sidebar.selectbox(
    "🏪 Restaurante",
    options=sorted(df_all['restaurante'].unique()),
    index=0
)

# Filtrar productos del restaurante
df_restaurante = df_all[df_all['restaurante'] == restaurante].copy()

# Obtener productos únicos y limpios
productos_raw = df_restaurante[columna_producto].dropna().unique()
productos = sorted([str(p) for p in productos_raw])

if len(productos) == 0:
    st.error(f"❌ No hay productos para {restaurante}")
    st.stop()

# Selección de producto
producto_seleccionado = st.sidebar.selectbox(
    "📦 Producto",
    options=productos,
    format_func=lambda x: x[:50] + "..." if len(x) > 50 else x
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔧 Parámetros del Modelo")

# ... resto del código

# ==========================================
# INFORMACIÓN DEL PRODUCTO
# ==========================================

# Filtrar datos del producto usando la columna correcta
df_producto = df_restaurante[df_restaurante[columna_producto] == producto_seleccionado].copy()
df_producto = df_producto.sort_values('fecha').reset_index(drop=True)

# Verificar que tenga columna correcta
if 'cantidad_vendida_diaria' not in df_producto.columns:
    st.error("❌ Error: La columna 'cantidad_vendida_diaria' no existe")
    st.info(f"Columnas disponibles: {', '.join(df_producto.columns)}")
    st.stop()

if len(df_producto) == 0:
    st.warning(f"⚠️ No hay datos para {producto_seleccionado}")
    st.stop()

# ==========================================
# GRÁFICO HISTÓRICO
# ==========================================

st.subheader("📈 Histórico de Ventas")

fig_historico = go.Figure()

fig_historico.add_trace(go.Scatter(
    x=df_producto['fecha'],
    y=df_producto['cantidad_vendida_diaria'],
    mode='lines+markers',
    name='Ventas Reales',
    line=dict(color='#1f77b4', width=2),
    marker=dict(size=4)
))

fig_historico.update_layout(
    xaxis_title="Fecha",
    yaxis_title="Cantidad (unidades)",
    hovermode='x unified',
    template='plotly_white',
    height=400
)

st.plotly_chart(fig_historico, use_container_width=True)

st.divider()

# ==========================================
# ENTRENAMIENTO Y PREDICCIÓN
# ==========================================

if entrenar:
    
    with st.spinner("🔄 Entrenando modelo..."):
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 1. Feature Engineering
            status_text.text("🔧 Creando features...")
            progress_bar.progress(20)
            
            df_features = create_all_features(df_producto)
            df_features = df_features.dropna()
            
            if len(df_features) < 50:
                st.error("❌ No hay suficientes datos (mínimo 50 días)")
                st.stop()
            
            # 2. Split
            status_text.text("📊 Dividiendo datos...")
            progress_bar.progress(30)
            
            split_idx = int(len(df_features) * train_val_split / 100)
            df_train = df_features[:split_idx].copy()
            df_test = df_features[split_idx:].copy()
            
            # Features
            feature_cols = get_feature_columns()
            feature_cols = [col for col in feature_cols if col in df_train.columns]
            
            X_train = df_train[feature_cols].fillna(0)
            y_train = df_train['cantidad_vendida_diaria']
            X_test = df_test[feature_cols].fillna(0)
            y_test = df_test['cantidad_vendida_diaria']
            
            # 3. Entrenar
            status_text.text(f"🤖 Entrenando XGBoost ({n_trials} trials)...")
            progress_bar.progress(40)
            
            # Split interno
            val_split = int(len(X_train) * 0.8)
            X_train_inner = X_train[:val_split]
            y_train_inner = y_train[:val_split]
            X_val = X_train[val_split:]
            y_val = y_train[val_split:]
            
            predictor = XGBoostPredictor(n_trials=n_trials, confidence_level=0.95)
            predictor.train(X_train_inner, y_train_inner, X_val, y_val)
            
            progress_bar.progress(70)
            
            # 4. Predecir en test
            status_text.text("🎯 Evaluando...")
            y_pred_test, y_pred_test_lower, y_pred_test_upper = predictor.predict(X_test, return_intervals=True)
            
            progress_bar.progress(80)
            
            # 5. Predicción futura
            status_text.text("🔮 Prediciendo futuro...")
            
            last_date = df_producto['fecha'].max()
            future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=horizonte, freq='D')
            
            df_future = pd.DataFrame({'fecha': future_dates})
            df_future['cantidad_vendida_diaria'] = df_producto['cantidad_vendida_diaria'].tail(30).mean()
            df_future = create_all_features(df_future)
            
            X_future = df_future[feature_cols].fillna(method='ffill').fillna(0)
            y_pred_future, y_pred_future_lower, y_pred_future_upper = predictor.predict(X_future[:horizonte], return_intervals=True)
            
            progress_bar.progress(90)
            
            # 6. Métricas
            metrics = calculate_metrics(y_test.values, y_pred_test)
            
            # 7. Alertas
            historical_mean = df_producto['cantidad_vendida_diaria'].mean()
            historical_std = df_producto['cantidad_vendida_diaria'].std()
            alerts = generate_alerts(y_pred_future, y_pred_future_lower, y_pred_future_upper, historical_mean, historical_std)
            
            progress_bar.progress(100)
            status_text.text("✅ ¡Completado!")
            
            # Guardar en session_state
            st.session_state.update({
                'predictor': predictor,
                'metrics': metrics,
                'y_test': y_test,
                'y_pred_test': y_pred_test,
                'y_pred_test_lower': y_pred_test_lower,
                'y_pred_test_upper': y_pred_test_upper,
                'df_test': df_test,
                'future_dates': future_dates,
                'y_pred_future': y_pred_future,
                'y_pred_future_lower': y_pred_future_lower,
                'y_pred_future_upper': y_pred_future_upper,
                'df_producto': df_producto,
                'alerts': alerts
            })
            
            progress_bar.empty()
            status_text.empty()
            
            st.success("✅ ¡Modelo entrenado exitosamente!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            with st.expander("Ver detalles del error"):
                st.code(traceback.format_exc())

# ==========================================
# MOSTRAR RESULTADOS
# ==========================================

if 'predictor' in st.session_state:
    
    # Extraer datos
    predictor = st.session_state['predictor']
    metrics = st.session_state['metrics']
    alerts = st.session_state['alerts']
    future_dates = st.session_state['future_dates']
    y_pred_future = st.session_state['y_pred_future']
    y_pred_future_lower = st.session_state['y_pred_future_lower']
    y_pred_future_upper = st.session_state['y_pred_future_upper']
    df_producto = st.session_state['df_producto']
    
    st.divider()
    
    # ==========================================
    # ALERTAS
    # ==========================================
    
    if alerts:
        st.subheader("🚨 Alertas Inteligentes")
        
        for alert in alerts:
            if alert['type'] == 'warning':
                st.markdown(f"""
                <div class='alert-warning'>
                    <strong>{alert['icon']} {alert['title']}</strong><br>
                    {alert['message']}
                </div>
                """, unsafe_allow_html=True)
            elif alert['type'] == 'success':
                st.markdown(f"""
                <div class='alert-success'>
                    <strong>{alert['icon']} {alert['title']}</strong><br>
                    {alert['message']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class='alert-info'>
                    <strong>{alert['icon']} {alert['title']}</strong><br>
                    {alert['message']}
                </div>
                """, unsafe_allow_html=True)
        
        st.divider()
    
    # ==========================================
    # MÉTRICAS
    # ==========================================
    
    st.subheader("📊 Métricas del Modelo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("MAE", f"{metrics['MAE']:.2f}", help="Error Absoluto Medio")
    with col2:
        st.metric("RMSE", f"{metrics['RMSE']:.2f}", help="Raíz del Error Cuadrático Medio")
    with col3:
        st.metric("MAPE", f"{metrics['MAPE']:.1f}%", help="Error Porcentual Absoluto Medio")
    with col4:
        precision = 100 - metrics['MAPE']
        st.metric("Precisión", f"{precision:.1f}%")
    
    st.divider()
    
    # ==========================================
    # TABS
    # ==========================================
    
    tab1, tab2, tab3 = st.tabs(["📈 Predicción", "🎯 Evaluación", "📋 Datos"])
    
    with tab1:
        st.subheader("Predicción Futura con Intervalos de Confianza (95%)")
        
        # Gráfico
        fig = go.Figure()
        
        # Histórico
        fig.add_trace(go.Scatter(
            x=df_producto['fecha'],
            y=df_producto['cantidad_vendida_diaria'],
            mode='lines',
            name='Histórico',
            line=dict(color='#1f77b4', width=2),
            opacity=0.7
        ))
        
        # Intervalo
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=y_pred_future_upper,
            mode='lines',
            line=dict(width=0),
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=y_pred_future_lower,
            mode='lines',
            name='Intervalo 95%',
            line=dict(width=0),
            fillcolor='rgba(255, 127, 14, 0.2)',
            fill='tonexty'
        ))
        
        # Predicción
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=y_pred_future,
            mode='lines+markers',
            name='Predicción',
            line=dict(color='#ff7f0e', width=3),
            marker=dict(size=8)
        ))
        
        # Línea hoy
        fig.add_vline(
            x=df_producto['fecha'].max(),
            line_dash="dot",
            line_color="red",
            annotation_text="Hoy"
        )
        
        fig.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Cantidad (unidades)",
            hovermode='x unified',
            template='plotly_white',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla
        st.markdown("### 📋 Predicciones Detalladas")
        
        interval_width = y_pred_future_upper - y_pred_future_lower
        
        df_table = pd.DataFrame({
            'Fecha': future_dates,
            'Día': future_dates.strftime('%A'),
            'Pesimista': y_pred_future_lower.round(1),
            'Predicción': y_pred_future.round(1),
            'Optimista': y_pred_future_upper.round(1),
            'Incertidumbre': interval_width.round(1)
        })
        
        st.dataframe(df_table, use_container_width=True, hide_index=True)
    
    with tab2:
        st.subheader("Evaluación en Test")
        
        y_test = st.session_state['y_test']
        y_pred_test = st.session_state['y_pred_test']
        df_test = st.session_state['df_test']
        
        # Gráfico test
        fig_test = go.Figure()
        
        fig_test.add_trace(go.Scatter(
            x=df_test['fecha'],
            y=y_test,
            mode='lines+markers',
            name='Real',
            line=dict(color='#1f77b4')
        ))
        
        fig_test.add_trace(go.Scatter(
            x=df_test['fecha'],
            y=y_pred_test,
            mode='lines+markers',
            name='Predicho',
            line=dict(color='#ff7f0e')
        ))
        
        fig_test.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Cantidad",
            hovermode='x unified',
            template='plotly_white',
            height=400
        )
        
        st.plotly_chart(fig_test, use_container_width=True)
        
        # Feature importance
        st.markdown("### 🔍 Features Más Importantes")
        
        importance_df = pd.DataFrame({
            'Feature': predictor.feature_names,
            'Importancia': predictor.model.feature_importances_
        }).sort_values('Importancia', ascending=False).head(10)
        
        fig_imp = go.Figure()
        fig_imp.add_trace(go.Bar(
            y=importance_df['Feature'],
            x=importance_df['Importancia'],
            orientation='h'
        ))
        fig_imp.update_layout(
            xaxis_title="Importancia",
            template='plotly_white',
            height=400
        )
        
        st.plotly_chart(fig_imp, use_container_width=True)
    
    with tab3:
        st.subheader("📥 Descargar Predicciones")
        
        # CSV
        df_download = pd.DataFrame({
            'fecha': future_dates,
            'prediccion': y_pred_future.round(2),
            'limite_inferior': y_pred_future_lower.round(2),
            'limite_superior': y_pred_future_upper.round(2)
        })
        
        csv = df_download.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            "📥 Descargar CSV",
            csv,
            f"prediccion_{producto_seleccionado[:20]}_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            use_container_width=True
        )

else:
    st.info("👈 Configura los parámetros en el sidebar y presiona **'Entrenar y Predecir'**")
