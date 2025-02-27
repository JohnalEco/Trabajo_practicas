import dash_bootstrap_components as dbc
from dash import html, dcc

from data.data_loader import get_date_range
from layouts.datos_tab import create_datos_tab
from layouts.triangulo_tab import create_triangulo_tab


def create_sidebar():
    """
    Crea el panel lateral con controles de filtrado.
    
    Returns:
        Componente de panel lateral
    """
    fecha_min, fecha_max = get_date_range()
    
    return dbc.Col(
        [
            html.H4("Filtros", className="mb-3"),
            
            dbc.Label("Periodicidad:"),
            dcc.Dropdown(
                id="periodicidad",
                options=[
                    {"label": "Mensual", "value": "mes"},
                    {"label": "Trimestral", "value": "trimestre"},
                    {"label": "Anual", "value": "año"}
                ],
                value="mes",
                clearable=False,
                className="mb-3"
            ),
            
            dbc.Label("Ramo:"),
            dcc.Dropdown(
                id="ramo",
                options=[{"label": "Todos", "value": ""}],
                value="",
                className="mb-3"
            ),
            
            dbc.Label("Canal:"),
            dcc.Dropdown(
                id="canal",
                options=[{"label": "Todos", "value": ""}],
                value="",
                className="mb-3"
            ),
            
            dbc.Label("Amparo:"),
            dcc.Dropdown(
                id="amparo",
                options=[{"label": "Todos", "value": ""}],
                value="",
                className="mb-3"
            ),
            
            html.Hr(),
            
            dbc.Label("Tipo de Valor:"),
            dbc.RadioItems(
                id="tipo_valor",
                options=[
                    {"label": "Bruto", "value": "Bruto"},
                    {"label": "Retenido", "value": "Retenido"}
                ],
                value="Bruto",
                inline=True,
                className="mb-3"
            ),
            
            html.Hr(),
            
            dbc.Label("Rango de Fechas:"),
            dcc.DatePickerRange(
                id="rango_fechas",
                start_date=fecha_min,
                end_date=fecha_max,
                display_format="YYYY-MM-DD",
                className="mb-3"
            ),
            
            html.Hr(),
            
            dbc.Label("Tipo de Triángulo:"),
            dcc.Dropdown(
                id="tipo_triangulo",
                options=[
                    {"label": "Plata", "value": "plata"},
                    {"label": "Severidad", "value": "severidad"},
                    {"label": "Frecuencia", "value": "frecuencia"}
                ],
                value="plata",
                clearable=False,
                className="mb-3"
            ),
            
            html.Hr(),
            
            dbc.Button(
                "Descargar Datos",
                id="descargar_datos",
                color="primary",
                className="w-100 mb-3"
            ),
            
            dcc.Download(id="download-data")
        ],
        width=2,
        className="sidebar"
    )


def create_layout():
    """
    Crea el diseño principal de la aplicación.
    
    Returns:
        Layout completo
    """
    return html.Div(
        [
            # Título principal
            html.Div(
                html.H1("Análisis de Siniestros de Seguros", className="header-title"),
                className="p-3"
            ),
            
            # Layout principal
            dbc.Row(
                [
                    # Panel lateral
                    create_sidebar(),
                    
                    # Panel principal
                    dbc.Col(
                        [
                            dbc.Tabs(
                                [
                                    dbc.Tab(
                                        create_datos_tab(),
                                        label="Resumen Ejecutivo",
                                        tab_id="tab-datos"
                                    ),
                                    dbc.Tab(
                                        create_triangulo_tab(),
                                        label="Análisis Técnico",
                                        tab_id="tab-triangulo"
                                    )
                                ],
                                id="tabs",
                                active_tab="tab-datos"
                            )
                        ],
                        width=10,
                        className="main-content"
                    )
                ],
                className="g-0"  # Elimina el espacio entre columnas
            ),
            
            # Almacenamiento de datos
            dcc.Store(id="stored-processed-data"),
            dcc.Store(id="stored-filtered-data"),
            dcc.Store(id="stored-triangle-data"),
            dcc.Store(id="stored-factors-data"),
            dcc.Store(id="stored-expuestos-data"),
            dcc.Store(id="stored-ultima-data")
        ]
    )