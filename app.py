import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from flask import Flask, request
from flask_caching import Cache
import time

# Importar componentes de la aplicación
from layouts.main_layout import create_layout
from callbacks.filter_callbacks import register_filter_callbacks
from callbacks.data_callbacks import register_data_callbacks

# Configuración del caché - SimpleCache es compatible con todas las versiones
cache_config = {
    'CACHE_TYPE': 'SimpleCache',  # En memoria, no requiere archivos
    'CACHE_DEFAULT_TIMEOUT': 3600,
    'CACHE_THRESHOLD': 500  # Máximo número de items en caché
}

# Inicializar la aplicación Flask
server = Flask(__name__)

# Inicializar el caché
cache = Cache()
cache.init_app(server, config=cache_config)

# Inicializar la aplicación Dash
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True,
    # Minimizar recursos para carga más rápida
    compress=True
    # Eliminamos el parámetro max_callback_wait_time que no es compatible
)

# Configurar el título
app.title = "Análisis de Siniestros de Seguros"

# Optimización para rendimiento
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

# Crear el diseño principal
app.layout = create_layout()

# Registrar callbacks
register_filter_callbacks(app, cache)
register_data_callbacks(app, cache)

# Handler global para errores
@server.errorhandler(Exception)
def handle_error(e):
    print(f"Error global: {str(e)}")
    return str(e), 500

# Middleware para medir tiempos de respuesta
@server.before_request
def before_request():
    server.start_time = time.time()

@server.after_request
def after_request(response):
    if hasattr(server, 'start_time'):
        elapsed = time.time() - server.start_time
        if elapsed > 1.0:  # Solo registrar operaciones que toman más de 1 segundo
            print(f"Tiempo de respuesta: {elapsed:.2f} segundos para {request.path}")
    return response

# Ejecutar la aplicación
if __name__ == '__main__':
    # Ejecutar la aplicación
    app.run_server(
        debug=True,
        # Utilizar múltiples procesos para mejor rendimiento 
        threaded=True
    )