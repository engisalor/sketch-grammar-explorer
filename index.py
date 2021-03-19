import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import scripts.classes as classes
import pathlib

# connect to main app.py file
from app import app
from app import server

# connect app pages
from apps import app5, app4, app3, app2, app1

# set data paths
data_folder = pathlib.Path("")
landing = data_folder / "README.md"

# get landing page
with open(landing, "r") as f:
    lines = [x for x in f]

# remove unwanted content
drops = ("# Sketch","!")
for l in lines:
    if l.startswith(drops):
        lines.remove(l)
lines = "".join(lines)

# get current version
versionall = classes.Call().version

#### LAYOUT

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        html.Div([
            html.Div([
                html.H1("Sketch Grammar Explorer"),
                html.Div([
                    html.Img(
                        src=app.get_asset_url("logo_ugr.png"),
                        # src='https://secretariageneral.ugr.es/pages/ivc/descarga/_img/horizontal/ugrmarca02color_2/!',
                        alt="University of Granada",
                        height=75)],
                    style={},
                ),
            ],style={
                "display": "flex", 
                "justify-content": "space-between",
                "align-items":"baseline",
                "margin-top": "10px",
                "margin-right": "10px",
                "margin-left": "10px",
                }),
        ]),
        html.Div([
        html.Div([dcc.Link("Home", href="/")],style={'margin': '10px'}),
        html.Div([dcc.Link("Get data", href="/apps/app5")],style={'margin': '10px'}),
        html.P(id="version",
            children="Version", 
            style={'color': '#1EAEDB','margin': '10px'}, 
            title=versionall)],
        style={
            "display": "flex", 
            "justify-content": "left",
            }),
        html.Div(id="page-content", children=[]),
    ])

@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):
    if pathname == "/apps/app5":
        return app5.layout
    if pathname == "/apps/app4":
        return app4.layout
    if pathname == "/apps/app3":
        return app3.layout
    if pathname == "/apps/app2":
        return app2.layout
    if pathname == "/apps/app1":
        return app1.layout
    else:
        return html.Div([
            html.Div([
                dcc.Markdown(lines)],
                style={"width":"1000px"})],
            style={
                "display": "flex",
                "justify-content": "center"})

if __name__ == "__main__":
    app.run_server(debug=True)
