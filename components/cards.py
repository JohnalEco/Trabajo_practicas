import dash_bootstrap_components as dbc
from dash import html


def create_info_card(title, id, color="primary"):
    """
    Crea una tarjeta de información con título y valor dinámico.
    
    Args:
        title: Título de la tarjeta
        id: ID del componente para el valor
        color: Color de la tarjeta (primary, success, info, warning, danger)
    
    Returns:
        Componente de tarjeta
    """
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H6(title, className=f"card-title"),
                    html.H4(id=id, className=f"card-text text-{color}")
                ],
                className="text-center"
            )
        ],
        className=f"border-{color}"
    )


def create_metric_cards():
    """
    Crea el conjunto de tarjetas métricas para el dashboard.
    
    Returns:
        Fila de tarjetas
    """
    return dbc.Row(
        [
            dbc.Col(
                create_info_card("Total Siniestros", "total_siniestros", "primary"),
                width=2
            ),
            dbc.Col(
                create_info_card("Siniestros Pagados", "siniestros_pagados", "success"),
                width=2
            ),
            dbc.Col(
                create_info_card("Total Pagos", "total_pagos", "info"),
                width=4
            ),
            dbc.Col(
                create_info_card("Total Incurrido", "total_incurrido", "warning"),
                width=4
            )
        ]
    )