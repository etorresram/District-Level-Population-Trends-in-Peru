import dash
from dash import dcc, html
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go

# Load data
df = pd.read_excel("data.xlsx", dtype={'ubigeo': str})
gdf_distritos = gpd.read_file('DISTRITOS_inei_geogpsperu_suyopomalia.shp', encoding='latin1')

# Reproject to a projected CRS (e.g., EPSG:3857) for accurate centroid calculations
gdf_distritos = gdf_distritos.to_crs(epsg=3857)

# Ensure that identifiers are strings
gdf_distritos["UBIGEO"] = gdf_distritos["UBIGEO"].astype(str)
df["ubigeo"] = df["ubigeo"].astype(str)

# Merge the information
gdf_merged = gdf_distritos.merge(df, left_on="UBIGEO", right_on="ubigeo", how="left")

# Fill null values in 'cp_dif' to avoid NaN in marker size
gdf_merged["cp_dif"] = gdf_merged["cp_dif"].fillna(0)

# Compute centroids using the projected CRS
gdf_merged["centroid"] = gdf_merged.geometry.centroid

# Increase the scale factor so circles are not too large
scale_factor = 10

# Compute marker size and assign color based on 'cp_dif'
gdf_merged["marker_size"] = (gdf_merged["cp_dif"].abs() ** 0.48) / scale_factor
gdf_merged["color"] = gdf_merged["cp_dif"].apply(lambda x: "red" if x > 0 else "blue")

# Create the Plotly figure
fig = go.Figure()

# Add district boundaries
for idx, row in gdf_distritos.iterrows():
    geom = row.geometry
    if geom.geom_type == 'Polygon':
        x, y = geom.exterior.xy
        fig.add_trace(go.Scatter(
            x=list(x),
            y=list(y),
            mode='lines',
            line=dict(color='grey', width=0.5),
            showlegend=False,
            hoverinfo='skip'
        ))
    elif geom.geom_type == 'MultiPolygon':
        for part in geom.geoms:
            x, y = part.exterior.xy
            fig.add_trace(go.Scatter(
                x=list(x),
                y=list(y),
                mode='lines',
                line=dict(color='grey', width=0.5),
                showlegend=False,
                hoverinfo='skip'
            ))

# Add centroids as markers
fig.add_trace(go.Scatter(
    x=gdf_merged["centroid"].x,
    y=gdf_merged["centroid"].y,
    mode='markers',
    marker=dict(
        size=gdf_merged["marker_size"],
        color=gdf_merged["color"],
        line=dict(color='white', width=0.5)
    ),
    name="Centroids",
    showlegend=False,
    text=gdf_merged["distrito"],   
    customdata=gdf_merged["cp_dif"],  
    hovertemplate="%{text}: %{customdata}<extra></extra>"
))

# For the legend, adjust sizes according to the same scale factor
legend_labels = [
    ("+50,000", (100000**0.5)/scale_factor, "red"),
    ("+25,000",  (50000**0.45)/scale_factor, "red"),
    ("+10,000",  (10000**0.5)/scale_factor, "red"),
    ("-1,000",   (1000**0.5)/scale_factor, "blue"),
    ("-10,000",  (10000**0.5)/scale_factor, "blue"),
    ("-25,000",  (50000**0.45)/scale_factor, "blue"),
]

for label, size, color in legend_labels:
    fig.add_trace(go.Scatter(
        x=[None],
        y=[None],
        mode='markers',
        marker=dict(size=size, color=color, line=dict(color='white', width=0.5)),
        showlegend=True,
        name=label
    ))

# Update figure layout
fig.update_layout(
    title="District-Level Population Change in Peru (2007-2022)",
    xaxis=dict(visible=False),
    yaxis=dict(visible=False, scaleanchor='x', scaleratio=1),
    margin=dict(l=0, r=0, t=40, b=40),  # Ajustamos el margen inferior para la fuente
    legend=dict(title="- Population change - "),
    annotations=[
        dict(
            x=0.01,
            y=-0.05,  # Posición debajo del gráfico
            xref='paper',
            yref='paper',
            text="Source: INEI, Census Data (2007) and Population Projections (2018-2022)",
            showarrow=False,
            font=dict(size=12, color="black")
        )
    ]
)

# Get the bounding box (total extent) of the districts
minx, miny, maxx, maxy = gdf_distritos.total_bounds

# Adjust axis range to display only Peru
fig.update_xaxes(range=[minx, maxx], visible=False)
fig.update_yaxes(range=[miny, maxy], visible=False, scaleanchor='x', scaleratio=1)

# Create the Dash application
app = dash.Dash(__name__, title="District-Level Population Change in Peru (2007-2021)")

app.layout = html.Div([
    dcc.Graph(figure=fig, style={'height': '90vh'})
])

if __name__ == '__main__':
    app.run(debug=True, port=8050)