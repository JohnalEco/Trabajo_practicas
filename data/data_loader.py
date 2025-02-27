import os
import pandas as pd
from pathlib import Path
import numpy as np
from functools import lru_cache


def get_data_path():
    """
    Función para determinar la ruta de los archivos de datos.
    En un entorno de producción, esto podría apuntar a un directorio específico o a una base de datos.
    """
    # Para desarrollo, usamos el directorio actual + /data
    base_path = Path(__file__).parent.parent / "data"
    return base_path


@lru_cache(maxsize=1)
def load_siniestros():
    """
    Carga el archivo de siniestros.txt.
    Los archivos originales están en formato TXT con delimitador de tabulación.
    La función está decorada con lru_cache para evitar cargar el archivo repetidamente.
    """
    try:
        # Intentar cargar desde la ruta especificada
        path = get_data_path() / "siniestros.txt"
        # Usar dtype para acelerar la carga de datos
        dtypes = {
            'Pago_Bruto': np.float32,
            'Pago_Retenido': np.float32
        }
        # Establecer usecols para leer solo las columnas necesarias
        usecols = [
            'Fecha_Siniestro', 'Fecha_Registro', 
            'Pago_Bruto', 'Pago_Retenido', 
            'Ramo_Desc', 'Apertura_Canal_Desc', 
            'Apertura_Amparo_Desc', 'Agrupacion_Reservas'
        ]
        
        print(f"Cargando datos de siniestros desde {path}")
        df = pd.read_csv(
            path, 
            delimiter="\t",
            encoding="utf-8",
            quoting=3,
            low_memory=False,
            parse_dates=['Fecha_Siniestro', 'Fecha_Registro'],
            dtype=dtypes,
            usecols=usecols
        )
        
        print(f"Datos de siniestros cargados: {len(df)} filas, {len(df.columns)} columnas")
        return df
    except FileNotFoundError:
        print("Archivo de siniestros no encontrado. Creando DataFrame vacío.")
        return pd.DataFrame({
            "Fecha_Siniestro": pd.Series(dtype="datetime64[ns]"),
            "Fecha_Registro": pd.Series(dtype="datetime64[ns]"),
            "Pago_Bruto": pd.Series(dtype="float32"),
            "Pago_Retenido": pd.Series(dtype="float32"),
            "Ramo_Desc": pd.Series(dtype="str"),
            "Apertura_Canal_Desc": pd.Series(dtype="str"),
            "Apertura_Amparo_Desc": pd.Series(dtype="str"),
            "Agrupacion_Reservas": pd.Series(dtype="str")
        })


@lru_cache(maxsize=1)
def load_expuestos():
    """
    Carga el archivo de expuestos.txt.
    Los archivos originales están en formato TXT con delimitador de tabulación.
    """
    try:
        path = get_data_path() / "expuestos.txt"
        # Usar dtype para acelerar la carga
        dtypes = {
            'Expuestos': np.int32
        }
        
        print(f"Cargando datos de expuestos desde {path}")
        df = pd.read_csv(
            path, 
            delimiter="\t",
            encoding="utf-8",
            quoting=3,
            low_memory=False,
            parse_dates=['Fecha_Registro'] if 'Fecha_Registro' in pd.read_csv(path, nrows=0, delimiter="\t").columns else None,
            dtype=dtypes
        )
        
        print(f"Datos de expuestos cargados: {len(df)} filas, {len(df.columns)} columnas")
        return df
    except FileNotFoundError:
        print("Archivo de expuestos no encontrado. Creando DataFrame vacío.")
        return pd.DataFrame({
            "Fecha_Registro": pd.Series(dtype="datetime64[ns]"),
            "Expuestos": pd.Series(dtype="int32"),
            "Ramo_Desc": pd.Series(dtype="str"),
            "Apertura_Canal_Desc": pd.Series(dtype="str"),
            "Apertura_Amparo_Desc": pd.Series(dtype="str")
        })


def get_date_range():
    """
    Obtiene el rango de fechas disponible en los datos de siniestros.
    """
    siniestros = load_siniestros()
    if siniestros.empty:
        # Si no hay datos, devolver un rango por defecto
        from datetime import datetime, timedelta
        today = datetime.now()
        return today - timedelta(days=365), today
    
    fecha_min = siniestros["Fecha_Siniestro"].min()
    fecha_max = siniestros["Fecha_Registro"].max()
    
    return fecha_min, fecha_max