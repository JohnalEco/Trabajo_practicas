"""
Módulo para precarga y caching de datos frecuentemente utilizados.
Este script se ejecuta al iniciar la aplicación.
"""
import time
import os
import threading
from data.data_loader import load_siniestros, load_expuestos
from data.data_processor import procesar_siniestros, asignar_periodos, calcular_tiempo_desarrollo


def precargar_datos_comunes(cache):
    """
    Precarga los datos más utilizados en la caché para acelerar la primera carga.
    
    Args:
        cache: Objeto de caché de Flask
    """
    print("Iniciando precarga de datos comunes...")
    start_time = time.time()
    
    # Crear directorio de caché si no existe
    if not os.path.exists("cache-directory"):
        os.makedirs("cache-directory")
        print("Directorio de caché creado.")
    
    # Cargar siniestros (este resultado será cacheado)
    try:
        siniestros = load_siniestros()
        print(f"Datos de siniestros cargados: {len(siniestros)} filas")
        
        # Procesar siniestros para las combinaciones más comunes
        # Estas serán las más usadas por los usuarios
        periodicidades = ["mes", "trimestre"]
        tipos_triangulo = ["plata", "severidad"]
        tipos_valor = ["Bruto", "Retenido"]
        
        for periodicidad in periodicidades:
            for tipo_triangulo in tipos_triangulo:
                for tipo_valor in tipos_valor:
                    # Clave para la caché
                    cache_key = f"precarga_{periodicidad}_{tipo_triangulo}_{tipo_valor}"
                    
                    # Procesar datos
                    try:
                        print(f"Procesando datos para {cache_key}...")
                        processed_data = procesar_siniestros(
                            siniestros, 
                            periodicidad, 
                            tipo_triangulo,
                            tipo_valor
                        )
                        
                        # Guardar en caché
                        cache.set(cache_key, processed_data.to_dict('records'))
                        print(f"Datos procesados y cacheados para {cache_key}: {len(processed_data)} filas")
                    except Exception as e:
                        print(f"Error al procesar datos para {cache_key}: {str(e)}")
        
    except Exception as e:
        print(f"Error en precarga de siniestros: {str(e)}")
    
    # Cargar expuestos (este resultado será cacheado)
    try:
        expuestos = load_expuestos()
        print(f"Datos de expuestos cargados: {len(expuestos)} filas")
        
        # Procesar expuestos para periodicidades comunes
        from data.data_processor import procesar_expuestos
        for periodicidad in periodicidades:
            # Clave para la caché
            cache_key = f"expuestos_{periodicidad}"
            
            try:
                expuestos_procesados = procesar_expuestos(expuestos, periodicidad)
                cache.set(cache_key, expuestos_procesados.to_dict('records'))
                print(f"Expuestos procesados y cacheados para {cache_key}: {len(expuestos_procesados)} filas")
            except Exception as e:
                print(f"Error al procesar expuestos para {cache_key}: {str(e)}")
    
    except Exception as e:
        print(f"Error en precarga de expuestos: {str(e)}")
    
    elapsed = time.time() - start_time
    print(f"Precarga de datos completada en {elapsed:.2f} segundos")


def iniciar_precarga(cache):
    """
    Inicia la precarga de datos en un hilo separado para no bloquear el inicio de la aplicación.
    
    Args:
        cache: Objeto de caché de Flask
    """
    thread = threading.Thread(target=precargar_datos_comunes, args=(cache,))
    thread.daemon = True  # El hilo se cerrará cuando termine la aplicación
    thread.start()