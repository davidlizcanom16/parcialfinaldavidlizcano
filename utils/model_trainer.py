"""
Entrenador de modelos con Optuna + Intervalos de Confianza
"""

import pandas as pd
import numpy as np
import xgboost as xgb
import optuna
from sklearn.metrics import mean_absolute_error, mean_squared_error
import pickle
import os

optuna.logging.set_verbosity(optuna.logging.WARNING)

class XGBoostPredictor:
    """Predictor con XGBoost, tuning automático e intervalos de confianza"""
    
    def __init__(self, n_trials=20, random_state=42, confidence_level=0.95):
        self.n_trials = n_trials
        self.random_state = random_state
        self.confidence_level = confidence_level
        self.model = None
        self.model_lower = None  # Cuantil inferior
        self.model_upper = None  # Cuantil superior
        self.best_params = None
        self.feature_names = None
        
        # Calcular quantiles para intervalos
        alpha = 1 - confidence_level
        self.quantile_lower = alpha / 2
        self.quantile_upper = 1 - (alpha / 2)
        
    def optimize_hyperparameters(self, X_train, y_train, X_val, y_val):
        """Optimizar hiperparámetros con Optuna"""
        
        def objective(trial):
            params = {
                'max_depth': trial.suggest_int('max_depth', 3, 8),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.2),
                'n_estimators': trial.suggest_int('n_estimators', 50, 200),
                'min_child_weight': trial.suggest_int('min_child_weight', 1, 5),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 0.5),
                'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 0.5),
                'random_state': self.random_state,
                'n_jobs': -1,
                'verbosity': 0
            }
            
            model = xgb.XGBRegressor(**params)
            model.fit(X_train, y_train, verbose=False)
            
            y_pred = model.predict(X_val)
            mae = mean_absolute_error(y_val, y_pred)
            
            return mae
        
        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=False)
        
        self.best_params = study.best_params
        return study.best_params
    
    def train(self, X_train, y_train, X_val=None, y_val=None):
        """Entrenar modelo + intervalos de confianza"""
        
        # Si hay validación, hacer tuning
        if X_val is not None and y_val is not None:
            self.optimize_hyperparameters(X_train, y_train, X_val, y_val)
            
            # Concatenar train + val para entrenamiento final
            X_full = pd.concat([X_train, X_val])
            y_full = pd.concat([y_train, y_val])
        else:
            # Usar parámetros por defecto
            self.best_params = {
                'max_depth': 6,
                'learning_rate': 0.1,
                'n_estimators': 100,
                'random_state': self.random_state,
                'n_jobs': -1
            }
            X_full = X_train
            y_full = y_train
        
        # 1. Entrenar modelo principal (predicción puntual)
        self.model = xgb.XGBRegressor(**self.best_params, verbosity=0)
        self.model.fit(X_full, y_full)
        
        # 2. Entrenar modelos para intervalos (quantile regression)
        params_quantile = self.best_params.copy()
        params_quantile['n_estimators'] = max(50, params_quantile['n_estimators'] // 2)  # Más rápido
        
        # Cuantil inferior
        self.model_lower = xgb.XGBRegressor(
            **params_quantile,
            objective='reg:quantileerror',
            quantile_alpha=self.quantile_lower,
            verbosity=0
        )
        self.model_lower.fit(X_full, y_full)
        
        # Cuantil superior
        self.model_upper = xgb.XGBRegressor(
            **params_quantile,
            objective='reg:quantileerror',
            quantile_alpha=self.quantile_upper,
            verbosity=0
        )
        self.model_upper.fit(X_full, y_full)
        
        self.feature_names = X_full.columns.tolist()
        
        return self.model
    
    def predict(self, X, return_intervals=False):
        """Hacer predicción con o sin intervalos"""
        if self.model is None:
            raise ValueError("Modelo no entrenado. Llama a train() primero.")
        
        # Predicción puntual
        predictions = self.model.predict(X)
        predictions = np.maximum(predictions, 0)
        
        if not return_intervals:
            return predictions
        
        # Intervalos de confianza
        pred_lower = self.model_lower.predict(X)
        pred_upper = self.model_upper.predict(X)
        
        # Asegurar que lower <= pred <= upper
        pred_lower = np.maximum(pred_lower, 0)
        pred_upper = np.maximum(pred_upper, predictions)
        pred_lower = np.minimum(pred_lower, predictions)
        
        return predictions, pred_lower, pred_upper
    
    def save(self, filepath):
        """Guardar modelo"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        model_data = {
            'model': self.model,
            'model_lower': self.model_lower,
            'model_upper': self.model_upper,
            'best_params': self.best_params,
            'feature_names': self.feature_names,
            'random_state': self.random_state,
            'confidence_level': self.confidence_level
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    @classmethod
    def load(cls, filepath):
        """Cargar modelo"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        predictor = cls()
        predictor.model = model_data['model']
        predictor.model_lower = model_data.get('model_lower')
        predictor.model_upper = model_data.get('model_upper')
        predictor.best_params = model_data['best_params']
        predictor.feature_names = model_data['feature_names']
        predictor.random_state = model_data['random_state']
        predictor.confidence_level = model_data.get('confidence_level', 0.95)
        
        return predictor

def calculate_metrics(y_true, y_pred):
    """Calcular métricas de evaluación"""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    
    mask = y_true != 0
    if mask.sum() > 0:
        mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    else:
        mape = np.nan
    
    return {
        'MAE': mae,
        'RMSE': rmse,
        'MAPE': mape
    }

def generate_alerts(predictions, pred_lower, pred_upper, historical_mean, historical_std):
    """Generar alertas inteligentes"""
    alerts = []
    
    # 1. Demanda inusualmente alta
    high_threshold = historical_mean + 2 * historical_std
    high_demand_days = predictions > high_threshold
    
    if high_demand_days.any():
        n_days = high_demand_days.sum()
        max_pred = predictions[high_demand_days].max()
        alerts.append({
            'type': 'warning',
            'icon': '⚠️',
            'title': 'Demanda Alta Esperada',
            'message': f'{n_days} día(s) con demanda inusualmente alta (hasta {max_pred:.0f} unidades, +{((max_pred/historical_mean - 1)*100):.0f}% vs promedio)',
            'days': np.where(high_demand_days)[0] + 1
        })
    
    # 2. Demanda inusualmente baja
    low_threshold = max(0, historical_mean - 2 * historical_std)
    low_demand_days = predictions < low_threshold
    
    if low_demand_days.any():
        n_days = low_demand_days.sum()
        min_pred = predictions[low_demand_days].min()
        alerts.append({
            'type': 'info',
            'icon': '📉',
            'title': 'Demanda Baja Esperada',
            'message': f'{n_days} día(s) con demanda baja (mínimo {min_pred:.0f} unidades, -{((1 - min_pred/historical_mean)*100):.0f}% vs promedio)',
            'days': np.where(low_demand_days)[0] + 1
        })
    
    # 3. Alta incertidumbre
    uncertainty = pred_upper - pred_lower
    uncertainty_ratio = uncertainty / predictions
    high_uncertainty_days = uncertainty_ratio > 0.5  # Más de 50% de incertidumbre
    
    if high_uncertainty_days.any():
        n_days = high_uncertainty_days.sum()
        alerts.append({
            'type': 'info',
            'icon': '🔮',
            'title': 'Alta Incertidumbre',
            'message': f'{n_days} día(s) con alta incertidumbre en la predicción. Considera comprar de manera conservadora.',
            'days': np.where(high_uncertainty_days)[0] + 1
        })
    
    # 4. Tendencia creciente
    if len(predictions) >= 7:
        first_half_mean = predictions[:len(predictions)//2].mean()
        second_half_mean = predictions[len(predictions)//2:].mean()
        
        if second_half_mean > first_half_mean * 1.2:  # 20% más
            alerts.append({
                'type': 'success',
                'icon': '📈',
                'title': 'Tendencia Creciente',
                'message': f'La demanda muestra tendencia creciente (+{((second_half_mean/first_half_mean - 1)*100):.0f}% en segunda mitad)',
                'days': None
            })
        elif second_half_mean < first_half_mean * 0.8:  # 20% menos
            alerts.append({
                'type': 'info',
                'icon': '📉',
                'title': 'Tendencia Decreciente',
                'message': f'La demanda muestra tendencia decreciente (-{((1 - second_half_mean/first_half_mean)*100):.0f}% en segunda mitad)',
                'days': None
            })
    
    # 5. Fin de semana vs días laborales
    # Asumiendo que tenemos información de días de la semana
    # (Esto se puede mejorar con features temporales)
    
    return alerts
