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

# Imports
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

# Selección de restaurante
restaurante = st.sidebar.selectbox(
    "🏪 Restaurante",
    options=sorted(df_all['restaurante'].unique()),
    index=0
)

# Filtrar productos del restaurante
df_restaurante = df_all[df_all['restaurante'] == restaurante].copy()

# Usar descripcion_producto (columna correcta según tu dataset)
productos = sorted(df_restaurante['descripcion_producto'].dropna().unique())

# Selección de producto
producto_seleccionado = st.sidebar.selectbox(
    "📦 Producto",
    options=productos,
    format_func=lambda x: x[:50] + "..." if len(x) > 50 else x
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔧 Parámetros del Modelo")

# Horizonte
horizonte = st.sidebar.slider(
    "📅 Horizonte de predicción (días)",
    min_value=7,
    max_value=60,
    value=14,
    step=7,
    help="Número de días a predecir hacia el futuro"
)

# Trials de Optuna
n_trials = st.sidebar.slider(
    "🔬 Trials de optimización",
    min_value=5,
    max_value=50,
    value=20,
    step=5,
    help="Más trials = mejor modelo pero más lento (recomendado: 20)"
)

# Split
train_val_split = st.sidebar.slider(
    "📊 % datos para entrenamiento",
    min_value=60,
    max_value=90,
    value=80,
    step=5
)

st.sidebar.markdown("---")

# BOTÓN DE ENTRENAMIENTO (ESTO FALTABA)
entrenar = st.sidebar.button(
    "🚀 Entrenar y Predecir",
    type="primary",
    use_container_width=True
)

st.sidebar.markdown("---")
st.sidebar.info("""
💡 **Tips:**
- Más trials mejoran precisión
- 80% train es óptimo
- Horizontes cortos (7-14 días) son más precisos
""")

# ==========================================
# INFORMACIÓN DEL PRODUCTO
# ==========================================

# Filtrar datos del producto (usar descripcion_producto)
df_producto = df_restaurante[df_restaurante['descripcion_producto'] == producto_seleccionado].copy()
df_producto = df_producto.sort_values('fecha').reset_index(drop=True)

# Verificar columnas
if len(df_producto) == 0:
    st.warning(f"⚠️ No hay datos para {producto_seleccionado}")
    st.stop()

if 'cantidad_vendida_diaria' not in df_producto.columns:
    st.error("❌ Error: La columna 'cantidad_vendida_diaria' no existe")
    st.info(f"Columnas disponibles: {', '.join(df_producto.columns)}")
    st.stop()

# Métricas del producto
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📊 Días disponibles", len(df_producto))

with col2:
    promedio = df_producto['cantidad_vendida_diaria'].mean()
    st.metric("📈 Promedio diario", f"{promedio:.1f} un")

with col3:
    std = df_producto['cantidad_vendida_diaria'].std()
    st.metric("📉 Desviación estándar", f"{std:.1f}")

with col4:
    periodo = f"{df_producto['fecha'].min().strftime('%Y-%m')} / {df_producto['fecha'].max().strftime('%Y-%m')}"
    st.metric("🗓️ Periodo", periodo)

st.divider()

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
            progress_bar.progress(10)
            
            # Mostrar info inicial
            st.info(f"📊 **Datos originales:** {len(df_producto)} días")
            
            # Crear features
            df_features = create_all_features(df_producto)
            
            st.info(f"📊 **Después de crear features:** {len(df_features)} días")
            
            progress_bar.progress(20)
            
            # CAMBIO CRÍTICO: Dropna SOLO en columnas esenciales
            status_text.text("🧹 Limpiando datos...")
            
            # Verificar qué columnas existen
            essential_cols = ['cantidad_vendida_diaria']
            
            # Agregar lag_1 y lag_7 si existen
            if 'lag_1' in df_features.columns:
                essential_cols.append('lag_1')
            if 'lag_7' in df_features.columns:
                essential_cols.append('lag_7')
            
            st.write(f"🔍 Verificando columnas esenciales: {essential_cols}")
            
            # Contar NaN ANTES de limpiar
            nan_before = df_features[essential_cols].isna().sum()
            st.write("**NaN en columnas esenciales (antes):**")
            st.write(nan_before)
            
            # Dropna SOLO en columnas esenciales
            df_clean = df_features.dropna(subset=essential_cols).copy()
            
            st.info(f"📊 **Después de eliminar NaN en esenciales:** {len(df_clean)} días")
            
            progress_bar.progress(25)
            
            # Rellenar NaN en el resto de columnas
            status_text.text("🔄 Rellenando valores faltantes...")
            
            # Forward fill, luego backward fill, luego 0
            df_clean = df_clean.fillna(method='ffill').fillna(method='bfill').fillna(0)
            
            # Verificar que no queden NaN
            remaining_nan = df_clean.isna().sum().sum()
            st.success(f"✅ **Datos finales limpios:** {len(df_clean)} días (NaN restantes: {remaining_nan})")
            
            progress_bar.progress(30)
            
            # Verificar cantidad mínima
            if len(df_clean) < 50:
                st.error(f"❌ **Insuficientes datos después de limpieza**")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Días originales", len(df_producto))
                with col2:
                    st.metric("Días con features", len(df_features))
                with col3:
                    st.metric("Días finales", len(df_clean))
                
                with st.expander("🔍 Diagnóstico Detallado"):
                    st.write("**¿Dónde se perdieron los datos?**")
                    st.write(f"- Pérdida en feature engineering: {len(df_producto) - len(df_features)} días")
                    st.write(f"- Pérdida en limpieza de NaN: {len(df_features) - len(df_clean)} días")
                    
                    st.write("\n**Primeros 20 registros (con NaN):**")
                    st.dataframe(df_features[essential_cols].head(20))
                    
                    st.write("\n**Estadísticas de NaN por columna:**")
                    nan_stats = df_features.isna().sum().sort_values(ascending=False)
                    st.dataframe(nan_stats[nan_stats > 0])
                
                st.stop()
            
            df_features = df_clean
            
            # 2. Preparar features y target
            status_text.text("📊 Preparando features...")
            progress_bar.progress(35)
            
            feature_cols = get_feature_columns()
            
            # Verificar que existan
            feature_cols = [col for col in feature_cols if col in df_features.columns]
            
            st.info(f"🔧 **Features seleccionadas:** {len(feature_cols)}")
            
            # Asegurar que no hay NaN
            X = df_features[feature_cols].fillna(0)
            y = df_features['cantidad_vendida_diaria']
            
            st.success(f"✅ **X shape:** {X.shape}, **y shape:** {y.shape}")
            
            progress_bar.progress(40)
            
            # 3. Split temporal
            status_text.text("✂️ Dividiendo datos...")
            
            split_idx = int(len(X) * train_val_split / 100)
            
            X_train = X[:split_idx]
            y_train = y[:split_idx]
            X_test = X[split_idx:]
            y_test = y[split_idx:]
            
            st.info(f"📊 **Train:** {len(X_train)} días | **Test:** {len(X_test)} días")
            
            progress_bar.progress(45)
            
            # 4. Split interno para validación
            status_text.text("🔀 Creando conjunto de validación...")
            
            val_split = int(len(X_train) * 0.8)
            X_train_inner = X_train[:val_split]
            y_train_inner = y_train[:val_split]
            X_val = X_train[val_split:]
            y_val = y_train[val_split:]
            
            st.info(f"📊 **Train interno:** {len(X_train_inner)} | **Val:** {len(X_val)}")
            
            progress_bar.progress(50)
            
            # 5. Entrenar modelo
            status_text.text(f"🤖 Entrenando XGBoost ({n_trials} trials)...")
            
            predictor = XGBoostPredictor(n_trials=n_trials, confidence_level=0.95)
            predictor.train(X_train_inner, y_train_inner, X_val, y_val)
            
            st.success("✅ **Modelo principal entrenado**")
            
            progress_bar.progress(70)
            
            # 6. Predecir en test
            status_text.text("🎯 Evaluando en test...")
            
            y_pred_test, y_pred_test_lower, y_pred_test_upper = predictor.predict(X_test, return_intervals=True)
            
            progress_bar.progress(80)
            
            # 7. Preparar predicción futura
            status_text.text("🔮 Preparando predicción futura...")
            
            last_date = df_producto['fecha'].max()
            future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=horizonte, freq='D')
            
            # Crear dataframe futuro
            df_future = pd.DataFrame({
                'fecha': future_dates,
                'cantidad_vendida_diaria': df_producto['cantidad_vendida_diaria'].tail(30).mean()
            })
            
            # Aplicar feature engineering
            df_future = create_all_features(df_future)
            
            # Asegurar que tenga todas las features
            for col in feature_cols:
                if col not in df_future.columns:
                    df_future[col] = 0
            
            # Rellenar NaN
            df_future = df_future.fillna(method='ffill').fillna(method='bfill').fillna(0)
            
            X_future = df_future[feature_cols].fillna(0)
            
            progress_bar.progress(85)
            
            # 8. Predecir futuro
            status_text.text("🎯 Generando predicciones futuras...")
            
            y_pred_future, y_pred_future_lower, y_pred_future_upper = predictor.predict(
                X_future[:horizonte], 
                return_intervals=True
            )
            
            progress_bar.progress(90)
            
            # 9. Calcular métricas
            status_text.text("📊 Calculando métricas...")
            
            metrics = calculate_metrics(y_test.values, y_pred_test)
            
            progress_bar.progress(95)
            
            # 10. Generar alertas
            status_text.text("🚨 Generando alertas...")
            
            historical_mean = df_producto['cantidad_vendida_diaria'].mean()
            historical_std = df_producto['cantidad_vendida_diaria'].std()
            
            alerts = generate_alerts(
                y_pred_future, 
                y_pred_future_lower, 
                y_pred_future_upper, 
                historical_mean, 
                historical_std
            )
            
            progress_bar.progress(100)
            status_text.text("✅ ¡Completado!")
            
            # 11. Guardar en session_state
            st.session_state.update({
                'predictor': predictor,
                'metrics': metrics,
                'y_test': y_test,
                'y_pred_test': y_pred_test,
                'y_pred_test_lower': y_pred_test_lower,
                'y_pred_test_upper': y_pred_test_upper,
                'df_test': df_features[split_idx:].copy(),
                'future_dates': future_dates,
                'y_pred_future': y_pred_future,
                'y_pred_future_lower': y_pred_future_lower,
                'y_pred_future_upper': y_pred_future_upper,
                'df_producto': df_producto,
                'alerts': alerts,
                'producto_nombre': producto_seleccionado
            })
            
            progress_bar.empty()
            status_text.empty()
            
            st.success("✅ **¡Modelo entrenado exitosamente!**")
            st.balloons()
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ **Error durante el entrenamiento:** {str(e)}")
            import traceback
            with st.expander("🔍 Ver detalles técnicos del error"):
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
    producto_nombre = st.session_state.get('producto_nombre', producto_seleccionado)
    
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
    
    # Intervalo superior
    fig.add_trace(go.Scatter(
        x=future_dates,
        y=y_pred_future_upper,
        mode='lines',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Intervalo inferior (con relleno)
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
    
    # Línea divisoria "Hoy" (CORREGIDA)
    last_historical_date = pd.Timestamp(df_producto['fecha'].max())
    
    fig.add_shape(
        type="line",
        x0=last_historical_date,
        x1=last_historical_date,
        y0=0,
        y1=1,
        yref="paper",
        line=dict(color="red", width=2, dash="dot")
    )
    
    # Agregar anotación "Hoy"
    fig.add_annotation(
        x=last_historical_date,
        y=1.05,
        yref="paper",
        text="Hoy",
        showarrow=False,
        font=dict(color="red", size=12)
    )
    
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Cantidad (unidades)",
        hovermode='x unified',
        template='plotly_white',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ... resto del código del tab1
    
    with tab2:
        st.subheader("Evaluación en Test")
        
        y_test = st.session_state['y_test']
        y_pred_test = st.session_state['y_pred_test']
        df_test = st.session_state['df_test']
        
        col1, col2 = st.columns(2)
        
        with col1:
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
                height=400,
                title="Real vs Predicho"
            )
            
            st.plotly_chart(fig_test, use_container_width=True)
        
        with col2:
            # Scatter
            fig_scatter = go.Figure()
            
            fig_scatter.add_trace(go.Scatter(
                x=y_test,
                y=y_pred_test,
                mode='markers',
                marker=dict(size=8, opacity=0.6)
            ))
            
            # Línea perfecta
            max_val = max(y_test.max(), y_pred_test.max())
            fig_scatter.add_trace(go.Scatter(
                x=[0, max_val],
                y=[0, max_val],
                mode='lines',
                line=dict(color='red', dash='dash'),
                name='Predicción Perfecta'
            ))
            
            fig_scatter.update_layout(
                xaxis_title="Real",
                yaxis_title="Predicho",
                template='plotly_white',
                height=400,
                title="Correlación"
            )
            
            st.plotly_chart(fig_scatter, use_container_width=True)
        
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
            orientation='h',
            marker=dict(color='#1f77b4')
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
            'producto': producto_nombre,
            'prediccion': y_pred_future.round(2),
            'limite_inferior': y_pred_future_lower.round(2),
            'limite_superior': y_pred_future_upper.round(2)
        })
        
        csv = df_download.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            "📥 Descargar CSV",
            csv,
            f"prediccion_{producto_nombre[:20].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            use_container_width=True
        )
        
        st.markdown("### 📊 Preview de Datos")
        st.dataframe(df_download, use_container_width=True)

else:
    st.info("👈 Configura los parámetros en el sidebar y presiona **'Entrenar y Predecir'** para comenzar")
