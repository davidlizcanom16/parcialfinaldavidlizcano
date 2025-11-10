# utils/data_loader.py
import pandas as pd
import streamlit as st
import numpy as np
from pathlib import Path

@st.cache_data
def cargar_datos():
    """Carga y procesa los 3 datasets"""
    
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
    
    df = pd.concat(dfs, ignore_index=True)
    
    # ==========================================
    # PROCESAR FECHAS
    # ==========================================
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['año'] = df['fecha'].dt.year
    df['mes'] = df['fecha'].dt.month
    df['mes_nombre'] = df['fecha'].dt.strftime('%B')
    df['dia'] = df['fecha'].dt.day
    df['dia_semana'] = df['fecha'].dt.day_name()
    df['semana_año'] = df['fecha'].dt.isocalendar().week
    df['es_fin_semana'] = df['dia_semana'].isin(['Saturday', 'Sunday']).astype(int)
    
    # ==========================================
    # USAR VALOR_TOTAL_DIARIO (YA ESTÁ EN PESOS)
    # ==========================================
    
    if 'valor_total_diario' in df.columns:
        # Convertir a numérico (maneja comas como decimales)
        df['venta_pesos'] = pd.to_numeric(
            df['valor_total_diario'].astype(str).str.replace(',', '.'), 
            errors='coerce'
        )
        
        # Reemplazar NaN con 0
        df['venta_pesos'] = df['venta_pesos'].fillna(0)
        
    else:
        st.error("❌ Columna 'valor_total_diario' no encontrada en los datos")
        return None
    
    # ==========================================
    # LIMPIAR NOMBRES DE PRODUCTOS
    # ==========================================
    df['producto'] = df['descripcion_producto'].str.strip().str.upper()
    
    # ==========================================
    # EVENTOS
    # ==========================================
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
