# Análisis de Siniestros - Dashboard en Python

Este proyecto es una migración de una aplicación originalmente desarrollada en R Shiny a Python utilizando el framework Dash para crear un dashboard interactivo de análisis de siniestros.

## Características

- **Análisis de Datos**: Permite visualizar y analizar datos de siniestros con diferentes filtros y agrupaciones.
- **Triangulación de Siniestralidad**: Implementa el método del triángulo para análisis actuarial de siniestros.
- **Visualizaciones Interactivas**: Gráficos y tablas dinámicas que responden a las selecciones del usuario.
- **Filtros Avanzados**: Múltiples opciones de filtrado por ramo, canal, amparo, fechas y tipo de valor.
- **Exportación de Datos**: Funcionalidad para descargar los datos procesados en formato CSV.

## Estructura del Proyecto

```
siniestros-dash/
│
├── app.py                   # Punto de entrada principal
├── assets/                  # Archivos estáticos (CSS, imágenes, etc.)
│   └── custom.css           # Estilos personalizados
│
├── components/              # Componentes reutilizables
│   ├── __init__.py
│   ├── cards.py             # Tarjetas de información
│   ├── data_table.py        # Tablas de datos
│   └── charts.py            # Gráficos y visualizaciones
│
├── data/                    # Procesamiento de datos
│   ├── __init__.py
│   ├── data_loader.py       # Carga de archivos
│   └── data_processor.py    # Procesamiento de datos
│
├── layouts/                 # Diseños de página
│   ├── __init__.py
│   ├── main_layout.py       # Diseño principal
│   ├── datos_tab.py         # Pestaña de datos
│   └── triangulo_tab.py     # Pestaña de triángulo
│
├── callbacks/               # Callbacks para interactividad
│   ├── __init__.py
│   ├── filter_callbacks.py  # Callbacks de filtrado
│   └── data_callbacks.py    # Callbacks para datos y visualizaciones
│
├── utils/                   # Utilidades
│   ├── __init__.py
│   └── helpers.py           # Funciones auxiliares
│
├── requirements.txt         # Dependencias
└── README.md                # Documentación
```

## Requisitos

- Python 3.8+
- Dash 2.14+
- Pandas 2.1+
- Plotly 5.18+
- Otros requisitos listados en requirements.txt

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tuusuario/siniestros-dash.git
cd siniestros-dash
```

2. Crear y activar un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Copiar los archivos de datos en el directorio `data/`.

## Ejecución

Para ejecutar la aplicación en modo desarrollo:

```bash
python app.py
```

La aplicación estará disponible en `http://127.0.0.1:8050/`.

## Despliegue en Producción

### Usando Gunicorn (Linux/macOS)

```bash
gunicorn app:server -b :8000
```

### Usando Waitress (Windows)

```bash
waitress-serve --port=8000 app:server
```

## Estructura de Datos

La aplicación espera archivos de datos con la siguiente estructura:

### siniestros.csv
- `Fecha_Siniestro`: Fecha en que ocurrió el siniestro
- `Fecha_Registro`: Fecha en que se registró el siniestro
- `Pago_Bruto`: Valor bruto del pago
- `Pago_Retenido`: Valor retenido del pago
- `Ramo_Desc`: Descripción del ramo
- `Apertura_Canal_Desc`: Canal de distribución
- `Apertura_Amparo_Desc`: Descripción del amparo
- `Agrupacion_Reservas`: Agrupación de reservas

### expuestos.csv
- `Fecha`: Fecha de exposición
- `Expuestos`: Número de expuestos
- `Ramo_Desc`: Descripción del ramo
- `Canal_Desc`: Canal de distribución
- `Amparo_Desc`: Descripción del amparo

## Licencia

[MIT](LICENSE)

## Autor

Tu Nombre

## Agradecimientos

Este proyecto es una migración de una aplicación desarrollada originalmente en R Shiny.