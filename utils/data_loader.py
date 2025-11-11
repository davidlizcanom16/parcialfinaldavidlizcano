# utils/data_loader.py - VERSIÓN CSV
import pandas as pd
import streamlit as st
import numpy as np
from pathlib import Path

@st.cache_data(ttl=3600, show_spinner=False)
def cargar_datos():
    """Carga y procesa los 3 datasets desde CSV"""
    
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
            
            # Leer CSV (mucho más compatible que Excel)
            df = pd.read_csv(archivo)
            
            # Convertir fecha
            df['fecha'] = pd.to_datetime(df['fecha'])
            
            # Verificar columnas
            columnas_requeridas = ['fecha', 'codigo_producto', 'descripcion_producto', 
                                  'cantidad_vendida_diaria', 'valor_total_diario']
            
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            
            if columnas_faltantes:
                st.error(f"❌ {nombre}: Faltan columnas: {columnas_faltantes}")
                continue
            
            df['restaurante'] = nombre
            dfs.append(df)
            
            st.sidebar.success(f"✅ {nombre}: {len(df):,} registros")
            
        except Exception as e:
            st.error(f"❌ Error cargando {nombre}: {str(e)}")
            continue
    
    progress_bar.empty()
    
    if not dfs:
        return None
    
    # Consolidar
    df = pd.concat(dfs, ignore_index=True)
    
    # Procesar
    df['año'] = df['fecha'].dt.year
    df['mes'] = df['fecha'].dt.month
    df['mes_nombre'] = df['fecha'].dt.strftime('%B')
    df['dia'] = df['fecha'].dt.day
    df['dia_semana'] = df['fecha'].dt.day_name()
    df['semana_año'] = df['fecha'].dt.isocalendar().week
    df['es_fin_semana'] = df['dia_semana'].isin(['Saturday', 'Sunday']).astype(int)
    
    df['venta_pesos'] = df['valor_total_diario']
    df['producto'] = df['descripcion_producto'].str.strip().str.upper()
    
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
