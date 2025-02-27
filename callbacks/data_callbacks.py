import pandas as pd
import numpy as np
from dash import Input, Output, callback_context
import plotly.graph_objects as go
import time
import json
import hashlib

from data.data_loader import load_expuestos
from data.data_processor import asignar_periodos, calcular_tiempo_desarrollo, crear_triangulo_siniestralidad
from data.data_processor import calcular_factores_desarrollo, procesar_expuestos, calcular_siniestralidad_ultima
from components.charts import generate_bar_chart_figure, generate_line_chart_figure


def register_data_callbacks(app, cache):
    """
    Registra los callbacks para el procesamiento y visualización de datos.
    
    Args:
        app: Aplicación Dash
        cache: Objeto de caché de Flask
    """
    
    # Callback optimizado para métricas usando cálculos eficientes
    @app.callback(
        [
            Output("total_siniestros", "children"),
            Output("siniestros_pagados", "children"),
            Output("total_pagos", "children"),
            Output("total_incurrido", "children")
        ],
        [
            Input("stored-filtered-data", "data"),
            Input("tipo_valor", "value")
        ]
    )
    def update_metrics(filtered_data, tipo_valor):
        """Actualiza las métricas basadas en los datos filtrados."""
        if not filtered_data:
            return "0", "0", "$0", "$0"
        
        start = time.time()
        
        # Extraer solo las columnas necesarias para eficiencia (en lugar de convertir todo)
        pago_columna = f"Pago_{tipo_valor}"
        valor_columna = "Valor"
        
        # Calcular métricas directamente desde los diccionarios
        total_siniestros = len(filtered_data)
        
        # Usar comprensión de listas para mayor velocidad
        siniestros_pagados = sum(1 for item in filtered_data if item.get(pago_columna, 0) > 0)
        total_pagos = sum(item.get(pago_columna, 0) for item in filtered_data)
        total_incurrido = sum(item.get(valor_columna, item.get(pago_columna, 0)) for item in filtered_data)
        
        print(f"Cálculo de métricas: {time.time() - start:.2f} segundos")
        
        # Formatear métricas
        return (
            f"{total_siniestros:,}",
            f"{siniestros_pagados:,}",
            f"${total_pagos:,.0f}",
            f"${total_incurrido:,.0f}"
        )
    
    
    # Versión cacheada para cálculos de gráficos
    @cache.memoize()
    def cached_calculate_chart_data(filtered_data, tipo_valor, chart_type):
        """Calcula datos para gráficos de manera optimizada y cacheada"""
        if not filtered_data:
            return None
        
        start = time.time()
        
        # Convertir a DataFrame solo las columnas necesarias
        pago_columna = f"Pago_{tipo_valor}"
        
        # Determinar las columnas que necesitamos
        if chart_type == "bar":
            periodo_col = "Periodo_Ocurrencia"
        else:  # line
            periodo_col = "Periodo_Desarrollo"
        
        # Extraer solo las columnas que necesitamos
        df_mini = pd.DataFrame({
            periodo_col: [item.get(periodo_col) for item in filtered_data],
            "Conteo_Incurrido": [item.get("Conteo_Incurrido") for item in filtered_data],
            pago_columna: [item.get(pago_columna, 0) for item in filtered_data]
        })
        
        # Convertir fechas
        df_mini[periodo_col] = pd.to_datetime(df_mini[periodo_col])
        
        # Agrupar para calcular resumen
        resumen = df_mini.groupby(periodo_col).agg(
            Total_Siniestros=("Conteo_Incurrido", "nunique"),
            Siniestros_Con_Pago=(pago_columna, lambda x: (x > 0).sum()),
            Total_Pagos=(pago_columna, "sum")
        ).reset_index()
        
        # Ordenar por fecha
        resumen = resumen.sort_values(periodo_col)
        
        print(f"Cálculo de datos para gráfico {chart_type}: {time.time() - start:.2f} segundos")
        return resumen.to_dict('records')
    
    
    # Callback para el gráfico de barras de ocurrencia
    @app.callback(
        Output("grafico_barras_ocurrencia", "figure"),
        [
            Input("stored-filtered-data", "data"),
            Input("tipo_valor", "value")
        ]
    )
    def update_bar_chart(filtered_data, tipo_valor):
        """Actualiza el gráfico de barras de ocurrencia."""
        if not filtered_data:
            return go.Figure()
        
        # Usar datos cacheados
        chart_data = cached_calculate_chart_data(filtered_data, tipo_valor, "bar")
        
        if not chart_data:
            return go.Figure()
        
        # Convertir a DataFrame para el generador de gráficos
        df = pd.DataFrame(chart_data)
        
        # Generar figura
        return generate_bar_chart_figure(
            df=df,
            x_col="Periodo_Ocurrencia",
            y_cols=["Total_Pagos"],
            names=["Total Pagos"],
            colors=["#00338D"],
            title="Siniestros por Período de Ocurrencia",
            x_title="Período de Ocurrencia",
            y_title="Valor"
        )
    
    
    # Callback para el gráfico de líneas de desarrollo
    @app.callback(
        Output("grafico_lineas_desarrollo", "figure"),
        [
            Input("stored-filtered-data", "data"),
            Input("tipo_valor", "value")
        ]
    )
    def update_line_chart(filtered_data, tipo_valor):
        """Actualiza el gráfico de líneas de desarrollo."""
        if not filtered_data:
            return go.Figure()
        
        # Usar datos cacheados
        chart_data = cached_calculate_chart_data(filtered_data, tipo_valor, "line")
        
        if not chart_data:
            return go.Figure()
        
        # Convertir a DataFrame para el generador de gráficos
        df = pd.DataFrame(chart_data)
        
        # Generar figura
        return generate_line_chart_figure(
            df=df,
            x_col="Periodo_Desarrollo",
            y_cols=["Total_Pagos"],
            names=["Total Pagos"],
            colors=["#00338D"],
            title="Siniestros por Período de Desarrollo",
            x_title="Período de Desarrollo",
            y_title="Valor"
        )
    
    
    # Versión cacheada para tabla de ocurrencia
    @cache.memoize()
    def cached_ocurrencia_table(filtered_data, tipo_valor):
        """Calcula datos para la tabla de ocurrencia de manera optimizada y cacheada"""
        if not filtered_data:
            return [], []
        
        start = time.time()
        
        # Pago columna basado en tipo de valor
        pago_columna = f"Pago_{tipo_valor}"
        
        # Crear un DataFrame mínimo con solo las columnas necesarias
        df_mini = pd.DataFrame({
            "Periodo_Ocurrencia": [item.get("Periodo_Ocurrencia") for item in filtered_data],
            "Conteo_Incurrido": [item.get("Conteo_Incurrido") for item in filtered_data],
            pago_columna: [item.get(pago_columna, 0) for item in filtered_data]
        })
        
        # Convertir fecha a datetime
        df_mini["Periodo_Ocurrencia"] = pd.to_datetime(df_mini["Periodo_Ocurrencia"])
        
        # Agrupar por período de ocurrencia
        resumen_ocurrencia = df_mini.groupby("Periodo_Ocurrencia").agg(
            Total_Siniestros=("Conteo_Incurrido", "nunique"),
            Siniestros_Con_Pago=(pago_columna, lambda x: (x > 0).sum()),
            Total_Pagos=(pago_columna, "sum")
        ).reset_index()
        
        # Calcular porcentaje de pagados de manera segura
        resumen_ocurrencia["Porcentaje_Pagados"] = np.where(
            resumen_ocurrencia["Total_Siniestros"] > 0,
            (resumen_ocurrencia["Siniestros_Con_Pago"] / resumen_ocurrencia["Total_Siniestros"] * 100).round(1),
            0
        )
        
        # Ordenar por fecha descendente
        resumen_ocurrencia = resumen_ocurrencia.sort_values("Periodo_Ocurrencia", ascending=False)
        
        # Convertir fechas a string para JSON
        resumen_ocurrencia["Periodo_Ocurrencia"] = resumen_ocurrencia["Periodo_Ocurrencia"].dt.strftime("%Y-%m-%d")
        
        # Crear columnas para la tabla
        columns = [
            {"name": "Período de Ocurrencia", "id": "Periodo_Ocurrencia"},
            {"name": "Total Siniestros", "id": "Total_Siniestros", "type": "numeric", "format": {"specifier": ","}},
            {"name": "Siniestros Pagados", "id": "Siniestros_Con_Pago", "type": "numeric", "format": {"specifier": ","}},
            {"name": "Total Pagos", "id": "Total_Pagos", "type": "numeric", "format": {"specifier": "$,.0f"}},
            {"name": "% Pagados", "id": "Porcentaje_Pagados", "type": "numeric", "format": {"specifier": ".1f%"}}
        ]
        
        print(f"Cálculo de tabla de ocurrencia: {time.time() - start:.2f} segundos")
        return resumen_ocurrencia.to_dict('records'), columns
    
    
    # Callback para la tabla de ocurrencia
    @app.callback(
        Output("tabla_ocurrencia", "data"),
        Output("tabla_ocurrencia", "columns"),
        [
            Input("stored-filtered-data", "data"),
            Input("tipo_valor", "value")
        ]
    )
    def update_ocurrencia_table(filtered_data, tipo_valor):
        """Actualiza la tabla de resumen por período de ocurrencia."""
        return cached_ocurrencia_table(filtered_data, tipo_valor)
    
    
    # Versión cacheada para datos de expuestos
    @cache.memoize()
    def cached_expuestos_data(periodicidad, ramo, canal, amparo):
        """Procesa y almacena los datos de expuestos de manera cacheada"""
        start = time.time()
        
        try:
            expuestos = load_expuestos()
            
            if expuestos.empty:
                print("No se encontraron datos de expuestos")
                return []
            
            # Procesar expuestos con filtros
            expuestos_procesados = procesar_expuestos(
                expuestos,
                periodicidad,
                ramo if ramo else None,
                canal if canal else None,
                amparo if amparo else None
            )
            
            # Convertir fechas a string para JSON
            if "Periodo" in expuestos_procesados.columns:
                expuestos_procesados["Periodo"] = pd.to_datetime(expuestos_procesados["Periodo"]).dt.strftime("%Y-%m-%d")
            
            print(f"Procesamiento de expuestos: {time.time() - start:.2f} segundos")
            return expuestos_procesados.to_dict('records')
        except Exception as e:
            print(f"Error en procesar expuestos: {str(e)}")
            return []
    
    
    # Callback para procesar datos de expuestos
    @app.callback(
        Output("stored-expuestos-data", "data"),
        [
            Input("periodicidad", "value"),
            Input("ramo", "value"),
            Input("canal", "value"),
            Input("amparo", "value")
        ]
    )
    def update_expuestos_data(periodicidad, ramo, canal, amparo):
        """Procesa y almacena los datos de expuestos."""
        return cached_expuestos_data(periodicidad, ramo, canal, amparo)
    
    
    # Versión cacheada para crear triángulo
    @cache.memoize()
    def cached_triangle_data(filtered_data, periodicidad, tipo_valor, tipo_triangulo):
        """Calcula y actualiza los datos del triángulo de siniestralidad de manera cacheada"""
        if not filtered_data:
            return None
        
        start = time.time()
        
        try:
            # Convertir a DataFrame
            df = pd.DataFrame(filtered_data)
            
            # Verificar que hay datos suficientes
            if len(df) == 0:
                print("DataFrame vacío al crear triángulo")
                return None
            
            # Procesar datos adicionales
            df = asignar_periodos(df)
            df = calcular_tiempo_desarrollo(df)
            
            # Crear triángulo
            triangulo = crear_triangulo_siniestralidad(df, periodicidad, tipo_valor, tipo_triangulo)
            
            # Verificar que el triángulo no está vacío
            if triangulo.empty:
                print("Triángulo resultante está vacío")
                return None
            
            # Reindexar para asegurar que los índices son strings para JSON
            triangulo = triangulo.reset_index()
            index_col = triangulo.columns[0]
            
            # Convertir fechas a string en el índice
            if pd.api.types.is_datetime64_any_dtype(triangulo[index_col]):
                triangulo[index_col] = triangulo[index_col].dt.strftime("%Y-%m-%d")
            
            # Renombrar la columna de índice si es necesario
            if index_col != "index":
                triangulo = triangulo.rename(columns={index_col: "index"})
            
            # Guardar los resultados convertidos para JSON
            result = {
                "index": triangulo["index"].tolist(),
                "columns": [str(col) for col in triangulo.columns if col != "index"],
                "data": triangulo.to_dict('records')
            }
            
            print(f"Creación de triángulo: {time.time() - start:.2f} segundos")
            return result
        except Exception as e:
            print(f"Error en triángulo: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    
    # Callback para actualizar datos del triángulo
    @app.callback(
        Output("stored-triangle-data", "data"),
        [
            Input("stored-filtered-data", "data"),
            Input("periodicidad", "value"),
            Input("tipo_valor", "value"),
            Input("tipo_triangulo", "value")
        ]
    )
    def update_triangle_data(filtered_data, periodicidad, tipo_valor, tipo_triangulo):
        """Calcula y actualiza los datos del triángulo de siniestralidad."""
        return cached_triangle_data(filtered_data, periodicidad, tipo_valor, tipo_triangulo)
    
    
    # Versión cacheada para cálculo de factores
    @cache.memoize()
    def cached_factors_data(triangle_data):
        """Calcula y actualiza los datos de factores de desarrollo de manera cacheada"""
        if not triangle_data:
            return None
        
        start = time.time()
        
        try:
            # Reconstruir el DataFrame del triángulo
            index = triangle_data["index"]
            columns = [int(col) for col in triangle_data["columns"]]
            
            # Crear DataFrame vacío
            triangulo = pd.DataFrame(index=index, columns=columns)
            
            # Llenar con los datos
            data_records = triangle_data["data"]
            for record in data_records:
                if "index" not in record:
                    continue
                
                row_idx = record["index"]
                for col in columns:
                    col_str = str(col)
                    if col_str in record and not pd.isna(record[col_str]):
                        triangulo.loc[row_idx, col] = record[col_str]
            
            # Calcular factores
            factores, estadisticas, factores_promedio, factores_acumulados = calcular_factores_desarrollo(triangulo)
            
            # Preparar para JSON
            result = {
                "factores": {
                    "index": factores.index.astype(str).tolist(),
                    "columns": [str(col) for col in factores.columns.tolist()],
                    "data": factores.reset_index().to_dict('records')
                },
                "estadisticas": estadisticas.to_dict('records'),
                "factores_promedio": factores_promedio.tolist(),
                "factores_acumulados": factores_acumulados.tolist()
            }
            
            print(f"Cálculo de factores: {time.time() - start:.2f} segundos")
            return result
        except Exception as e:
            print(f"Error en factores: {str(e)}")
            return None
    
    
    # Callback para actualizar datos de factores
    @app.callback(
        Output("stored-factors-data", "data"),
        Input("stored-triangle-data", "data")
    )
    def update_factors_data(triangle_data):
        """Calcula y actualiza los datos de factores de desarrollo."""
        return cached_factors_data(triangle_data)
    
    
    # Versión cacheada para cálculo de siniestralidad última
    @cache.memoize()
    def cached_ultima_data(triangle_data, factors_data, expuestos_data, metodo_calculo, periodicidad, tipo_triangulo):
        """Calcula la siniestralidad última de manera cacheada"""
        if not triangle_data or not factors_data or not expuestos_data:
            return None
        
        start = time.time()
        
        try:
            # Reconstruir el DataFrame del triángulo
            index = triangle_data["index"]
            columns = [int(col) for col in triangle_data["columns"]]
            
            # Crear DataFrame vacío
            triangulo = pd.DataFrame(index=index, columns=columns)
            
            # Llenar con los datos
            data_records = triangle_data["data"]
            for record in data_records:
                if "index" not in record:
                    continue
                
                row_idx = record["index"]
                for col in columns:
                    col_str = str(col)
                    if col_str in record and pd.notna(record[col_str]):
                        triangulo.loc[row_idx, col] = record[col_str]
            
            # Obtener factores
            factores_promedio = np.array(factors_data["factores_promedio"])
            factores_acumulados = np.array(factors_data["factores_acumulados"])
            
            # Crear DataFrame de expuestos
            expuestos = pd.DataFrame(expuestos_data)
            if not expuestos.empty and "Periodo" in expuestos.columns:
                expuestos["Periodo"] = pd.to_datetime(expuestos["Periodo"])
            
            # Calcular siniestralidad última
            resultado = calcular_siniestralidad_ultima(
                triangulo,
                factores_promedio,
                factores_acumulados,
                expuestos,
                metodo_calculo,
                periodicidad,
                tipo_triangulo
            )
            
            print(f"Cálculo de siniestralidad última: {time.time() - start:.2f} segundos")
            return resultado.to_dict('records')
        except Exception as e:
            print(f"Error en cálculo de siniestralidad última: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    
    # Callback para calcular siniestralidad última
    @app.callback(
        Output("stored-ultima-data", "data"),
        [
            Input("stored-triangle-data", "data"),
            Input("stored-factors-data", "data"),
            Input("stored-expuestos-data", "data"),
            Input("metodo_calculo", "value"),
            Input("periodicidad", "value"),
            Input("tipo_triangulo", "value")
        ]
    )
    def update_ultima_data(triangle_data, factors_data, expuestos_data, metodo_calculo, periodicidad, tipo_triangulo):
        """Calcula la siniestralidad última."""
        return cached_ultima_data(triangle_data, factors_data, expuestos_data, metodo_calculo, periodicidad, tipo_triangulo)
    
    
    # Callback para la tabla de triángulo
    @app.callback(
        Output("triangulo", "data"),
        Output("triangulo", "columns"),
        Input("stored-triangle-data", "data")
    )
    def update_triangle_table(triangle_data):
        """Actualiza la tabla del triángulo de siniestralidad."""
        if not triangle_data:
            print("No hay datos de triángulo disponibles")
            return [], []
        
        try:
            # Verificar la estructura de los datos
            if "index" not in triangle_data or "columns" not in triangle_data or "data" not in triangle_data:
                print("Estructura de datos de triángulo incorrecta:", triangle_data.keys())
                return [], []
            
            # Extraer datos
            data_records = triangle_data["data"]
            
            # Verificar si hay registros
            if not data_records:
                print("No hay registros en los datos del triángulo")
                return [], []
            
            # Asegurarse de que cada registro tenga 'index'
            for record in data_records:
                if "index" not in record:
                    record["index"] = ""
            
            # Definir columnas
            columns = [{"name": "Período", "id": "index"}]
            
            for col in triangle_data["columns"]:
                try:
                    col_name = f"Desarrollo {col}"
                    columns.append({
                        "name": col_name,
                        "id": col,
                        "type": "numeric",
                        "format": {"specifier": "$,.0f"}
                    })
                except Exception as e:
                    print(f"Error al procesar columna {col}: {str(e)}")
            
            return data_records, columns
        except Exception as e:
            print(f"Error en tabla de triángulo: {str(e)}")
            return [], []
    
    
    # Callback para la tabla de factores
    @app.callback(
        Output("tabla_factores", "data"),
        Output("tabla_factores", "columns"),
        Input("stored-factors-data", "data")
    )
    def update_factors_table(factors_data):
        """Actualiza la tabla de factores de desarrollo."""
        if not factors_data:
            return [], []
        
        try:
            # Extraer datos
            data_records = factors_data["factores"]["data"]
            columns = [{"name": "Período", "id": "index"}]
            
            for col in factors_data["factores"]["columns"]:
                col_name = f"Desarrollo {col}"
                columns.append({
                    "name": col_name,
                    "id": col,
                    "type": "numeric",
                    "format": {"specifier": ",.4f"}
                })
            
            return data_records, columns
        except Exception as e:
            print(f"Error en tabla de factores: {str(e)}")
            return [], []
    
    
    # Callback para la tabla de estadísticas de factores
    @app.callback(
        Output("tabla_estadisticas_factores", "data"),
        Output("tabla_estadisticas_factores", "columns"),
        Input("stored-factors-data", "data")
    )
    def update_factor_stats_table(factors_data):
        """Actualiza la tabla de estadísticas de factores."""
        if not factors_data:
            return [], []
        
        try:
            # Extraer datos
            data_records = factors_data["estadisticas"]
            
            # Crear columnas
            columns = []
            for record in data_records:
                for key in record.keys():
                    if key not in [col["id"] for col in columns]:
                        col_format = {"specifier": ",.4f"} if key != "Estadistica" else None
                        col_type = "numeric" if key != "Estadistica" else "text"
                        
                        columns.append({
                            "name": key,
                            "id": key,
                            "type": col_type,
                            "format": col_format
                        })
            
            return data_records, columns
        except Exception as e:
            print(f"Error en tabla de estadísticas: {str(e)}")
            return [], []
    
    
    # Callback para la tabla de siniestralidad última
    @app.callback(
        Output("tabla_resumen_ultima", "data"),
        Output("tabla_resumen_ultima", "columns"),
        Input("stored-ultima-data", "data")
    )
    def update_ultima_table(ultima_data):
        """Actualiza la tabla de resumen de siniestralidad última."""
        if not ultima_data:
            return [], []
        
        try:
            # Crear columnas
            columns = [
                {"name": "Período", "id": "Periodo"},
                {"name": "Método", "id": "Metodo"},
                {"name": "Expuestos", "id": "Expuestos", "type": "numeric", "format": {"specifier": ","}},
                {"name": "Valor Inicial", "id": "Valor_Inicial", "type": "numeric", "format": {"specifier": "$,.0f"}},
                {"name": "Valor Actual", "id": "Valor_Actual", "type": "numeric", "format": {"specifier": "$,.0f"}},
                {"name": "Siniestralidad Última", "id": "Siniestralidad_Ultima", "type": "numeric", "format": {"specifier": "$,.0f"}},
                {"name": "IBNR", "id": "IBNR", "type": "numeric", "format": {"specifier": "$,.0f"}},
                {"name": "Factor Desarrollo", "id": "Factor_Desarrollo", "type": "numeric", "format": {"specifier": ",.4f"}},
                {"name": "Loss Ratio", "id": "Loss_Ratio", "type": "numeric", "format": {"specifier": ",.4f"}}
            ]
            
            # Verificar si hay columna de Indicador (para triángulos de frecuencia)
            if ultima_data and "Indicador" in ultima_data[0]:
                columns.append({"name": "Indicador (%)", "id": "Indicador", "type": "numeric", "format": {"specifier": ",.4f"}})
            
            return ultima_data, columns
        except Exception as e:
            print(f"Error en tabla de siniestralidad última: {str(e)}")
            return [], []
    
    
    # Callback para descarga de datos
    @app.callback(
        Output("download-data", "data"),
        Input("descargar_datos", "n_clicks"),
        [
            Input("stored-triangle-data", "data"),
            Input("tipo_valor", "value"),
            Input("tipo_triangulo", "value")
        ],
        prevent_initial_call=True
    )
    def download_data(n_clicks, triangle_data, tipo_valor, tipo_triangulo):
        """Prepara los datos para descarga."""
        if not n_clicks or not triangle_data:
            return None
        
        try:
            # Reconstruir el triángulo
            index = triangle_data["index"]
            columns = [int(col) for col in triangle_data["columns"]]
            
            # Crear DataFrame para la descarga
            download_df = pd.DataFrame(index=index)
            for i, idx in enumerate(index):
                for col in columns:
                    col_str = str(col)
                    for record in triangle_data["data"]:
                        if record.get("index") == idx and col_str in record:
                            download_df.loc[idx, col_str] = record[col_str]
            
            # Preparar para descarga
            from datetime import datetime
            prefix_tipo = tipo_triangulo
            prefix_valor = tipo_valor.lower()
            filename = f"triangulo_{prefix_tipo}_{prefix_valor}_{datetime.now().strftime('%Y%m%d')}.csv"
            
            return dict(
                content=download_df.to_csv(),
                filename=filename
            )
        except Exception as e:
            print(f"Error en descarga de datos: {str(e)}")
            return None