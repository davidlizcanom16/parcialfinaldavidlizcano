"""
Predictor Inteligente - Pestaña de Dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Agregar path para imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.data_loader import load_all_data
from utils.feature_engineering import create_all_features, get_feature_columns
from utils.model_trainer import XGBoostPredictor, calculate_metrics

# Configuración de página
st.set_page_config(
    page_title="Predictor Inteligente",
    page_icon="🎯",
    layout="wide"
)

# Título
st.title("🎯 Predictor Inteligente de Demanda")
st.markdown("### Predicción con XGBoost + Tuning Automático")
st.divider()

# ==========================================
# SIDEBAR - CONFIGURACIÓN
# ==========================================

st.sidebar.header("⚙️ Configuración")

# Cargar datos
@st.cache_data
def load_data():
    """Cargar todos los datos"""
    try:
        data = load_all_data()
        return data
    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
        return None

data = load_data()

if data is None:
    st.error("No se pudieron cargar los datos. Verifica la conexión.")
    st.stop()

# Selección de restaurante
restaurante = st.sidebar.selectbox(
    "🏪 Restaurante",
    options=list(data.keys()),
    index=0
)

# Obtener productos disponibles
df_restaurante = data[restaurante]
productos = sorted(df_restaurante['codigo_producto'].unique())

# Selección de producto
producto_seleccionado = st.sidebar.selectbox(
    "📦 Producto",
    options=productos,
    format_func=lambda x: f"{x}"
)

# Configuración del modelo
st.sidebar.markdown("---")
st.sidebar.subheader("🔧 Configuración del Modelo")

horizonte = st.sidebar.slider(
    "Horizonte de predicción (días)",
    min_value=7,
    max_value=60,
    value=14,
    step=7
)

n_trials = st.sidebar.slider(
    "Número de trials (Optuna)",
    min_value=5,
    max_value=50,
    value=20,
    step=5,
    help="Más trials = mejor modelo pero más lento"
)

train_val_split = st.sidebar.slider(
    "% de datos para entrenamiento",
    min_value=60,
    max_value=90,
    value=80,
    step=5
)

# Botón de entrenamiento
entrenar = st.sidebar.button("🚀 Entrenar y Predecir", type="primary", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Tip:** Más trials mejoran la precisión pero toman más tiempo. "
    "Para pruebas rápidas usa 10-15 trials."
)

# ==========================================
# MAIN - ÁREA DE TRABAJO
# ==========================================

# Filtrar datos del producto
df_producto = df_restaurante[df_restaurante['codigo_producto'] == producto_seleccionado].copy()
df_producto = df_producto.sort_values('fecha').reset_index(drop=True)

# Información del producto
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📊 Días disponibles", len(df_producto))

with col2:
    st.metric("📈 Promedio diario", f"{df_producto['cantidad_vendida_diaria'].mean():.1f}")

with col3:
    st.metric("📉 Desv. estándar", f"{df_producto['cantidad_vendida_diaria'].std():.1f}")

with col4:
    st.metric("🗓️ Periodo", f"{df_producto['fecha'].min().strftime('%Y-%m')} a {df_producto['fecha'].max().strftime('%Y-%m')}")

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

# ... (imports anteriores)

# ==========================================
# ENTRENAMIENTO Y PREDICCIÓN (ACTUALIZADO)
# ==========================================

if entrenar:
    
    with st.spinner("🔄 Preparando datos y entrenando modelo..."):
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 1. Feature Engineering
            status_text.text("🔧 Creando features...")
            progress_bar.progress(20)
            
            df_features = create_all_features(df_producto)
            df_features = df_features.dropna()
            
            if len(df_features) < 50:
                st.error("❌ No hay suficientes datos históricos para entrenar (mínimo 50 días)")
                st.stop()
            
            # 2. Preparar train/test
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
            
            # 3. Entrenar modelo
            status_text.text(f"🤖 Entrenando XGBoost + Intervalos ({n_trials} trials)...")
            progress_bar.progress(40)
            
            # Split interno para validación
            val_split = int(len(X_train) * 0.8)
            X_train_inner = X_train[:val_split]
            y_train_inner = y_train[:val_split]
            X_val = X_train[val_split:]
            y_val = y_train[val_split:]
            
            predictor = XGBoostPredictor(n_trials=n_trials, confidence_level=0.95)
            predictor.train(X_train_inner, y_train_inner, X_val, y_val)
            
            progress_bar.progress(70)
            
            # 4. Predecir en test (con intervalos)
            status_text.text("🎯 Evaluando en test...")
            
            y_pred_test, y_pred_test_lower, y_pred_test_upper = predictor.predict(X_test, return_intervals=True)
            
            progress_bar.progress(80)
            
            # 5. Predicción futura
            status_text.text("🔮 Prediciendo futuro...")
            
            last_date = df_producto['fecha'].max()
            future_dates = pd.date_range(
                start=last_date + timedelta(days=1),
                periods=horizonte,
                freq='D'
            )
            
            # Crear dataframe futuro con features
            df_future = pd.DataFrame({'fecha': future_dates})
            
            # Usar últimos valores como base
            last_values = df_producto['cantidad_vendida_diaria'].tail(30)
            df_future['cantidad_vendida_diaria'] = last_values.mean()  # Placeholder
            
            df_future = create_all_features(df_future)
            X_future = df_future[feature_cols].fillna(method='ffill').fillna(0)
            
            y_pred_future, y_pred_future_lower, y_pred_future_upper = predictor.predict(
                X_future[:horizonte], 
                return_intervals=True
            )
            
            progress_bar.progress(90)
            
            # 6. Calcular métricas
            metrics = calculate_metrics(y_test.values, y_pred_test)
            
            # 7. Generar alertas
            from utils.model_trainer import generate_alerts
            
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
            status_text.text("✅ ¡Listo!")
            
            # 8. Guardar en session state
            st.session_state['predictor'] = predictor
            st.session_state['metrics'] = metrics
            st.session_state['y_test'] = y_test
            st.session_state['y_pred_test'] = y_pred_test
            st.session_state['y_pred_test_lower'] = y_pred_test_lower
            st.session_state['y_pred_test_upper'] = y_pred_test_upper
            st.session_state['df_test'] = df_test
            st.session_state['future_dates'] = future_dates
            st.session_state['y_pred_future'] = y_pred_future
            st.session_state['y_pred_future_lower'] = y_pred_future_lower
            st.session_state['y_pred_future_upper'] = y_pred_future_upper
            st.session_state['df_producto'] = df_producto
            st.session_state['alerts'] = alerts
            
            progress_bar.empty()
            status_text.empty()
            
            st.success("✅ ¡Modelo entrenado exitosamente!")
            
        except Exception as e:
            st.error(f"❌ Error durante el entrenamiento: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            st.stop()

# ==========================================
# MOSTRAR RESULTADOS (ACTUALIZADO)
# ==========================================

if 'predictor' in st.session_state:
    
    predictor = st.session_state['predictor']
    metrics = st.session_state['metrics']
    y_test = st.session_state['y_test']
    y_pred_test = st.session_state['y_pred_test']
    y_pred_test_lower = st.session_state['y_pred_test_lower']
    y_pred_test_upper = st.session_state['y_pred_test_upper']
    df_test = st.session_state['df_test']
    future_dates = st.session_state['future_dates']
    y_pred_future = st.session_state['y_pred_future']
    y_pred_future_lower = st.session_state['y_pred_future_lower']
    y_pred_future_upper = st.session_state['y_pred_future_upper']
    df_producto = st.session_state['df_producto']
    alerts = st.session_state['alerts']
    
    st.divider()
    
    # ==========================================
    # ALERTAS (NUEVO)
    # ==========================================
    
    if alerts:
        st.subheader("🚨 Alertas Inteligentes")
        
        for alert in alerts:
            if alert['type'] == 'warning':
                with st.warning(f"{alert['icon']} **{alert['title']}**"):
                    st.write(alert['message'])
                    if alert['days'] is not None:
                        st.caption(f"Días afectados: {', '.join(map(str, alert['days']))}")
            
            elif alert['type'] == 'success':
                with st.success(f"{alert['icon']} **{alert['title']}**"):
                    st.write(alert['message'])
            
            else:  # info
                with st.info(f"{alert['icon']} **{alert['title']}**"):
                    st.write(alert['message'])
                    if alert['days'] is not None:
                        st.caption(f"Días afectados: {', '.join(map(str, alert['days']))}")
        
        st.divider()
    
    st.subheader("📊 Resultados del Modelo")
    
    # Métricas (igual que antes)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("MAE", f"{metrics['MAE']:.2f}", help="Error Absoluto Medio")
    
    with col2:
        st.metric("RMSE", f"{metrics['RMSE']:.2f}", help="Raíz del Error Cuadrático Medio")
    
    with col3:
        st.metric("MAPE", f"{metrics['MAPE']:.1f}%", help="Error Porcentual Absoluto Medio")
    
    with col4:
        accuracy = 100 - metrics['MAPE']
        st.metric("Precisión", f"{accuracy:.1f}%", help="100% - MAPE")
    
    st.divider()
    
    # Tabs de visualización
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Predicción", "🎯 Evaluación", "🔍 Features", "📋 Recomendaciones"])
    
    with tab1:
        st.subheader("Predicción Futura con Intervalos de Confianza (95%)")
        
        # Gráfico de predicción CON INTERVALOS
        fig_pred = go.Figure()
        
        # Histórico
        fig_pred.add_trace(go.Scatter(
            x=df_producto['fecha'],
            y=df_producto['cantidad_vendida_diaria'],
            mode='lines',
            name='Histórico',
            line=dict(color='#1f77b4', width=2),
            opacity=0.7
        ))
        
        # INTERVALO DE CONFIANZA (área sombreada)
        fig_pred.add_trace(go.Scatter(
            x=future_dates,
            y=y_pred_future_upper,
            mode='lines',
            name='Límite superior (95%)',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        fig_pred.add_trace(go.Scatter(
            x=future_dates,
            y=y_pred_future_lower,
            mode='lines',
            name='Intervalo 95%',
            line=dict(width=0),
            fillcolor='rgba(255, 127, 14, 0.2)',
            fill='tonexty',
            hoverinfo='skip'
        ))
        
        # Predicción puntual
        fig_pred.add_trace(go.Scatter(
            x=future_dates,
            y=y_pred_future,
            mode='lines+markers',
            name='Predicción',
            line=dict(color='#ff7f0e', width=3),
            marker=dict(size=8, symbol='diamond')
        ))
        
        # Línea divisoria
        last_date = df_producto['fecha'].max()
        fig_pred.add_vline(
            x=last_date,
            line_dash="dot",
            line_color="red",
            annotation_text="Hoy",
            annotation_position="top"
        )
        
        fig_pred.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Cantidad (unidades)",
            hovermode='x unified',
            template='plotly_white',
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig_pred, use_container_width=True)
        
        # Tabla de predicciones CON INTERVALOS
        st.markdown("### 📋 Predicciones Detalladas")
        
        # Calcular ancho del intervalo
        interval_width = y_pred_future_upper - y_pred_future_lower
        
        df_pred_table = pd.DataFrame({
            'Fecha': future_dates,
            'Día': future_dates.strftime('%A'),
            'Pesimista (5%)': y_pred_future_lower.round(1),
            'Predicción': y_pred_future.round(1),
            'Optimista (95%)': y_pred_future_upper.round(1),
            'Incertidumbre': interval_width.round(1),
            'Recomendación': [
                '🟢 Comprar conservador' if w > pred * 0.5 
                else '🟡 Comprar normal' if w > pred * 0.3
                else '🟢 Alta confianza'
                for pred, w in zip(y_pred_future, interval_width)
            ]
        })
        
        st.dataframe(
            df_pred_table,
            use_container_width=True,
            hide_index=True
        )
        
        # Explicación de intervalos
        with st.expander("ℹ️ ¿Cómo interpretar los intervalos de confianza?"):
            st.markdown("""
            **Intervalo de Confianza del 95%:**
            - Hay un 95% de probabilidad de que la demanda real esté entre el límite inferior y superior
            - **Escenario Pesimista (5%):** Compra esta cantidad para estar 95% seguro de vender todo
            - **Predicción:** Pronóstico más probable
            - **Escenario Optimista (95%):** Cantidad máxima esperada con 95% de confianza
            
            **Recomendaciones de compra:**
            - 🟢 **Alta incertidumbre:** Comprar conservadoramente (cerca del pesimista)
            - 🟡 **Incertidumbre media:** Comprar la predicción o un punto intermedio
            - 🟢 **Alta confianza:** Puedes comprar cerca de la predicción o incluso optimista
            """)
    
    with tab2:
        st.subheader("Evaluación en Conjunto de Test")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico Real vs Predicho (igual que antes)
            fig_scatter = go.Figure()
            
            fig_scatter.add_trace(go.Scatter(
                x=y_test,
                y=y_pred_test,
                mode='markers',
                marker=dict(size=8, color='#1f77b4', opacity=0.6),
                name='Predicciones'
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
                title="Real vs Predicho"
            )
            
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        with col2:
            # Distribución de errores (igual que antes)
            errores = y_test.values - y_pred_test
            
            fig_hist = go.Figure()
            
            fig_hist.add_trace(go.Histogram(
                x=errores,
                nbinsx=20,
                marker=dict(color='#1f77b4', opacity=0.7),
                name='Errores'
            ))
            
            fig_hist.update_layout(
                xaxis_title="Error (Real - Predicho)",
                yaxis_title="Frecuencia",
                template='plotly_white',
                height=400,
                title="Distribución de Errores"
            )
            
            st.plotly_chart(fig_hist, use_container_width=True)
        
        # Series temporales de test CON INTERVALOS
        st.markdown("### 📊 Predicciones en Test (con intervalos)")
        
        fig_test = go.Figure()
        
        # Intervalo de confianza
        fig_test.add_trace(go.Scatter(
            x=df_test['fecha'],
            y=y_pred_test_upper,
            mode='lines',
            name='Límite superior',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        fig_test.add_trace(go.Scatter(
            x=df_test['fecha'],
            y=y_pred_test_lower,
            mode='lines',
            name='Intervalo 95%',
            line=dict(width=0),
            fillcolor='rgba(255, 127, 14, 0.2)',
            fill='tonexty'
        ))
        
        # Real
        fig_test.add_trace(go.Scatter(
            x=df_test['fecha'],
            y=y_test,
            mode='lines+markers',
            name='Real',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6)
        ))
        
        # Predicción
        fig_test.add_trace(go.Scatter(
            x=df_test['fecha'],
            y=y_pred_test,
            mode='lines+markers',
            name='Predicho',
            line=dict(color='#ff7f0e', width=2),
            marker=dict(size=6)
        ))
        
        fig_test.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Cantidad (unidades)",
            hovermode='x unified',
            template='plotly_white',
            height=400
        )
        
        st.plotly_chart(fig_test, use_container_width=True)
        
        # Métricas de cobertura del intervalo
        coverage = ((y_test >= y_pred_test_lower) & (y_test <= y_pred_test_upper)).mean() * 100
        
        st.metric(
            "Cobertura del Intervalo",
            f"{coverage:.1f}%",
            help="% de valores reales que cayeron dentro del intervalo del 95%. Idealmente debería ser cercano al 95%."
        )
    
    with tab3:
        # Feature importance (igual que antes)
        st.subheader("Importancia de Features")
        
        feature_importance = pd.DataFrame({
            'Feature': predictor.feature_names,
            'Importance': predictor.model.feature_importances_
        }).sort_values('Importance', ascending=False).head(15)
        
        fig_importance = go.Figure()
        
        fig_importance.add_trace(go.Bar(
            y=feature_importance['Feature'],
            x=feature_importance['Importance'],
            orientation='h',
            marker=dict(color='#1f77b4')
        ))
        
        fig_importance.update_layout(
            xaxis_title="Importancia",
            yaxis_title="Feature",
            template='plotly_white',
            height=500,
            title="Top 15 Features Más Importantes"
        )
        
        st.plotly_chart(fig_importance, use_container_width=True)
        
        # Hiperparámetros
        st.markdown("### ⚙️ Hiperparámetros Óptimos")
        
        col1, col2 = st.columns(2)
        
        params_list = list(predictor.best_params.items())
        mid = len(params_list) // 2
        
        with col1:
            for key, value in params_list[:mid]:
                st.metric(key, f"{value}")
        
        with col2:
            for key, value in params_list[mid:]:
                st.metric(key, f"{value}")
    
    with tab4:
        st.subheader("📋 Recomendaciones Operativas")
        
        # Análisis de la predicción
        mean_pred = y_pred_future.mean()
        mean_hist = df_producto['cantidad_vendida_diaria'].mean()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Análisis General")
            
            if mean_pred > mean_hist * 1.1:
                st.info("📈 **Tendencia:** La demanda promedio predicha es mayor al histórico")
                st.write(f"- Promedio histórico: {mean_hist:.1f} unidades")
                st.write(f"- Promedio predicho: {mean_pred:.1f} unidades")
                st.write(f"- Incremento: +{((mean_pred/mean_hist - 1)*100):.1f}%")
            elif mean_pred < mean_hist * 0.9:
                st.warning("📉 **Tendencia:** La demanda promedio predicha es menor al histórico")
                st.write(f"- Promedio histórico: {mean_hist:.1f} unidades")
                st.write(f"- Promedio predicho: {mean_pred:.1f} unidades")
                st.write(f"- Decremento: -{((1 - mean_pred/mean_hist)*100):.1f}%")
            else:
                st.success("➡️ **Tendencia:** La demanda se mantiene estable")
                st.write(f"- Promedio histórico: {mean_hist:.1f} unidades")
                st.write(f"- Promedio predicho: {mean_pred:.1f} unidades")
        
        with col2:
            st.markdown("### 💡 Recomendación de Compra")
            
            # Calcular incertidumbre promedio
            avg_uncertainty = (y_pred_future_upper - y_pred_future_lower).mean()
            uncertainty_ratio = avg_uncertainty / mean_pred
            
            if uncertainty_ratio > 0.5:
                st.warning("⚠️ **Alta Incertidumbre**")
                st.write("Recomendación: Compra conservadora")
                st.write(f"- Cantidad segura: {y_pred_future_lower.mean():.0f} unidades/día")
                st.write(f"- Evita sobrestock")
            elif uncertainty_ratio > 0.3:
                st.info("ℹ️ **Incertidumbre Media**")
                st.write("Recomendación: Compra balanceada")
                st.write(f"- Cantidad recomendada: {mean_pred:.0f} unidades/día")
            else:
                st.success("✅ **Baja Incertidumbre**")
                st.write("Recomendación: Puedes comprar con confianza")
                st.write(f"- Cantidad óptima: {mean_pred:.0f} unidades/día")
                st.write(f"- Puedes considerar hasta: {y_pred_future_upper.mean():.0f} unidades/día")
        
        st.divider()
        
        # Descarga
        st.markdown("### 💾 Descargar Resultados")
        
        # CSV de predicciones con intervalos
        df_download = pd.DataFrame({
            'fecha': future_dates,
            'prediccion': y_pred_future.round(2),
            'limite_inferior_95': y_pred_future_lower.round(2),
            'limite_superior_95': y_pred_future_upper.round(2),
            'dia_semana': future_dates.strftime('%A')
        })
        
        csv = df_download.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📥 Descargar Predicciones con Intervalos (CSV)",
            data=csv,
            file_name=f"predicciones_{producto_seleccionado}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

else:
    st.info("👈 Configura los parámetros en el sidebar y presiona **'Entrenar y Predecir'** para comenzar")
