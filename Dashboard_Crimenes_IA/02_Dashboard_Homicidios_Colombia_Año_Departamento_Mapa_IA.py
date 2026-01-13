import requests
import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from sklearn.linear_model import LinearRegression
import numpy as np

# Se crean las variables relacionadas a la API
URL = "https://www.datos.gov.co/resource/m8fd-ahd9.json"
params = {"$limit": 10000000}

response = requests.get(URL, params=params)
response.raise_for_status()
data = response.json()
df = pd.DataFrame(data)

# El siguiente codigo limpia los datos que viene de la api
posibles_fechas = ["fecha_hecho", "fecha", "fecha_del_hecho"]
col_fecha = next((c for c in posibles_fechas if c in df.columns), None)
if col_fecha is None:
    raise Exception("No se encontró columna de fecha en el dataset")

df.rename(columns={col_fecha: "fecha_hecho"}, inplace=True)
df["fecha_hecho"] = pd.to_datetime(df["fecha_hecho"], errors="coerce")

df["anio"] = df["fecha_hecho"].dt.year
df["mes"] = df["fecha_hecho"].dt.month
df["dia"] = df["fecha_hecho"].dt.day
df["departamento"] = df["departamento"].str.upper()

df = df.dropna(subset=["anio", "mes", "dia", "departamento"])
df[["anio", "mes", "dia"]] = df[["anio", "mes", "dia"]].astype(int)

anios_disponibles = sorted(df["anio"].unique())

# Lista de todos los departamantos y sus coordenadas
departamentos_colombia = list({
    "AMAZONAS", "ANTIOQUIA", "ARAUCA", "ATLANTICO", "BOLIVAR", "BOYACA",
    "CALDAS", "CAQUETA", "CASANARE", "CAUCA", "CESAR", "CHOCO", "CORDOBA",
    "CUNDINAMARCA", "GUAINIA", "GUAVIARE", "HUILA", "LA_GUAJIRA", "MAGDALENA",
    "META", "NARIÑO", "NORTE_DE_SANTANDER", "PUTUMAYO", "QUINDIO",
    "RISARALDA", "SAN_ANDRES", "SANTANDER", "SUCRE", "TOLIMA",
    "VALLE_DEL_CAUCA", "VAUPES", "VICHADA", "BOGOTA D.C."
})

centroides_departamentos = {
    "AMAZONAS": [-69.9333, -1.4433],
    "ANTIOQUIA": [-75.5636, 6.2518],
    "ARAUCA": [-70.7333, 7.0833],
    "ATLANTICO": [-75.5247, 10.4230],
    "BOLIVAR": [-75.5000, 10.4000],
    "BOYACA": [-73.3500, 5.5500],
    "CALDAS": [-75.5138, 5.0703],
    "CAQUETA": [-75.6667, 1.5833],
    "CASANARE": [-71.7333, 5.3667],
    "CAUCA": [-76.0000, 2.5000],
    "CESAR": [-73.2500, 10.9833],
    "CHOCO": [-76.6413, 5.6936],
    "CORDOBA": [-75.8800, 8.7700],
    "CUNDINAMARCA": [-74.0758, 4.5981],
    "GUAINIA": [-69.7500, 2.5667],
    "GUAVIARE": [-72.6333, 2.5667],
    "HUILA": [-75.2800, 2.9300],
    "LA_GUAJIRA": [-72.9000, 11.5400],
    "MAGDALENA": [-74.2500, 10.5000],
    "META": [-73.6140, 4.1560],
    "NARIÑO": [-77.2719, 1.2141],
    "NORTE_DE SANTANDER": [-72.4967, 7.8891],
    "PUTUMAYO": [-76.5417, 0.1521],
    "QUINDIO": [-75.7688, 4.5617],
    "RISARALDA": [-75.6946, 4.8517],
    "SAN_ANDRES": [-81.7000, 12.5847],
    "SANTANDER": [-73.1198, 7.1254],
    "SUCRE": [-75.3977, 9.3070],
    "TOLIMA": [-75.2322, 4.4359],
    "VALLE_DEL_CAUCA": [-76.5225, 3.4372],
    "VAUPES": [-70.2500, 1.5833],
    "VICHADA": [-69.1000, 4.6000],
    "BOGOTA D.C.": [-74.0721, 4.7110]
}

# Codigo relacionado a la regresion lineal con machine learning red neuronal
def calcular_predicciones_ml():
    df_ml = df.groupby(["departamento", "anio"]).size().reset_index(name="homicidios")
    resultados = []

    for depto in departamentos_colombia:
        datos = df_ml[df_ml["departamento"] == depto]
        if len(datos) >= 2:
            X = datos[["anio"]].values
            y = datos["homicidios"].values
            modelo = LinearRegression()
            modelo.fit(X, y)
            pred_base = modelo.predict(np.array([[2026]]))[0]
            desviacion = max(abs(pred_base) * 0.15, 1)
            ruido = np.random.normal(0, desviacion)
            pred_final = int(max(pred_base + ruido, 0))
        else:
            pred_final = 0
        resultados.append({
            "departamento": depto,
            "homicidios_estimados_2026": pred_final
        })

    df_resultados = pd.DataFrame(resultados)
    df_resultados = df_resultados.set_index("departamento").reindex(departamentos_colombia).fillna(0).reset_index()
    df_resultados["homicidios_estimados_2026"] = df_resultados["homicidios_estimados_2026"].astype(int)
    return df_resultados.sort_values("homicidios_estimados_2026", ascending=False)

df_predicciones = calcular_predicciones_ml()

# Posteriormente procedemos a crear el dashboard
app = dash.Dash(__name__)
fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

app.layout = html.Div(
    style={"width": "95%", "margin": "auto", "backgroundColor": "black",
           "color": "red", "minHeight": "100vh", "padding": "20px"},
    children=[
        html.H1("Homicidios en Colombia", style={"textAlign": "center"}),
        html.H4(f"Fecha y hora actual: {fecha_actual}", style={"textAlign": "center"}),

        html.Label("Seleccione el año:", style={"color": "red"}),
        dcc.Dropdown(
            id="select-anio",
            options=[{"label": str(a), "value": a} for a in anios_disponibles],
            value=anios_disponibles[0],
            clearable=False,
            style={"color": "black"}
        ),

        html.Hr(style={"borderColor": "red"}),

        dash_table.DataTable(
            id="tabla-homicidios",
            page_size=10,
            style_header={"backgroundColor": "red", "color": "black"},
            style_cell={"backgroundColor": "gray", "color": "black"}
        ),

        html.Hr(style={"borderColor": "red"}),

        dcc.Graph(id="grafica-barras"),

        html.Hr(style={"borderColor": "red"}),

        dcc.Graph(id="mapa-colombia", style={"height": "800px"}),

        html.Hr(style={"borderColor": "red"}),

        html.H2("Pronóstico de homicidios 2026 (33 departamentos)", style={"textAlign": "center"}),

        dash_table.DataTable(
            columns=[
                {"name": "Departamento", "id": "departamento"},
                {"name": "Homicidios estimados 2026", "id": "homicidios_estimados_2026"}
            ],
            data=df_predicciones.to_dict("records"),
            page_size=16,
            style_header={"backgroundColor": "red", "color": "black"},
            style_cell={"backgroundColor": "gray", "color": "black"}
        )
    ]
)

# A continuacion se crean los callback
@app.callback(
    [
        Output("tabla-homicidios", "data"),
        Output("tabla-homicidios", "columns"),
        Output("grafica-barras", "figure"),
        Output("mapa-colombia", "figure")
    ],
    Input("select-anio", "value")
)
def actualizar_dashboard(anio):
    df_anio = df[df["anio"] == anio]

    columnas = [{"name": c, "id": c} for c in df_anio.columns]
    data_tabla = df_anio.to_dict("records")

    conteo = df_anio.groupby("departamento").size().reset_index(name="cantidad")

    fig_barras = px.bar(
        conteo,
        x="departamento",
        y="cantidad",
        color="departamento",
        template="plotly_dark",
        title=f"Homicidios por departamento en {anio}"
    )
    fig_barras.update_layout(xaxis_tickangle=-45)

    # Se crea el mapa
    lons, lats, texts, sizes = [], [], [], []
    max_val = conteo["cantidad"].max() if not conteo.empty else 1

    for _, r in conteo.iterrows():
        depto = r["departamento"]
        if depto in centroides_departamentos:
            lon, lat = centroides_departamentos[depto]
            lons.append(lon)
            lats.append(lat)
            texts.append(f"{depto}<br>{r['cantidad']}")
            sizes.append(8 + (r["cantidad"] / max_val) * 32)

    fig_mapa = go.Figure(go.Scattermapbox(
        lon=lons,
        lat=lats,
        text=texts,
        mode="markers+text",
        marker=dict(size=sizes, color="red")
    ))

    fig_mapa.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=4.5,
        mapbox_center={"lat": 4.5, "lon": -74},
        template="plotly_dark"
    )

    return data_tabla, columnas, fig_barras, fig_mapa

# Finalmente se crea el main de ejecucion
if __name__ == "__main__":
    app.run(debug=True)
