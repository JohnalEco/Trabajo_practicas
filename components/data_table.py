import dash_bootstrap_components as dbc
from dash import html, dash_table
import pandas as pd


def create_data_table(id, title, color="primary"):
    """
    Crea una tabla de datos con un título.
    
    Args:
        id: ID del componente de tabla
        title: Título de la tabla
        color: Color del encabezado (primary, success, info, warning, danger)
    
    Returns:
        Componente de tabla con tarjeta
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H4(title, className="mb-0"),
                className=f"bg-{color} text-white"
            ),
            dbc.CardBody(
                dash_table.DataTable(
                    id=id,
                    page_size=12,
                    style_table={'overflowX': 'auto'},
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold'
                    },
                    style_cell={
                        'textAlign': 'left',
                        'padding': '8px'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        }
                    ],
                    export_format="csv"
                )
            )
        ]
    )


def create_triangle_table(id, title, no_padding=True, color="primary", no_header=False):
    """
    Crea una tabla específica para triángulos con opciones adicionales.
    
    Args:
        id: ID del componente de tabla
        title: Título de la tabla
        no_padding: Si se elimina el padding de la tarjeta
        color: Color del encabezado
        no_header: Si se muestra el encabezado o no
    
    Returns:
        Componente de tabla con tarjeta
    """
    table = dash_table.DataTable(
        id=id,
        page_action='none',
        style_table={
            'overflowX': 'auto',
            'overflowY': 'auto',
            'height': '500px'
        },
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold',
            'position': 'sticky',
            'top': 0,
            'zIndex': 1
        },
        style_cell={
            'textAlign': 'right',
            'padding': '8px',
            'minWidth': '80px'
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'index'},
                'fontWeight': 'bold',
                'textAlign': 'left',
                'backgroundColor': 'rgb(240, 240, 240)',
                'position': 'sticky',
                'left': 0,
                'zIndex': 1
            },
            {
                'if': {'filter_query': '{0} = 0 || {0} = null'},
                'backgroundColor': 'rgb(240, 240, 240)'
            },
            {
                'if': {'filter_query': '{Periodo} = "TOTAL"'},
                'backgroundColor': 'rgb(240, 240, 240)',
                'fontWeight': 'bold'
            },
            {
                'if': {'filter_query': '{IBNR} < 0'},
                'color': 'red'
            }
        ],
        export_format="csv",
        export_headers="display"
    )
    
    if no_header:
        return table
    
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H4(title, className="mb-0"),
                className=f"bg-{color} text-white"
            ),
            dbc.CardBody(
                table,
                className=no_padding and "p-0" or ""
            )
        ],
        className="triangle-table"
    )