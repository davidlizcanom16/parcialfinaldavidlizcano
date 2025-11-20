"""
Feature Engineering para Predictor
"""

import pandas as pd
import numpy as np
from datetime import timedelta

def create_temporal_features(df):
    """Crear features temporales"""
    df = df.copy()
    df['fecha'] = pd.to_datetime(df['fecha'])
    
    # Features básicas
    df['dia_semana'] = df['fecha'].dt.dayofweek
    df['mes'] = df['fecha'].dt.month
    df['dia_mes'] = df['fecha'].dt.day
    df['semana_año'] = df['fecha'].dt.isocalendar().week
    df['trimestre'] = df['fecha'].dt.quarter
    
    # Features cíclicas
    df['dia_semana_sin'] = np.sin(2 * np.pi * df['dia_semana'] / 7)
    df['dia_semana_cos'] = np.cos(2 * np.pi * df['dia_semana'] / 7)
    df['mes_sin'] = np.sin(2 * np.pi * df['mes'] / 12)
    df['mes_cos'] = np.cos(2 * np.pi * df['mes'] / 12)
    
    # Fin de semana
    df['es_fin_semana'] = (df['dia_semana'] >= 5).astype(int)
    
    # Normalizar día del mes
    df['dia_mes_norm'] = df['dia_mes'] / df['fecha'].dt.days_in_month
    
    return df

def create_event_features(df):
    """Crear features de eventos especiales"""
    df = df.copy()
    df['fecha'] = pd.to_datetime(df['fecha'])
    
    # Carnaval (Febrero)
    df['es_carnaval'] = (df['fecha'].dt.month == 2).astype(int)
    
    # Grados (Mayo-Junio)
    df['es_grados'] = df['fecha'].dt.month.isin([5, 6]).astype(int)
    
    # Navidad (Dic 20-31)
    df['es_navidad'] = ((df['fecha'].dt.month == 12) & (df['fecha'].dt.day >= 20)).astype(int)
    
    # Fin de año (Dic 29-31)
    df['es_fin_año'] = ((df['fecha'].dt.month == 12) & (df['fecha'].dt.day >= 29)).astype(int)
    
    # Temporada empresarial (Nov-Dic)
    df['es_temp_empresarial'] = df['fecha'].dt.month.isin([11, 12]).astype(int)
    
    return df

def create_lag_features(df, target_col='cantidad_vendida_diaria', lags=[1, 2, 3, 7, 14, 30]):
    """Crear features de lags"""
    df = df.copy()
    
    for lag in lags:
        df[f'lag_{lag}'] = df[target_col].shift(lag)
    
    return df

def create_rolling_features(df, target_col='cantidad_vendida_diaria', windows=[7, 14, 30]):
    """Crear features de rolling windows"""
    df = df.copy()
    
    for window in windows:
        df[f'rolling_mean_{window}'] = df[target_col].shift(1).rolling(window=window, min_periods=1).mean()
        df[f'rolling_std_{window}'] = df[target_col].shift(1).rolling(window=window, min_periods=1).std()
        df[f'rolling_min_{window}'] = df[target_col].shift(1).rolling(window=window, min_periods=1).min()
        df[f'rolling_max_{window}'] = df[target_col].shift(1).rolling(window=window, min_periods=1).max()
    
    return df

def create_all_features(df, target_col='cantidad_vendida_diaria'):
    """Crear todas las features"""
    df = create_temporal_features(df)
    df = create_event_features(df)
    df = create_lag_features(df, target_col)
    df = create_rolling_features(df, target_col)
    
    # Diferencias
    df['diff_1'] = df[target_col].diff(1)
    df['diff_7'] = df[target_col].diff(7)
    
    return df

def get_feature_columns():
    """Obtener lista de columnas de features"""
    lag_features = [f'lag_{lag}' for lag in [1, 2, 3, 7, 14, 30]]
    
    rolling_features = []
    for window in [7, 14, 30]:
        rolling_features.extend([
            f'rolling_mean_{window}',
            f'rolling_std_{window}',
            f'rolling_min_{window}',
            f'rolling_max_{window}'
        ])
    
    temporal_features = [
        'dia_semana', 'mes', 'dia_mes_norm', 'semana_año', 'trimestre',
        'dia_semana_sin', 'dia_semana_cos', 'mes_sin', 'mes_cos', 'es_fin_semana'
    ]
    
    event_features = [
        'es_carnaval', 'es_grados', 'es_navidad', 'es_fin_año', 'es_temp_empresarial'
    ]
    
    diff_features = ['diff_1', 'diff_7']
    
    return lag_features + rolling_features + temporal_features + event_features + diff_features
