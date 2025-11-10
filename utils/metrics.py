# utils/metrics.py
import pandas as pd
import numpy as np

def calcular_metricas_anuales(df, año):
    """Métricas ejecutivas anuales"""
    df_año = df[df['año'] == año]
    
    if len(df_año) == 0:
        return None
    
    return {
        'ventas_totales': df_año['venta_pesos'].sum(),
        'unidades_totales': df_año['cantidad_vendida_diaria'].sum(),
        'ticket_promedio': df_año['venta_pesos'].sum() / max(len(df_año['fecha'].unique()), 1),
        'dias_operacion': df_año['fecha'].nunique(),
        'productos_activos': df_año['producto'].nunique(),
        'ventas_promedio_dia': df_año.groupby('fecha')['venta_pesos'].sum().mean(),
        'mejor_mes': df_año.groupby('mes')['venta_pesos'].sum().idxmax() if len(df_año) > 0 else None,
        'peor_mes': df_año.groupby('mes')['venta_pesos'].sum().idxmin() if len(df_año) > 0 else None,
        'producto_estrella': df_año.groupby('producto')['venta_pesos'].sum().idxmax() if len(df_año) > 0 else None,
    }


def calcular_metricas_mensuales(df, año, mes):
    """Métricas del mes"""
    df_mes = df[(df['año'] == año) & (df['mes'] == mes)]
    
    if len(df_mes) == 0:
        return None
    
    # Mes anterior
    if mes > 1:
        df_mes_anterior = df[(df['año'] == año) & (df['mes'] == mes - 1)]
    else:
        df_mes_anterior = df[(df['año'] == año - 1) & (df['mes'] == 12)]
    
    ventas_mes = df_mes['venta_pesos'].sum()
    ventas_anterior = df_mes_anterior['venta_pesos'].sum() if len(df_mes_anterior) > 0 else ventas_mes
    
    return {
        'ventas_totales': ventas_mes,
        'cambio_vs_anterior': ((ventas_mes - ventas_anterior) / ventas_anterior * 100) if ventas_anterior > 0 else 0,
        'dias_operacion': df_mes['fecha'].nunique(),
        'ventas_promedio_dia': df_mes.groupby('fecha')['venta_pesos'].sum().mean(),
        'mejor_dia': df_mes.groupby('fecha')['venta_pesos'].sum().idxmax() if len(df_mes) > 0 else None,
        'peor_dia': df_mes.groupby('fecha')['venta_pesos'].sum().idxmin() if len(df_mes) > 0 else None,
        'mejor_dia_semana': df_mes.groupby('dia_semana')['venta_pesos'].sum().idxmax() if len(df_mes) > 0 else None,
        'top_3_productos': df_mes.groupby('producto')['venta_pesos'].sum().nlargest(3),
    }


def calcular_metricas_diarias(df, fecha):
    """Métricas del día específico"""
    df_dia = df[df['fecha'] == pd.to_datetime(fecha)]
    
    if len(df_dia) == 0:
        return None
    
    dia_semana = pd.to_datetime(fecha).day_name()
    df_dias_similares = df[df['dia_semana'] == dia_semana]
    
    ventas_dia = df_dia['venta_pesos'].sum()
    ventas_promedio_similar = df_dias_similares.groupby('fecha')['venta_pesos'].sum().mean()
    
    return {
        'ventas_totales': ventas_dia,
        'unidades_vendidas': df_dia['cantidad_vendida_diaria'].sum(),
        'productos_vendidos': df_dia['producto'].nunique(),
        'ticket_promedio': ventas_dia / max(len(df_dia), 1),
        'vs_promedio_dia_similar': ((ventas_dia - ventas_promedio_similar) / ventas_promedio_similar * 100) if ventas_promedio_similar > 0 else 0,
        'top_producto': df_dia.groupby('producto')['venta_pesos'].sum().idxmax() if len(df_dia) > 0 else 'N/A',
        'tiene_evento': df_dia['tiene_evento'].max() if len(df_dia) > 0 else 0,
        'restaurante_lider': df_dia.groupby('restaurante')['venta_pesos'].sum().idxmax() if len(df_dia) > 0 else 'N/A'
    }


def calcular_top_productos(df, top_n=10):
    """Calcula top productos con métricas"""
    productos = df.groupby('producto').agg({
        'venta_pesos': 'sum',
        'cantidad_vendida_diaria': 'sum',
        'fecha': 'count'
    }).rename(columns={'fecha': 'frecuencia'})
    
    productos = productos.sort_values('venta_pesos', ascending=False).head(top_n)
    productos['ticket_promedio'] = productos['venta_pesos'] / productos['cantidad_vendida_diaria']
    
    return productos


def calcular_productos_riesgo(df, top_n=10):
    """Identifica productos en riesgo"""
    from scipy import stats
    
    productos_riesgo = []
    
    for producto in df['producto'].unique():
        df_prod = df[df['producto'] == producto]
        
        if len(df_prod) < 10:  # Muy poco histórico
            continue
        
        ventas_total = df_prod['venta_pesos'].sum()
        fecha_max = df_prod['fecha'].max()
        fecha_hace_30 = fecha_max - pd.Timedelta(days=30)
        
        df_reciente = df_prod[df_prod['fecha'] >= fecha_hace_30]
        ventas_recientes = df_reciente['venta_pesos'].sum()
        
        # Calcular tendencia
        ventas_diarias = df_prod.groupby('fecha')['cantidad_vendida_diaria'].sum().reset_index()
        if len(ventas_diarias) >= 5:
            x = np.arange(len(ventas_diarias))
            y = ventas_diarias['cantidad_vendida_diaria'].values
            slope, _, _, _, _ = stats.linregress(x, y)
            tendencia = slope
        else:
            tendencia = 0
        
        # Score de riesgo
        score_riesgo = 0
        
        if tendencia < 0:
            score_riesgo += 30
        
        if ventas_recientes < ventas_total * 0.15:
            score_riesgo += 25
        
        varianza = df_prod.groupby('fecha')['cantidad_vendida_diaria'].sum().std()
        if varianza > df_prod['cantidad_vendida_diaria'].mean():
            score_riesgo += 20
        
        if len(df_prod) < len(df['fecha'].unique()) * 0.3:
            score_riesgo += 25
        
        productos_riesgo.append({
            'producto': producto,
            'score_riesgo': score_riesgo,
            'ventas_total': ventas_total,
            'ventas_recientes': ventas_recientes,
            'tendencia': tendencia
        })
    
    df_riesgo = pd.DataFrame(productos_riesgo).sort_values('score_riesgo', ascending=False)
    return df_riesgo.head(top_n)
