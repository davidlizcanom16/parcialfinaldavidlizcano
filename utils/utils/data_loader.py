# utils/data_loader.py
import pandas as pd
import streamlit as st
import numpy as np
from pathlib import Path

@st.cache_data
def cargar_datos():
    """Carga y procesa los 3 datasets"""
    
    # Detectar si estamos en local o en cloud
    base_path = Path(__file__).parent.parent / "data"
    
    archivos = {
        'Le Meridiem': base_path / 'dataset_lemeridiem_DIARIO.xlsx',
        'Sabina': base_path / 'dataset_sabina_DIARIO.xlsx',
        'Principal': base_path / 'dataset_principal_DIARIO.xlsx'
    }
    
    dfs = []
    
    for nombre, archivo in archivos.items():
        try:
            df = pd.read_excel(archivo)
            df['restaurante'] = nombre
            dfs.append(df)
        except Exception as e:
            st.error(f"❌ Error cargando {archivo.name}: {e}")
            return None
    
    if not dfs:
        return None
    
    # Consolidar
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
    
    # Calcular ventas en pesos
    if 'precio_promedio' in df.columns:
        df['venta_pesos'] = df['cantidad_vendida_diaria'] * df['precio_promedio']
    else:
        # Si no hay precio, usar cantidad como proxy
        df['venta_pesos'] = df['cantidad_vendida_diaria'] * 10000  # Precio promedio estimado
    
    # Limpiar nombres de productos
    df['producto'] = df['descripcion_producto'].str.strip().str.upper()
    
    # Marcar eventos
    df['tiene_evento'] = df['evento_especial'].notna().astype(int) if 'evento_especial' in df.columns else 0
    
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
    """Formatea números para display"""
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
