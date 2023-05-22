'''
MAIN PAGE
'''
import dash
from dash import html
import dash_bootstrap_components as dbc
import os
import dash_auth
from dotenv import load_dotenv
load_dotenv()

app_user = os.getenv('app-username')
app_pass = os.getenv('app-password')


VALID_USERNAME_PASSWORD_PAIRS = {
    app_user: app_pass
}

app = dash.Dash(__name__, use_pages=True,
                external_stylesheets=[dbc.themes.DARKLY],
                meta_tags=[
                    {"name": "viewport", "content": "width=device-width, initial-scale=1"}
                ])

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)
server = app.server
sidebar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink(
            [
                html.Div(page["name"]),
            ],
            href=page["path"],
            active="exact",
        ))
        for page in sorted(dash.page_registry.values(), key=lambda page:  page["name"])
    ],
    color="primary",
    dark=True,
    fluid=True,
    id='nav-bar'
)


app.layout = dbc.Container([

    dbc.Row([
        dbc.Col(html.A(
            html.Img(src="assets\logo.png", height=80, id='logo'),
            href="https://www.megawattpower.com.au",
            target="_blank",
            style={'position': 'absolute', 'top': '5px', 'right': '40px'}
        ),)
    ]),

    dbc.Row([
        dbc.Col(html.Div("Wandoan Solar Farm Weather Station",
                         style={'fontSize': 50, 'textAlign': 'center'}, id='wsf-mainheading'))
    ]),

    html.Br(),
    sidebar,
    html.Br(),
    dash.page_container

], fluid=True)


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8051)
