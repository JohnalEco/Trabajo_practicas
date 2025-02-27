import plotly.graph_objects as go
from dash import dcc
import pandas as pd


def create_bar_chart(id, height="400px"):
    """
    Crea un componente de gráfico de barras.
    
    Args:
        id: ID del componente
        height: Altura del gráfico
    
    Returns:
        Componente de gráfico
    """
    return dcc.Graph(
        id=id,
        config={
            'displayModeBar': True,
            'responsive': True,
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'grafico',
                'height': 500,
                'width': 700,
                'scale': 2
            }
        },
        style={'height': height}
    )


def create_line_chart(id, height="400px"):
    """
    Crea un componente de gráfico de líneas.
    
    Args:
        id: ID del componente
        height: Altura del gráfico
    
    Returns:
        Componente de gráfico
    """
    return dcc.Graph(
        id=id,
        config={
            'displayModeBar': True,
            'responsive': True,
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'grafico',
                'height': 500,
                'width': 700,
                'scale': 2
            }
        },
        style={'height': height}
    )


def generate_bar_chart_figure(df, x_col, y_cols, names, colors, title, x_title, y_title):
    """
    Genera una figura de gráfico de barras con múltiples series.
    
    Args:
        df: DataFrame con los datos
        x_col: Columna para el eje X
        y_cols: Lista de columnas para el eje Y
        names: Lista de nombres para cada serie
        colors: Lista de colores para cada serie
        title: Título del gráfico
        x_title: Título del eje X
        y_title: Título del eje Y
    
    Returns:
        Figura de Plotly
    """
    fig = go.Figure()
    
    for i, y_col in enumerate(y_cols):
        fig.add_trace(
            go.Bar(
                x=df[x_col],
                y=df[y_col],
                name=names[i],
                marker_color=colors[i]
            )
        )
    
    fig.update_layout(
        title=title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        template="plotly_white"
    )
    
    return fig


def generate_line_chart_figure(df, x_col, y_cols, names, colors, title, x_title, y_title):
    """
    Genera una figura de gráfico de líneas con múltiples series.
    
    Args:
        df: DataFrame con los datos
        x_col: Columna para el eje X
        y_cols: Lista de columnas para el eje Y
        names: Lista de nombres para cada serie
        colors: Lista de colores para cada serie
        title: Título del gráfico
        x_title: Título del eje X
        y_title: Título del eje Y
    
    Returns:
        Figura de Plotly
    """
    fig = go.Figure()
    
    for i, y_col in enumerate(y_cols):
        fig.add_trace(
            go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode='lines+markers',
                name=names[i],
                line=dict(color=colors[i], width=2)
            )
        )
    
    fig.update_layout(
        title=title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        template="plotly_white"
    )
    
    return fig