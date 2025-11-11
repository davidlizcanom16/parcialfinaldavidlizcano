# utils/data_loader.py - VERSIÓN CORREGIDA
import pandas as pd
import streamlit as st
from pathlib import Path

@st.cache_data(ttl=3600, show_spinner=False)
def cargar_datos():
    """Carga datos desde CSV - USA CÓDIGO COMO IDENTIFICADOR"""
    
    base_path = Path(__file__).parent.parent / "data"
    
    archivos = {
        'Le Meridiem': base_path / 'dataset_lemeridiem_DIARIO.csv',
        'Sabina': base_path / 'dataset_sabina_DIARIO.csv',
        'Principal': base_path / 'dataset_principal_DIARIO.csv'
    }
    
    dfs = []
    
    progress_bar = st.progress(0, text="🔄 Cargando datos...")
    total_archivos = len(archivos)
    
    for idx, (nombre, archivo) in enumerate(archivos.items(), 1):
        try:
            progress_bar.progress(idx / total_archivos, 
                                text=f"🔄 Cargando {nombre}... ({idx}/{total_archivos})")
            
            # Leer CSV
            df = pd.read_csv(archivo, parse_dates=['fecha'])
            
            df['restaurante'] = nombre
            dfs.append(df)
            
        except Exception as e:
            st.error(f"❌ Error cargando {nombre}: {str(e)}")
            continue
    
    progress_bar.empty()
    
    if not dfs:
        return None
    
    df = pd.concat(dfs, ignore_index=True)
    
    # Procesar fechas
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['año'] = df['fecha'].dt.year
    df['mes'] = df['fecha'].dt.month
    df['mes_nombre'] = df['fecha'].dt.strftime('%B')
    df['dia'] = df['fecha'].dt.day
    df['dia_semana'] = df['fecha'].dt.day_name()
    df['semana_año'] = df['fecha'].dt.isocalendar().week
    df['es_fin_semana'] = df['dia_semana'].isin(['Saturday', 'Sunday']).astype(int)
    
    # ==========================================
    # CRÍTICO: CONSOLIDAR DESCRIPCIONES POR CÓDIGO
    # ==========================================
    
    # Para cada código, tomar la descripción más reciente
    descripcion_por_codigo = df.sort_values('fecha', ascending=False).groupby('codigo_producto')['descripcion_producto'].first()
    
    # Mapear descripciones consolidadas
    df['descripcion_consolidada'] = df['codigo_producto'].map(descripcion_por_codigo)
    
    # USAR DESCRIPCIÓN CONSOLIDADA como "producto"
    df['producto'] = df['descripcion_consolidada'].str.strip().str.upper()
    
    # Columna de ventas
    df['venta_pesos'] = df['valor_total_diario']
    
    # Eventos
    if 'evento_especial' in df.columns:
        df['tiene_evento'] = df['evento_especial'].notna().astype(int)
    else:
        df['tiene_evento'] = 0
    
    return df.sort_values('fecha').reset_index(drop=True)


def get_restaurante_color(restaurante):
    """Colores por restaurante"""
    colores = {
        'Le Meridiem': '#FF6B6B',
        'Sabina': '#4ECDC4', 
        'Principal': '#FFD93D'
    }
    return colores.get(restaurante, '#95E1D3')


def formatear_numero(numero, tipo='moneda'):
    """Formatea números"""
    if pd.isna(numero):
        return 'N/A'
    
    if tipo == 'moneda':
        return f"${numero:,.0f}"
    elif tipo == 'porcentaje':
        return f"{numero:.1f}%"
    elif tipo == 'numero':
        return f"{numero:,.0f}"
    else:
        return str(numero)


@st.cache_data(ttl=3600)
def get_metricas_generales(df):
    """Calcula métricas generales (cacheado)"""
    return {
        'ventas_totales': df['venta_pesos'].sum(),
        'unidades_totales': df['cantidad_vendida_diaria'].sum(),
        'productos_unicos': df['codigo_producto'].nunique(),  # ← USAR CÓDIGO
        'dias_operacion': df['fecha'].nunique(),
        'restaurantes': df['restaurante'].unique().tolist(),
        'fecha_min': df['fecha'].min(),
        'fecha_max': df['fecha'].max()
    }
