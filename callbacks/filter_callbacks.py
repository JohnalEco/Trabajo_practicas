from dash import Input, Output, State, callback_context
import pandas as pd
import numpy as np
import time
import hashlib
import json

from data.data_loader import load_siniestros
from data.data_processor import procesar_siniestros


def register_filter_callbacks(app, cache):
    """
    Registra los callbacks para los filtros con optimización de caché.
    
    Args:
        app: Aplicación Dash
        cache: Objeto de caché de Flask
    """
    
    # Función para generar una clave de caché única basada en los parámetros
    def get_cache_key(prefix, *args):
        # Convertir argumentos a string y concatenar
        args_str = json.dumps(args, sort_keys=True, default=str)
        # Generar hash único
        key = hashlib.md5(args_str.encode()).hexdigest()
        return f"{prefix}_{key}"
    
    # Función cacheada para cargar datos
    @cache.memoize()
    def cached_load_siniestros():
        """Versión cacheada de load_siniestros"""
        start = time.time()
        data = load_siniestros()
        print(f"Carga de siniestros: {time.time() - start:.2f} segundos")
        return data
    
    # Función cacheada para procesamiento inicial
    @cache.memoize()
    def cached_process_initial_data(periodicidad, tipo_triangulo, tipo_valor):
        """Versión cacheada del procesamiento inicial"""
        start = time.time()
        
        # Cargar datos
        siniestros = cached_load_siniestros()
        
        if siniestros.empty:
            print("¡Archivo de siniestros vacío o no encontrado!")
            return None
        
        # Procesar datos
        try:
            processed_data = procesar_siniestros(
                siniestros, 
                periodicidad, 
                tipo_triangulo,
                tipo_valor
            )
            
            if processed_data.empty:
                print(f"Procesamiento produjo un DataFrame vacío")
                return None
            
            result = processed_data.to_dict('records')
            print(f"Procesamiento inicial: {time.time() - start:.2f} segundos, {len(processed_data)} filas")
            return result
            
        except Exception as e:
            print(f"Error en procesamiento inicial: {str(e)}")
            return None
    
    # Callback para procesar datos iniciales
    @app.callback(
        Output("stored-processed-data", "data"),
        [
            Input("periodicidad", "value"),
            Input("tipo_triangulo", "value"),
            Input("tipo_valor", "value")
        ]
    )
    def process_initial_data(periodicidad, tipo_triangulo, tipo_valor):
        """Procesa los datos iniciales según la periodicidad seleccionada."""
        if not periodicidad or not tipo_triangulo or not tipo_valor:
            return None
        
        # Usar la versión cacheada
        return cached_process_initial_data(periodicidad, tipo_triangulo, tipo_valor)
    
    
    # Función cacheada para obtener opciones únicas
    @cache.memoize()
    def get_unique_options(data, column, filter_dict=None):
        """Función para obtener opciones únicas de una columna con posibles filtros"""
        if not data:
            return [{"label": "Todos", "value": ""}]
        
        start = time.time()
        
        # Convertir a DataFrame
        df = pd.DataFrame(data)
        
        # Aplicar filtros si existen
        if filter_dict:
            for col, value in filter_dict.items():
                if value and col in df.columns:
                    df = df[df[col] == value]
        
        # Obtener opciones únicas
        try:
            unique_values = sorted(df[column].unique())
            options = [{"label": "Todos", "value": ""}]
            options.extend([{"label": val, "value": val} for val in unique_values])
            
            print(f"Opciones para {column}: {time.time() - start:.2f} segundos, {len(options)-1} opciones")
            return options
        except Exception as e:
            print(f"Error obteniendo opciones para {column}: {str(e)}")
            return [{"label": "Todos", "value": ""}]
    
    
    # Callback para actualizar opciones de filtro de ramo
    @app.callback(
        Output("ramo", "options"),
        Input("stored-processed-data", "data")
    )
    def update_ramo_options(processed_data):
        """Actualiza las opciones de ramo basadas en los datos procesados."""
        return get_unique_options(processed_data, "Ramo_Desc")
    
    
    # Callback para actualizar opciones de filtro de canal
    @app.callback(
        Output("canal", "options"),
        [
            Input("stored-processed-data", "data"),
            Input("ramo", "value")
        ]
    )
    def update_canal_options(processed_data, ramo):
        """Actualiza las opciones de canal basadas en los datos y ramo seleccionados."""
        filter_dict = {"Ramo_Desc": ramo} if ramo else None
        return get_unique_options(processed_data, "Apertura_Canal_Desc", filter_dict)
    
    
    # Callback para actualizar opciones de filtro de amparo
    @app.callback(
        Output("amparo", "options"),
        [
            Input("stored-processed-data", "data"),
            Input("ramo", "value"),
            Input("canal", "value")
        ]
    )
    def update_amparo_options(processed_data, ramo, canal):
        """Actualiza las opciones de amparo basadas en los datos y filtros seleccionados."""
        filter_dict = {}
        if ramo:
            filter_dict["Ramo_Desc"] = ramo
        if canal:
            filter_dict["Apertura_Canal_Desc"] = canal
            
        return get_unique_options(processed_data, "Apertura_Amparo_Desc", filter_dict)
    
    
    # Función cacheada para filtrado
    @cache.memoize()
    def cached_filter_data(data_json, ramo, canal, amparo, fecha_inicio, fecha_fin):
        """Versión cacheada del filtrado de datos"""
        if not data_json:
            return None
        
        start = time.time()
        
        # Generar clave de caché
        cache_key = get_cache_key("filter", ramo, canal, amparo, fecha_inicio, fecha_fin)
        
        # Convertir a DataFrame
        df = pd.DataFrame(data_json)
        
        # Crear máscara de filtro
        mask = np.ones(len(df), dtype=bool)
        
        # Aplicar filtros
        if ramo:
            mask &= (df["Ramo_Desc"] == ramo)
        if canal:
            mask &= (df["Apertura_Canal_Desc"] == canal)
        if amparo:
            mask &= (df["Apertura_Amparo_Desc"] == amparo)
        
        # Filtrar por fecha
        if fecha_inicio and fecha_fin:
            if "Fecha_Siniestro" in df.columns:
                df["Fecha_Siniestro"] = pd.to_datetime(df["Fecha_Siniestro"])
                mask &= (df["Fecha_Siniestro"] >= fecha_inicio) & (df["Fecha_Siniestro"] <= fecha_fin)
        
        # Aplicar filtros
        filtered_df = df[mask]
        
        result = filtered_df.to_dict('records')
        print(f"Filtrado: {time.time() - start:.2f} segundos, {len(filtered_df)} filas")
        return result
    
    
    # Callback para filtrar datos según las selecciones
    @app.callback(
        Output("stored-filtered-data", "data"),
        [
            Input("stored-processed-data", "data"),
            Input("ramo", "value"),
            Input("canal", "value"),
            Input("amparo", "value"),
            Input("rango_fechas", "start_date"),
            Input("rango_fechas", "end_date")
        ]
    )
    def filter_data(processed_data, ramo, canal, amparo, fecha_inicio, fecha_fin):
        """Filtra los datos según las selecciones de usuario."""
        # Usar la versión cacheada
        return cached_filter_data(processed_data, ramo, canal, amparo, fecha_inicio, fecha_fin)