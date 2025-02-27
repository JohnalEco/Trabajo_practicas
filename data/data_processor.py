import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import math

def procesar_siniestros(df, periodicidad="mes", tipo_triangulo="plata", 
                       tipo_valor="Bruto", agrupacion_reservas=None, ramo=None, 
                       canal=None, amparo=None, fecha_inicio=None, fecha_fin=None):
    """
    Procesa los datos de siniestros aplicando filtros y transformaciones.
    Versión optimizada para mejor rendimiento.
    
    Args:
        df: DataFrame con los datos de siniestros
        periodicidad: Periodicidad para agrupar los datos ('mes', 'trimestre', 'año')
        tipo_triangulo: Tipo de triángulo a calcular ('plata', 'severidad', 'frecuencia')
        tipo_valor: Tipo de valor a usar ('Bruto', 'Retenido')
        agrupacion_reservas: Filtro de agrupación de reservas
        ramo: Filtro de ramo
        canal: Filtro de canal
        amparo: Filtro de amparo
        fecha_inicio: Fecha de inicio para filtrar
        fecha_fin: Fecha de fin para filtrar
    
    Returns:
        DataFrame procesado
    """
    # Crear una vista para no modificar el original (más eficiente que copy())
    df_view = df
    
    # Aplicar filtros al inicio para reducir el tamaño del DataFrame
    print(f"Iniciando filtrado con {len(df_view)} filas")
    
    # Crear una máscara de filtro
    mask = np.ones(len(df_view), dtype=bool)
    
    if agrupacion_reservas and agrupacion_reservas != "":
        mask &= (df_view["Agrupacion_Reservas"] == agrupacion_reservas)
    
    if ramo and ramo != "":
        mask &= (df_view["Ramo_Desc"] == ramo)
    
    if canal and canal != "":
        mask &= (df_view["Apertura_Canal_Desc"] == canal)
    
    if amparo and amparo != "":
        mask &= (df_view["Apertura_Amparo_Desc"] == amparo)
    
    if fecha_inicio and fecha_fin:
        mask &= (df_view["Fecha_Siniestro"] >= fecha_inicio) & (df_view["Fecha_Siniestro"] <= fecha_fin)
    
    # Aplicar todos los filtros de una vez (más eficiente)
    df_filtered = df_view[mask].copy()
    print(f"Después de filtrado: {len(df_filtered)} filas")
    
    # Si después de filtrar no quedan datos, devolver un DataFrame vacío
    if df_filtered.empty:
        return pd.DataFrame()
    
    # Calcular frecuencia (número de siniestros por fecha)
    frecuencia = df_filtered.groupby("Fecha_Siniestro").size()
    
    # Función para asignar la frecuencia (más eficiente que merge)
    def get_frecuencia(fecha):
        return frecuencia.get(fecha, 1)
    
    # Vectorizar la función para mayor velocidad
    vectorized_get_freq = np.vectorize(get_frecuencia)
    
    # Calcular frecuencia para cada fila
    df_filtered["Frecuencia"] = vectorized_get_freq(df_filtered["Fecha_Siniestro"].values)
    
    # Calcular severidad
    df_filtered["Severidad_Bruta"] = df_filtered["Pago_Bruto"] / df_filtered["Frecuencia"]
    df_filtered["Severidad_Retenida"] = df_filtered["Pago_Retenido"] / df_filtered["Frecuencia"]
    
    # Determinar la columna de valor según el tipo de triángulo y tipo de valor
    if tipo_triangulo == "plata":
        valor_columna = "Pago_Bruto" if tipo_valor == "Bruto" else "Pago_Retenido"
    elif tipo_triangulo == "severidad":
        valor_columna = "Severidad_Bruta" if tipo_valor == "Bruto" else "Severidad_Retenida"
    else:  # frecuencia
        valor_columna = "Frecuencia"
    
    # Eliminar registros sin valor
    df_filtered = df_filtered[df_filtered[valor_columna] > 0]
    
    # Verificar que queden datos después de los filtros
    if df_filtered.empty:
        return pd.DataFrame()
    
    # Añadir columna de valor
    df_filtered["Valor"] = df_filtered[valor_columna]
    
    # Agregar una columna única de conteo de manera optimizada
    df_filtered["Conteo_Incurrido"] = np.arange(1, len(df_filtered) + 1)
    
    # Definir períodos según periodicidad (usando métodos vectorizados)
    if periodicidad == "mes":
        df_filtered["Periodo_Ocurrencia"] = pd.to_datetime(
            df_filtered["Fecha_Siniestro"].dt.year.astype(str) + "-" + 
            df_filtered["Fecha_Siniestro"].dt.month.astype(str) + "-01"
        )
        df_filtered["Periodo_Desarrollo"] = pd.to_datetime(
            df_filtered["Fecha_Registro"].dt.year.astype(str) + "-" + 
            df_filtered["Fecha_Registro"].dt.month.astype(str) + "-01"
        )
    elif periodicidad == "trimestre":
        df_filtered["Periodo_Ocurrencia"] = pd.to_datetime(
            df_filtered["Fecha_Siniestro"].dt.year.astype(str) + "-" + 
            ((df_filtered["Fecha_Siniestro"].dt.month - 1) // 3 * 3 + 1).astype(str) + "-01"
        )
        df_filtered["Periodo_Desarrollo"] = pd.to_datetime(
            df_filtered["Fecha_Registro"].dt.year.astype(str) + "-" + 
            ((df_filtered["Fecha_Registro"].dt.month - 1) // 3 * 3 + 1).astype(str) + "-01"
        )
    elif periodicidad == "año":
        df_filtered["Periodo_Ocurrencia"] = pd.to_datetime(
            df_filtered["Fecha_Siniestro"].dt.year.astype(str) + "-01-01"
        )
        df_filtered["Periodo_Desarrollo"] = pd.to_datetime(
            df_filtered["Fecha_Registro"].dt.year.astype(str) + "-01-01"
        )
    
    print(f"Procesamiento finalizado: {len(df_filtered)} filas")
    return df_filtered

def asignar_periodos(df):
    """
    Asigna períodos adicionales a los datos procesados.
    Versión optimizada para mejor rendimiento.
    
    Args:
        df: DataFrame con datos procesados
    
    Returns:
        DataFrame con períodos adicionales
    """
    # Usar una copia para no modificar el original
    df_result = df.copy()
    
    # Convertir a datetime si no lo es, sólo si es necesario
    if "Periodo_Ocurrencia" in df_result.columns and df_result["Periodo_Ocurrencia"].dtype != "datetime64[ns]":
        df_result["Periodo_Ocurrencia"] = pd.to_datetime(df_result["Periodo_Ocurrencia"])
    
    # Asignar períodos con métodos vectorizados
    if "Periodo_Ocurrencia" in df_result.columns:
        # Trimestre: primer día del trimestre correspondiente
        df_result["Trimestre_Ocurrencia"] = pd.to_datetime(
            df_result["Periodo_Ocurrencia"].dt.year.astype(str) + "-" + 
            ((df_result["Periodo_Ocurrencia"].dt.month - 1) // 3 * 3 + 1).astype(str) + "-01"
        )
        
        # Mes: primer día del mes
        df_result["Mes_Ocurrencia"] = pd.to_datetime(
            df_result["Periodo_Ocurrencia"].dt.year.astype(str) + "-" + 
            df_result["Periodo_Ocurrencia"].dt.month.astype(str) + "-01"
        )
        
        # Año: primer día del año
        df_result["Año_Ocurrencia"] = pd.to_datetime(
            df_result["Periodo_Ocurrencia"].dt.year.astype(str) + "-01-01"
        )
    
    return df_result


def calcular_tiempo_desarrollo(df):
    """
    Calcula el tiempo de desarrollo entre la fecha de siniestro y registro.
    Versión optimizada para mejor rendimiento.
    
    Args:
        df: DataFrame con datos procesados
    
    Returns:
        DataFrame con tiempos de desarrollo
    """
    # Crear una copia para no modificar el original
    df_result = df.copy()
    
    # Convertir a datetime si no lo es, solo si es necesario
    for col in ["Fecha_Siniestro", "Fecha_Registro"]:
        if col in df_result.columns and df_result[col].dtype != "datetime64[ns]":
            df_result[col] = pd.to_datetime(df_result[col])
    
    # Calcular la diferencia en meses usando vectorización
    if "Fecha_Siniestro" in df_result.columns and "Fecha_Registro" in df_result.columns:
        # Meses de desarrollo (más eficiente que usar relativedelta)
        df_result["Desarrollo_Meses"] = ((df_result["Fecha_Registro"].dt.year - df_result["Fecha_Siniestro"].dt.year) * 12 + 
                                      (df_result["Fecha_Registro"].dt.month - df_result["Fecha_Siniestro"].dt.month))
        
        # Trimestres: dividir meses por 3 y tomar la parte entera
        df_result["Desarrollo_Trimestres"] = df_result["Desarrollo_Meses"] // 3
        
        # Años: dividir meses por 12 y tomar la parte entera
        df_result["Desarrollo_Años"] = df_result["Desarrollo_Meses"] // 12
        
        # Asegurarse de que los desarrollos sean enteros no negativos
        df_result["Desarrollo_Meses"] = df_result["Desarrollo_Meses"].clip(lower=0).astype(np.int32)
        df_result["Desarrollo_Trimestres"] = df_result["Desarrollo_Trimestres"].clip(lower=0).astype(np.int32)
        df_result["Desarrollo_Años"] = df_result["Desarrollo_Años"].clip(lower=0).astype(np.int32)
    
    return df_result


def crear_triangulo_siniestralidad(df, periodicidad="mes", tipo_valor="Bruto", tipo_triangulo="plata"):
    """
    Crea un triángulo de siniestralidad a partir de los datos procesados.
    
    Args:
        df: DataFrame con datos procesados
        periodicidad: Periodicidad para el triángulo ('mes', 'trimestre', 'año')
        tipo_valor: Tipo de valor a usar ('Bruto', 'Retenido')
        tipo_triangulo: Tipo de triángulo ('plata', 'severidad', 'frecuencia')
    
    Returns:
        DataFrame con el triángulo de siniestralidad
    """
    print(f"Creando triángulo con tipo_triangulo={tipo_triangulo}, tipo_valor={tipo_valor}")
    
    # Determinar columnas de periodicidad y desarrollo
    periodo_col = {
        "mes": "Mes_Ocurrencia",
        "trimestre": "Trimestre_Ocurrencia",
        "año": "Año_Ocurrencia"
    }.get(periodicidad)
    
    desarrollo_col = {
        "mes": "Desarrollo_Meses",
        "trimestre": "Desarrollo_Trimestres",
        "año": "Desarrollo_Años"
    }.get(periodicidad)
    
    # Verificar que las columnas existan
    if periodo_col not in df.columns:
        print(f"Error: Columna de período '{periodo_col}' no encontrada. Columnas disponibles: {df.columns.tolist()}")
        return pd.DataFrame()
        
    if desarrollo_col not in df.columns:
        print(f"Error: Columna de desarrollo '{desarrollo_col}' no encontrada. Columnas disponibles: {df.columns.tolist()}")
        return pd.DataFrame()
    
    # Determinar la columna de valor
    if tipo_triangulo == "plata":
        valor_columna = f"Pago_{tipo_valor}"
    elif tipo_triangulo == "severidad":
        valor_columna = f"Severidad_{tipo_valor}" if tipo_valor == "Retenido" else "Severidad_Bruta"
    else:  # frecuencia
        valor_columna = "Frecuencia"
    
    # Verificar que la columna existe
    if valor_columna not in df.columns:
        print(f"Error: Columna de valor '{valor_columna}' no encontrada. Columnas disponibles: {df.columns.tolist()}")
        # Intentar usar una alternativa
        if "Valor" in df.columns:
            valor_columna = "Valor"
            print(f"Usando 'Valor' como alternativa")
        else:
            try:
                # Intentar crear las columnas necesarias
                if tipo_triangulo == "severidad":
                    if tipo_valor == "Bruto" and "Pago_Bruto" in df.columns and "Frecuencia" in df.columns:
                        df["Severidad_Bruta"] = df["Pago_Bruto"] / df["Frecuencia"]
                        valor_columna = "Severidad_Bruta"
                    elif tipo_valor == "Retenido" and "Pago_Retenido" in df.columns and "Frecuencia" in df.columns:
                        df["Severidad_Retenida"] = df["Pago_Retenido"] / df["Frecuencia"]
                        valor_columna = "Severidad_Retenida"
                    else:
                        valor_columna = "Pago_Bruto" if tipo_valor == "Bruto" else "Pago_Retenido"
                elif tipo_triangulo == "frecuencia" and "Conteo_Incurrido" in df.columns:
                    df["Frecuencia"] = 1
                    valor_columna = "Frecuencia"
                else:
                    valor_columna = "Pago_Bruto" if tipo_valor == "Bruto" else "Pago_Retenido"
            except Exception as e:
                print(f"Error al crear columna alternativa: {str(e)}")
                # Usar una columna numérica existente
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if numeric_cols:
                    valor_columna = numeric_cols[0]
                    print(f"Usando '{valor_columna}' como última alternativa")
                else:
                    print("No se encontraron columnas numéricas para usar")
                    return pd.DataFrame()
    
    print(f"Usando columna de valor: '{valor_columna}'")
    
    # Limpiar datos para evitar problemas
    df_clean = df.dropna(subset=[periodo_col, desarrollo_col, valor_columna])
    
    # Comprobar si quedan datos después de filtrar valores nulos
    if df_clean.empty:
        print("No hay datos después de eliminar valores nulos")
        return pd.DataFrame()
    
    # Asegurar que las columnas son del tipo adecuado
    df_clean[desarrollo_col] = df_clean[desarrollo_col].astype(int)
    
    print(f"Preparando triángulo con {len(df_clean)} filas válidas")
    
    # Agrupar datos para crear triángulo base
    triangulo_base = df_clean.groupby([periodo_col, desarrollo_col])[valor_columna].sum().reset_index()
    
    # Verificar si hay datos en el resultado
    if triangulo_base.empty:
        print("No hay datos después de agrupar")
        return pd.DataFrame()
    
    print(f"Triángulo base tiene {len(triangulo_base)} filas")
    
    # Crear una tabla pivote para formar el triángulo
    try:
        triangulo_pivot = pd.pivot_table(
            triangulo_base,
            values=valor_columna,
            index=periodo_col,
            columns=desarrollo_col,
            fill_value=0
        )
        
        print(f"Triángulo pivot creado con forma: {triangulo_pivot.shape}")
        print(f"Períodos: {triangulo_pivot.index.tolist()}")
        print(f"Desarrollos: {triangulo_pivot.columns.tolist()}")
        
        # Acumular valores por columna de desarrollo
        triangulo_acumulado = triangulo_pivot.copy()
        for col in range(1, len(triangulo_acumulado.columns)):
            if col in triangulo_acumulado.columns and (col - 1) in triangulo_acumulado.columns:
                triangulo_acumulado[col] = triangulo_acumulado[col] + triangulo_acumulado[col - 1]
        
        # Crear matriz final con NaN fuera de la diagonal principal
        triangulo_final = pd.DataFrame(index=triangulo_acumulado.index, columns=triangulo_acumulado.columns)
        
        for i, periodo in enumerate(triangulo_acumulado.index):
            for j, desarrollo in enumerate(triangulo_acumulado.columns):
                if j <= len(triangulo_acumulado.index) - i - 1:
                    triangulo_final.loc[periodo, desarrollo] = triangulo_acumulado.loc[periodo, desarrollo]
        
        print(f"Triángulo final creado con forma: {triangulo_final.shape}")
        
        return triangulo_final
    
    except Exception as e:
        print(f"Error al crear triángulo pivotado: {str(e)}")
        return pd.DataFrame()


def calcular_factores_desarrollo(triangulo):
    """
    Calcula factores de desarrollo a partir del triángulo de siniestralidad.
    
    Args:
        triangulo: DataFrame con el triángulo de siniestralidad
    
    Returns:
        Tuple con (factores, estadísticas, factores_promedio, factores_acumulados)
    """
    print(f"Calculando factores para triángulo con forma: {triangulo.shape}")
    
    if triangulo.empty:
        print("Triángulo vacío, no se pueden calcular factores")
        empty_df = pd.DataFrame()
        empty_stats = pd.DataFrame(columns=["Estadistica"])
        return empty_df, empty_stats, np.array([]), np.array([])
    
    # Convertir a numpy para operaciones más eficientes
    triangulo_np = triangulo.values
    
    # Determinar el número máximo de desarrollos (algunos pueden ser NaN)
    n_desarrollos = triangulo.shape[1]
    n_periodos = triangulo.shape[0]
    
    print(f"Períodos: {n_periodos}, Desarrollos: {n_desarrollos}")
    
    # Crear matriz para factores individuales - un factor menos que desarrollos
    factores_matriz = np.full((n_periodos, n_desarrollos - 1), np.nan)
    
    # Calcular factores individuales (división celda a celda)
    for i in range(n_periodos):
        for j in range(n_desarrollos - 1):
            # Solo calcular si estamos dentro de la diagonal
            if j <= n_periodos - i - 2:  # -2 porque necesitamos el valor siguiente también
                actual = triangulo_np[i, j]
                siguiente = triangulo_np[i, j + 1]
                
                # Solo calcular si ambos valores son válidos y el actual es mayor que cero
                if (not np.isnan(actual) and not np.isnan(siguiente) and actual > 0):
                    factores_matriz[i, j] = siguiente / actual
    
    # Mostrar factores individuales para depuración
    print("Muestra de factores individuales:", factores_matriz[0, :5])
    
    # Calcular factores promedio ponderados (siguiendo el método ChainLadder de R)
    factores_promedio = np.ones(n_desarrollos - 1)
    for j in range(n_desarrollos - 1):
        # Suma de valores para cada columna (para numerador y denominador)
        suma_numerador = 0
        suma_denominador = 0
        
        for i in range(n_periodos):
            # Solo usar celdas dentro de la diagonal principal
            if j <= n_periodos - i - 2:
                # Obtener valores actuales y siguientes de la diagonal
                actual = triangulo_np[i, j]
                siguiente = triangulo_np[i, j + 1]
                
                # Verificar que ambos valores existan
                if not np.isnan(actual) and not np.isnan(siguiente):
                    suma_numerador += siguiente
                    suma_denominador += actual
        
        # Calcular factor como cociente de sumas (evitar división por cero)
        if suma_denominador > 0:
            factores_promedio[j] = suma_numerador / suma_denominador
        else:
            factores_promedio[j] = 1.0
    
    print("Factores promedio:", factores_promedio)
    
    # Calcular factores acumulados (empezando desde el final)
    factores_acumulados = np.ones(n_desarrollos - 1)
    
    # El último factor acumulado es igual al último factor promedio
    if len(factores_promedio) > 0:
        factores_acumulados[-1] = factores_promedio[-1]
    
    # Calcular los demás factores acumulados de derecha a izquierda
    for i in range(len(factores_promedio) - 2, -1, -1):
        factores_acumulados[i] = factores_promedio[i] * factores_acumulados[i + 1]
    
    print("Factores acumulados:", factores_acumulados)
    
    # Crear DataFrame de factores individuales
    factores_df = pd.DataFrame(
        factores_matriz, 
        index=triangulo.index,
        columns=[f"Factor_{i}" for i in range(n_desarrollos - 1)]
    )
    
    # Crear DataFrame de estadísticas
    estadisticas_dict = {
        "Estadistica": ["Factor Promedio", "Factor Acumulado", "Número de Datos", 
                      "Valor Mínimo", "Valor Máximo", "Desviación Estándar"]
    }
    
    # Calcular estadísticas para cada desarrollo
    for j in range(n_desarrollos - 1):
        col_data = factores_matriz[:, j]
        col_data = col_data[~np.isnan(col_data)]
        
        if len(col_data) > 0:
            stats = [
                factores_promedio[j],
                factores_acumulados[j],
                len(col_data),
                np.min(col_data),
                np.max(col_data),
                np.std(col_data) if len(col_data) > 1 else 0
            ]
        else:
            stats = [1.0, 1.0, 0, np.nan, np.nan, np.nan]
        
        estadisticas_dict[f"Desarrollo_{j}"] = stats
    
    estadisticas_df = pd.DataFrame(estadisticas_dict)
    
    return factores_df, estadisticas_df, factores_promedio, factores_acumulados

def calcular_siniestralidad_ultima(triangulo, factores_promedio, factores_acumulados, expuestos, 
                                  metodo_calculo="auto", periodicidad="mes", tipo_triangulo="plata"):
    """
    Calcula la siniestralidad última utilizando diferentes métodos.
    
    Args:
        triangulo: DataFrame con el triángulo de siniestralidad
        factores_promedio: Array con factores de desarrollo promedio
        factores_acumulados: Array con factores de desarrollo acumulados
        expuestos: DataFrame con datos de expuestos
        metodo_calculo: Método de cálculo ('auto', 'chain_ladder', 'bornhuetter_ferguson')
        periodicidad: Periodicidad de los datos
        tipo_triangulo: Tipo de triángulo usado
    
    Returns:
        DataFrame con resultados del cálculo
    """
    print(f"Calculando siniestralidad última con método: {metodo_calculo}")
    
    if triangulo.empty:
        print("Triángulo vacío, no se puede calcular siniestralidad última")
        return pd.DataFrame(columns=["Periodo", "Metodo", "Expuestos", "Valor_Inicial", 
                                     "Valor_Actual", "Siniestralidad_Ultima", "IBNR", 
                                     "Factor_Desarrollo", "Loss_Ratio"])
    
    # Convertir triángulo a numpy para operaciones eficientes
    triangulo_np = triangulo.values
    periodos = triangulo.index.tolist()
    
    # Identificar períodos recientes según periodicidad
    fechas_periodos = pd.to_datetime(periodos)
    ultimo_periodo = max(fechas_periodos)
    
    # Definir período reciente según periodicidad
    if periodicidad == "mes":
        periodo_reciente = ultimo_periodo - pd.DateOffset(years=1)
    elif periodicidad == "trimestre":
        periodo_reciente = ultimo_periodo - pd.DateOffset(years=1)
    else:  # año
        periodo_reciente = ultimo_periodo - pd.DateOffset(years=1)
    
    es_periodo_reciente = fechas_periodos >= periodo_reciente
    
    # Encontrar últimos valores conocidos y sus posiciones
    valores_actuales = []
    posiciones_actuales = []
    
    for i in range(triangulo_np.shape[0]):
        # Encontrar la última columna no-NaN para esta fila
        ultima_col = -1
        for j in range(triangulo_np.shape[1]):
            if not np.isnan(triangulo_np[i, j]):
                ultima_col = j
        
        if ultima_col >= 0:
            valores_actuales.append(triangulo_np[i, ultima_col])
            posiciones_actuales.append(ultima_col)
        else:
            valores_actuales.append(np.nan)
            posiciones_actuales.append(-1)
    
    # Convertir a arrays de numpy
    valores_actuales = np.array(valores_actuales)
    posiciones_actuales = np.array(posiciones_actuales)
    
    # Obtener valores iniciales del triángulo (primera columna)
    valores_iniciales = triangulo_np[:, 0].copy()
    for i in range(len(valores_iniciales)):
        if np.isnan(valores_iniciales[i]):
            valores_iniciales[i] = 0
    
    # Preparar expuestos
    expuestos_dict = {}
    if not expuestos.empty and "Periodo" in expuestos.columns and "Total_Expuestos" in expuestos.columns:
        # Convertir a datetime si es string
        if expuestos["Periodo"].dtype == object:
            expuestos["Periodo"] = pd.to_datetime(expuestos["Periodo"])
        
        # Crear diccionario para mapear expuestos a períodos
        expuestos_dict = dict(zip(expuestos["Periodo"].astype(str), expuestos["Total_Expuestos"]))
    
    # Obtener expuestos para cada período
    expuestos_valores = []
    for periodo in periodos:
        # Intentar encontrar expuestos para este período
        exp_val = expuestos_dict.get(str(periodo), 0)
        expuestos_valores.append(exp_val if exp_val > 0 else 1000)  # Valor por defecto si no hay datos
    
    # Calcular ratio histórico usando períodos no recientes para Bornhuetter-Ferguson
    periodos_historicos = ~es_periodo_reciente
    if np.any(periodos_historicos):
        valores_iniciales_historicos = valores_iniciales[periodos_historicos]
        expuestos_historicos = np.array([expuestos_valores[i] for i in range(len(periodos_historicos)) 
                                         if periodos_historicos[i]])
        
        # Calcular ratio (evitar división por cero)
        if np.sum(expuestos_historicos) > 0:
            ratio_historico = np.sum(valores_iniciales_historicos) / np.sum(expuestos_historicos)
        else:
            ratio_historico = 0.01  # Valor por defecto
    else:
        ratio_historico = 0.01
    
    print(f"Ratio histórico calculado: {ratio_historico:.4f}")
    
    # Calcular siniestralidad última
    siniestralidad_ultima = np.zeros(len(valores_actuales))
    metodos_usados = []
    
    for i in range(len(valores_actuales)):
        # Determinar método a usar
        if metodo_calculo == "auto":
            # Automático: Bornhuetter-Ferguson para períodos recientes, Chain Ladder para el resto
            metodo = "bornhuetter_ferguson" if es_periodo_reciente[i] else "chain_ladder"
        else:
            # Usar el método seleccionado
            metodo = metodo_calculo
        
        metodos_usados.append(metodo)
        
        # Calcular según el método
        pos = posiciones_actuales[i]
        valor_actual = valores_actuales[i]
        expuesto = expuestos_valores[i]
        
        if np.isnan(valor_actual) or pos < 0:
            siniestralidad_ultima[i] = 0
            continue
        
        if metodo == "bornhuetter_ferguson" and pos < len(factores_acumulados):
            # Método Bornhuetter-Ferguson
            factor_acum = factores_acumulados[pos]
            
            # Fórmula de Bornhuetter-Ferguson
            parte_reportada = valor_actual
            parte_no_reportada = expuesto * ratio_historico * (1 - 1/factor_acum) if factor_acum > 1.0 else 0
            siniestralidad_ultima[i] = parte_reportada + parte_no_reportada
        else:
            # Método Chain Ladder
            if pos < len(factores_acumulados):
                siniestralidad_ultima[i] = valor_actual * factores_acumulados[pos]
            else:
                siniestralidad_ultima[i] = valor_actual  # Si ya está en el último desarrollo
    
    # Crear DataFrame con resultados
    resultados = pd.DataFrame({
        "Periodo": periodos,
        "Metodo": metodos_usados,
        "Expuestos": expuestos_valores,
        "Valor_Inicial": valores_iniciales,
        "Valor_Actual": valores_actuales,
        "Siniestralidad_Ultima": siniestralidad_ultima,
        "IBNR": siniestralidad_ultima - valores_actuales,
        "Factor_Desarrollo": np.where(valores_actuales > 0, 
                                      siniestralidad_ultima / valores_actuales,
                                      np.nan)
    })
    
    # Calcular Loss Ratio
    resultados["Loss_Ratio"] = np.where(np.array(expuestos_valores) > 0,
                                       resultados["Siniestralidad_Ultima"] / np.array(expuestos_valores),
                                       np.nan)
    
    # Añadir indicador para triángulo de frecuencia
    if tipo_triangulo == "frecuencia":
        resultados["Indicador"] = np.where(np.array(expuestos_valores) > 0,
                                          (resultados["Siniestralidad_Ultima"] / np.array(expuestos_valores)) * 100,
                                          np.nan)
    
    # Calcular totales
    total_row = pd.DataFrame({
        "Periodo": ["TOTAL"],
        "Metodo": ["Combinado"],
        "Expuestos": [np.sum(expuestos_valores)],
        "Valor_Inicial": [np.sum(valores_iniciales)],
        "Valor_Actual": [np.sum(valores_actuales)],
        "Siniestralidad_Ultima": [np.sum(siniestralidad_ultima)],
        "IBNR": [np.sum(siniestralidad_ultima - valores_actuales)],
        "Factor_Desarrollo": [np.sum(siniestralidad_ultima) / np.sum(valores_actuales) 
                             if np.sum(valores_actuales) > 0 else np.nan],
        "Loss_Ratio": [np.sum(siniestralidad_ultima) / np.sum(expuestos_valores) 
                      if np.sum(expuestos_valores) > 0 else np.nan]
    })
    
    # Añadir indicador total para triángulo de frecuencia
    if tipo_triangulo == "frecuencia":
        total_row["Indicador"] = [(total_row["Siniestralidad_Ultima"].values[0] / total_row["Expuestos"].values[0]) * 100 
                                 if total_row["Expuestos"].values[0] > 0 else np.nan]
    
    # Combinar resultados y ordenar
    resultados = pd.concat([resultados, total_row])
    resultados = resultados.sort_values("Periodo", ascending=False)
    
    return resultados

def procesar_expuestos(df, periodicidad="mes", ramo=None, canal=None, amparo=None):
    """
    Procesa los datos de expuestos con filtros similares a los siniestros.
    
    Args:
        df: DataFrame con datos de expuestos
        periodicidad: Periodicidad para agrupar datos
        ramo: Filtro de ramo
        canal: Filtro de canal
        amparo: Filtro de amparo
    
    Returns:
        DataFrame procesado de expuestos
    """
    # Crear una copia para no modificar el original
    df = df.copy()
    
    print(f"Procesando expuestos, columns: {df.columns.tolist()}")
    
    # Aplicar filtros
    if ramo and ramo != "":
        if "Ramo_Desc" in df.columns:
            df = df[df["Ramo_Desc"] == ramo]
            print(f"Filtrado por ramo: {ramo}, quedan {len(df)} filas")
    
    if canal and canal != "":
        canal_cols = ["Apertura_Canal_Desc", "Canal_Desc"]
        for col in canal_cols:
            if col in df.columns:
                df = df[df[col] == canal]
                print(f"Filtrado por canal ({col}): {canal}, quedan {len(df)} filas")
                break
    
    if amparo and amparo != "":
        amparo_cols = ["Apertura_Amparo_Desc", "Amparo_Desc"]
        for col in amparo_cols:
            if col in df.columns:
                df = df[df[col] == amparo]
                print(f"Filtrado por amparo ({col}): {amparo}, quedan {len(df)} filas")
                break
    
    # Encontrar columna de fecha
    fecha_cols = ["Fecha_Registro", "Fecha"]
    fecha_col = None
    for col in fecha_cols:
        if col in df.columns:
            fecha_col = col
            break
    
    if not fecha_col:
        print("No se encontró columna de fecha en los expuestos")
        return pd.DataFrame({"Periodo": [], "Total_Expuestos": []})
    
    # Convertir fecha a datetime si no lo es
    if df[fecha_col].dtype != "datetime64[ns]":
        df[fecha_col] = pd.to_datetime(df[fecha_col], errors='coerce')
    
    # Agrupar por período
    if periodicidad == "mes":
        df["Periodo"] = df[fecha_col].dt.to_period("M").dt.to_timestamp()
    elif periodicidad == "trimestre":
        df["Periodo"] = df[fecha_col].dt.to_period("Q").dt.to_timestamp()
    elif periodicidad == "año":
        df["Periodo"] = df[fecha_col].dt.to_period("Y").dt.to_timestamp()
    
    # Verificar si existe columna Expuestos
    if "Expuestos" not in df.columns:
        print("No se encontró columna 'Expuestos', usando valores constantes")
        df["Expuestos"] = 1  # Valor por defecto
    
    # Resumir por período
    try:
        resultado = df.groupby("Periodo").agg(
            Total_Expuestos=("Expuestos", "sum")
        ).reset_index().sort_values("Periodo", ascending=False)
        
        print(f"Expuestos procesados: {len(resultado)} períodos")
        
        return resultado
    except Exception as e:
        print(f"Error al procesar expuestos: {str(e)}")
        # Crear un DataFrame mínimo con estructura correcta
        periodos = pd.date_range(
            start=df[fecha_col].min() if not df.empty else pd.Timestamp.now() - pd.DateOffset(years=1),
            end=df[fecha_col].max() if not df.empty else pd.Timestamp.now(),
            freq='M' if periodicidad == "mes" else 'Q' if periodicidad == "trimestre" else 'Y'
        )
        
        return pd.DataFrame({
            "Periodo": periodos,
            "Total_Expuestos": 1000  # Valor por defecto
        })