import dash_bootstrap_components as dbc
from dash import html, dcc

from components.data_table import create_triangle_table


def create_triangulo_tab():
    """
    Crea el contenido de la pestaña de Triángulo de Siniestralidad.
    
    Returns:
        Componentes de la pestaña
    """
    return html.Div(
        [
            # Triángulo de siniestros
            dbc.Row(
                dbc.Col(
                    create_triangle_table(
                        "triangulo",
                        "Triángulo de Siniestros Acumulados"
                    ),
                    width=12
                )
            ),
            
            html.Br(),
            
            # Factores de desarrollo
            dbc.Row(
                dbc.Col(
                    create_triangle_table(
                        "tabla_factores",
                        "Factores de Desarrollo"
                    ),
                    width=12
                )
            ),
            
            html.Br(),
            
            # Estadísticas de factores
            dbc.Row(
                dbc.Col(
                    create_triangle_table(
                        "tabla_estadisticas_factores",
                        "Estadísticas de Factores de Desarrollo"
                    ),
                    width=12
                )
            ),
            
            html.Br(),
            
            # Cálculo de IBNR
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                [
                                    html.H4("Cálculo de IBNR", className="mb-0 d-inline-block"),
                                    html.Div(
                                        [
                                            dbc.Label("Método:", className="mr-2"),
                                            dcc.Dropdown(
                                                id="metodo_calculo",
                                                options=[
                                                    {"label": "Automático", "value": "auto"},
                                                    {"label": "Chain Ladder", "value": "chain_ladder"},
                                                    {"label": "Bornhuetter-Ferguson", "value": "bornhuetter_ferguson"}
                                                ],
                                                value="auto",
                                                clearable=False,
                                                style={"width": "200px", "display": "inline-block"}
                                            ),
                                            html.Small(
                                                "Seleccione el método de estimación de IBNR",
                                                className="text-muted ml-2"
                                            )
                                        ],
                                        className="float-right d-flex align-items-center"
                                    )
                                ],
                                className="bg-primary text-white d-flex justify-content-between"
                            ),
                            dbc.CardBody(
                                create_triangle_table(
                                    "tabla_resumen_ultima",
                                    "",
                                    no_header=True
                                ),
                                className="p-0"
                            )
                        ]
                    ),
                    width=12
                )
            )
        ]
    )