import dash_bootstrap_components as dbc
from dash import html

from components.cards import create_metric_cards
from components.charts import create_bar_chart, create_line_chart
from components.data_table import create_data_table


def create_datos_tab():
    """
    Crea el contenido de la pestaña de Datos.
    
    Returns:
        Componentes de la pestaña
    """
    return html.Div(
        [
            # Tarjetas métricas
            create_metric_cards(),
            
            html.Br(),
            
            # Gráficos
            dbc.Row(
                [
                    dbc.Col(
                        create_bar_chart("grafico_barras_ocurrencia"),
                        width=6
                    ),
                    dbc.Col(
                        create_line_chart("grafico_lineas_desarrollo"),
                        width=6
                    )
                ]
            ),
            
            html.Br(),
            
            # Tabla de resumen
            dbc.Row(
                dbc.Col(
                    create_data_table(
                        "tabla_ocurrencia",
                        "Resumen por Período de Ocurrencia"
                    ),
                    width=12
                )
            )
        ]
    )