import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import subprocess

# Connect to main app.py file
from app import app
from app import server

# Connect to your app pages
from apps import app5, app4, app3, app2, app1

# get current git version/hash
try:
    version = subprocess.check_output(["git", "describe",  "--always"]).decode("utf-8").strip()
    versiondate = subprocess.check_output(["git", "show", "-s", "--format=%cd", "--date=short"]).decode("utf-8").strip()
    versionall = "{} {}".format(versiondate, version)
except:
    versionall= "unknown"

#### LAYOUT

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    dcc.Link(
                                        "README & source code",
                                        href="https://github.com/engisalor/sketch-grammar-explorer",
                                        target="blank",
                                    )
                                ),
                                html.Div(
                                    dcc.Link(
                                        "LexiCon Research Group",
                                        href="https://ecolexicon.ugr.es/",
                                        target="blank",
                                    )
                                ),
                                html.Div(
                                    dcc.Link(
                                        "Sketch Engine",
                                        href="https://www.sketchengine.eu/",
                                        target="blank",
                                    )
                                ),
                                html.Div(
                                    dcc.Link(
                                        "Dash",
                                        href="https://plotly.com/dash/",
                                        target="blank",
                                    )
                                ),
                                html.P(id="version",children="Version info", style={'color': '#1EAEDB'}, title=versionall),
                            ]
                        ),
                        html.Img(
                            src=app.get_asset_url("logo_ugr.png"),
                            # src='https://secretariageneral.ugr.es/pages/ivc/descarga/_img/horizontal/ugrmarca02color_2/!',
                            alt="University of Granada",
                            height=75,
                        ),
                    ],
                    style={"display": "flex", "justify-content": "space-between"},
                ),
                html.H2(children="Sketch Grammar Explorer"),                
                html.Div(
                    [
                        dcc.Link("Frequency Visualizations    |    ", href="/apps/app1"),
                        dcc.Link("Summary Table    |    ", href="/apps/app2"),
                        dcc.Link("All Records    |    ", href="/apps/app3"),
                        dcc.Link("WS freqs    |    ", href="/apps/app4"),
                        dcc.Link("Precision Analysis", href="/apps/app5"),
                    ],
                    className="row",
                ),
                html.Div(id="page-content", children=[]),
            ]
        ),
    ]
)


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
        return "404 Page Error! Please choose a link"


if __name__ == "__main__":
    app.run_server(debug=True)
