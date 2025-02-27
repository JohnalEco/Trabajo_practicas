import pandas as pd
import numpy as np
from datetime import datetime


def format_currency(value, decimals=0):
    """
    Formatea un valor numérico como moneda.
    
    Args:
        value: Valor numérico
        decimals: Número de decimales a mostrar
    
    Returns:
        Cadena formateada como moneda
    """
    if pd.isna(value):
        return "$0"
    
    return f"${value:,.{decimals}f}"


def format_percentage(value, decimals=1):
    """
    Formatea un valor numérico como porcentaje.
    
    Args:
        value: Valor numérico
        decimals: Número de decimales a mostrar
    
    Returns:
        Cadena formateada como porcentaje
    """
    if pd.isna(value):
        return "0.0%"
    
    return f"{value:.{decimals}f}%"


def format_date(date, format_str="%Y-%m-%d"):
    """
    Formatea una fecha en el formato especificado.
    
    Args:
        date: Objeto de fecha (datetime, timestamp, etc.)
        format_str: Formato de fecha deseado
    
    Returns:
        Cadena formateada como fecha
    """
    if pd.isna(date):
        return ""
    
    # Convertir a datetime si no lo es
    if not isinstance(date, (datetime, pd.Timestamp)):
        try:
            date = pd.to_datetime(date)
        except:
            return str(date)
    
    return date.strftime(format_str)


def safe_division(numerator, denominator, default=0):
    """
    Realiza una división segura evitando divisiones por cero.
    
    Args:
        numerator: Numerador
        denominator: Denominador
        default: Valor por defecto si el denominador es cero
    
    Returns:
        Resultado de la división o valor por defecto
    """
    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return default
    
    return numerator / denominator


def categorize_periods(df, date_column, period_type="month"):
    """
    Categoriza una columna de fecha en períodos.
    
    Args:
        df: DataFrame
        date_column: Nombre de la columna de fecha
        period_type: Tipo de período ('month', 'quarter', 'year')
    
    Returns:
        DataFrame con columna de período añadida
    """
    df = df.copy()
    
    # Convertir a datetime si no lo es
    if df[date_column].dtype != "datetime64[ns]":
        df[date_column] = pd.to_datetime(df[date_column])
    
    # Categorizar según tipo de período
    if period_type == "month":
        df["Period"] = df[date_column].dt.to_period("M").dt.to_timestamp()
    elif period_type == "quarter":
        df["Period"] = df[date_column].dt.to_period("Q").dt.to_timestamp()
    elif period_type == "year":
        df["Period"] = df[date_column].dt.to_period("Y").dt.to_timestamp()
    
    return df