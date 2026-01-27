# Ejemplo Dashboard con mapa de Colombia y sus Departamentos
# Un punto amarillo en la comuna que no llueve y
# un punto azul en la comuna que llueve
# pip install dash pandas requests pydeck
# pip 25.3.1
# Python 3.13.1


import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
import dash
from dash import html, dash_table
import pydeck as pdk

# Codigo relacionado a la sesion request de la pagina web
session = requests.Session()
retries = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)

# Coordenadas de cada departamento de colombia
DEPARTAMENTOS = {
    "Amazonas": (-1.4429, -71.5724),
    "Antioquia": (6.5569, -75.8281),
    "Arauca": (7.0900, -70.7617),
    "Atlántico": (10.6966, -74.8741),
    "Bolívar": (8.6704, -74.0300),
    "Boyacá": (5.4545, -73.3620),
    "Caldas": (5.2983, -75.2479),
    "Caquetá": (0.8699, -73.8419),
    "Casanare": (5.7589, -71.5724),
    "Cauca": (2.7049, -76.8259),
    "Cesar": (9.3373, -73.6536),
    "Chocó": (5.2528, -76.8260),
    "Córdoba": (8.0493, -75.5740),
    "Cundinamarca": (4.6816, -74.1546),
    "Guainía": (2.5854, -68.5247),
    "Guaviare": (2.0439, -72.3311),
    "Huila": (2.5359, -75.5277),
    "La Guajira": (11.3548, -72.5205),
    "Magdalena": (10.2240, -74.2017),
    "Meta": (3.2719, -73.0877),
    "Nariño": (1.2892, -77.3579),
    "Norte de Santander": (7.9463, -72.8988),
    "Putumayo": (0.4359, -75.5277),
    "Quindío": (4.4610, -75.6674),
    "Risaralda": (5.3158, -75.9928),
    "San Andrés y Providencia": (12.5847, -81.7006),
    "Santander": (6.6437, -73.6536),
    "Sucre": (9.3047, -75.3978),
    "Tolima": (4.0925, -75.1545),
    "Valle del Cauca": (3.8009, -76.6413),
    "Vaupés": (0.8554, -70.8110),
    "Vichada": (4.4234, -69.2878),
    "Bogotá D.C.": (4.7110, -74.0721)
}

# Funcion que consulta la api y recibe los datos relacionados a la lluvia
def obtener_datos_lluvia():
    datos = []
    for depto, (lat, lon) in DEPARTAMENTOS.items():
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}"
            f"&longitude={lon}"
            f"&current_weather=true"
            f"&hourly=precipitation"
            f"&timezone=auto"
        )

        try:
            response = session.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            current = data.get("current", {})
            temperatura = current.get("temperature_2m")
            lluvia = current.get("precipitation", 0)
        except requests.exceptions.RequestException as e:
            print(f"Error consultando {depto}: {e}")
            temperatura = None
            lluvia = 0

        datos.append({
            "Departamento": depto,
            "Temperatura (°C)": temperatura,
            "Lluvia (mm)": lluvia,
            "Latitud": lat,
            "Longitud": lon
        })
    return pd.DataFrame(datos)

# Se crea el mapa con las caracteristicas
def crear_mapa_pydeck(df):
    min_size = 3000     # pequeño (sin lluvia)
    max_size = 15000    # mediano (lluvia fuerte)

    max_lluvia = df["Lluvia (mm)"].max()
    max_lluvia = max_lluvia if max_lluvia > 0 else 1

    # Tamaño progresivo
    df["size"] = df["Lluvia (mm)"].apply(
        lambda x: min_size + (x / max_lluvia) * (max_size - min_size)
    )

    # Color progresivo: amarillo hasta azul oscuro
    def color_por_lluvia(lluvia):
        ratio = lluvia / max_lluvia

        # Amarillo (255,255,0) → Azul oscuro (0,0,139)
        r = int(255 * (1 - ratio))
        g = int(255 * (1 - ratio))
        b = int(139 * ratio)

        return [r, g, b]

    df["color"] = df["Lluvia (mm)"].apply(color_por_lluvia)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["Longitud", "Latitud"],
        get_radius="size",
        get_fill_color="color",
        pickable=True,
        auto_highlight=True
    )

    view_state = pdk.ViewState(
        latitude=4.0,
        longitude=-74.0,
        zoom=5,
        pitch=45
    )

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        tooltip={
            "text": "{Departamento}\nTemp: {Temperatura (°C)} °C\nLluvia: {Lluvia (mm)} mm"
        }
    )

    tmp_html = "mapa_lluvias_colombia_pydeck.html"
    deck.to_html(tmp_html, open_browser=False)
    return tmp_html

# Codigo relacionado al dashboard
df = obtener_datos_lluvia()
df_table = df.drop(columns=["color"], errors="ignore")
mapa_html = crear_mapa_pydeck(df)

app = dash.Dash(__name__)
fecha_hora_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

app.layout = html.Div(
    style={
        "backgroundColor": "black",
        "color": "red",
        "padding": "15px",
        "fontFamily": "Arial"
    },
    children=[
        html.H1("Dashboard de Lluvias en Colombia"),
        html.H4(f"Fecha y hora actual: {fecha_hora_actual}"),

        html.H3("Tabla de lluvia por departamento"),
        dash_table.DataTable(
            data=df_table.to_dict("records"),
            columns=[{"name": c, "id": c} for c in df_table.columns],
            style_table={"overflowX": "auto"},
            style_cell={
                "textAlign": "center",
                "padding": "6px",
                "backgroundColor": "#e6e6e6",
                "color": "black"
            },
            style_header={
                "backgroundColor": "red",
                "color": "black",
                "fontWeight": "bold"
            },
            page_size=10
        ),

        html.H3("Mapa que muestra en que departamento de Colombia llueve, amarillo pequeño no llueve hasta azul oscuro grande llueve bastante"),
        html.Iframe(
            srcDoc=open(mapa_html, "r", encoding="utf-8").read(),
            width="100%",
            height="800"
        )
    ]
)

# Main de ejecucion
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1234, debug=True)
