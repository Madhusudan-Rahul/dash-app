'''
DASH PYTHON PAGE - 1 ---> CURRENT DATA VISULISATION
'''
import dash
from dash import Input, Output, dcc, html, callback
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote
import dash_bootstrap_components as dbc
import datetime
from datetime import datetime, date
import pytz
import dash_daq as daq
import plotly.graph_objects as go
from dash_iconify import DashIconify
from rosely import WindRose
import plotly.express as px
import json
import requests
from dotenv import load_dotenv
import os

# Load the .env file to access the api keys and other secret data
load_dotenv()
'''
DASH AND MAKE THIS PAGE AS HOME PAGE
'''

dash.register_page(__name__, name='Current', path='/')

'''
FUNCTIONS
'''

# Function to calculate Brisbane time from epoch time


def timeconversion(epoch_timestamp):
    if epoch_timestamp == 0:
        return ("0")
    else:
        epoch_timestamp = int(epoch_timestamp)
        utc_dt = datetime.fromtimestamp(epoch_timestamp, pytz.utc)
        utc_dt = utc_dt.replace(second=0, microsecond=0)
        brisbane = pytz.timezone("Australia/Brisbane")
        local_dt = brisbane.normalize(utc_dt.astimezone(brisbane))
        time = local_dt.strftime("%H:%M:%S")
        return (time)

# Function to return sunrise and sunset time, hourly data from openweather api


def open_weather():
    api_key = os.getenv('ow-api-key')
    lat = -26.26063
    lon = 149.77280
    url = f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&appid={api_key}&units=metric'
    live_data = json.loads(requests.get(url).text)
    ls = ['sunrise', 'sunset', 'description']
    dict_val = {}

    for i in ls:
        if i != "description":
            if i not in dict_val:
                dict_val[i] = []
            dict_val[i].append(timeconversion(live_data['current'][i]))
        else:
            if i not in dict_val:
                dict_val[i] = []
            dict_val[i].append(live_data['current']
                               ['weather'][0]['description'])
    hourly_list = []
    for hourly_data in live_data['hourly']:
        hourly_list.append(hourly_data)
    df_hourly_data = pd.DataFrame(hourly_list)

    # df_hourly_data_copy = df_hourly_data.copy()
    count = 0
    for i in (df_hourly_data['dt']):
        df_hourly_data.loc[count, 'dt'] = timeconversion(i)
        count += 1
    df_hourly_data['weather_descp'] = df_hourly_data['weather'].apply(
        lambda x: x[0]['description'])
    df_hourly_data['weather_icon'] = df_hourly_data['weather'].apply(
        lambda x: x[0]['icon'])
    df_hourly_data = df_hourly_data.drop(['feels_like', 'pressure', 'humidity', 'dew_point', 'uvi',
                                         'clouds', 'visibility', 'wind_speed', 'wind_deg', 'wind_gust', 'weather', 'pop'], axis=1)
    df_hourly_data = df_hourly_data.iloc[:8]

    return dict_val, df_hourly_data


# Function to return last data from database
username = os.getenv('username-postgres')
password = os.getenv('password-postgres')
port = 5432
host = os.getenv('host-postgres-wl')
db_name = os.getenv('db-name-postgres')


def last_data():
    engine = create_engine(
        f'postgresql://{username}:{password}@{host}/{db_name}')

    # Create a table with list of all sensors
    ls_table = ['sensor_type_243_15min', 'sensor_type_242_15min',
                'sensor_type_43_15min', 'sensor_type_504_15min']

    # Loop through ls_table and collect the last data from the database
    list_currentdata = []
    for i in ls_table:

        query = f'SELECT * FROM {i} ORDER BY ts DESC LIMIT 1'
        result = engine.execute(query)
        headers = [col[0] for col in result.cursor.description]
        data = [dict(zip(headers, row)) for row in result]
        list_currentdata.append(data)

        # Create a emply list, add all the data from list and save it to "df_last_current_data"dataframe
    dfs = []
    val = len(list_currentdata)
    for i in range(val):
        dfs.append(pd.DataFrame(list_currentdata[i]))

    df_last_current_data = pd.concat(dfs, axis=1)

    # Remove all the duplicates
    df_last_current_data = df_last_current_data.loc[:, ~
                                                    df_last_current_data.columns.duplicated(keep='first')]
    return df_last_current_data

# Function to return todays data from database


def currentdata():
    # Connect to database
    engine = create_engine(
        f'postgresql://{username}:{password}@{host}/{db_name}')

    # Create a table with list of all sensors
    ls_table = ['sensor_type_243_15min', 'sensor_type_242_15min',
                'sensor_type_43_15min', 'sensor_type_504_15min']

    # Get the current datetime and last midnight
    now = datetime.now()
    last_midnight = datetime.combine(date.today(), datetime.min.time())

    # Loop through ls_table and collect the last data from the database
    list_currentdata = []
    for i in ls_table:
        # query = f'SELECT * FROM {i} ORDER BY ts DESC LIMIT 450'
        query = f"SELECT * FROM {i} WHERE ts BETWEEN '{last_midnight}' AND '{now}' ORDER BY ts ASC"
        result = engine.execute(query)
        headers = [col[0] for col in result.cursor.description]
        data = [dict(zip(headers, row)) for row in result]
        list_currentdata.append(data)

    # Create a emply list, add all the data from list and save it to "df_last_current_data"     dataframe
    df_today = pd.concat([pd.DataFrame(data)
                         for data in list_currentdata], axis=1)
    df_today = df_today.loc[:, ~df_today.columns.duplicated(keep='first')]

    return df_today


'''
ALL CARDS FOR THE LAYOUTS
'''

# CARD 1A ------> WEATHER STATION TIME


card_1a = html.Div([
    dbc.Card(
        dbc.CardBody([
            html.H5(
                children="Weather station time:",
                id='card1a-title'
            ),

            html.P(id='current_time'),
            dcc.Interval(
                id='currenttime_interval',
                interval=1*1000,
                n_intervals=0,

            )
        ], style={
            'height': '100px'
        }
        ),
    )
])

# CARD 1B ------> OPENWEATHER HOURLY UPDATE

card_1b = html.Div([
    dbc.Card(
        dbc.CardBody([
            dbc.Row([
                html.Div(id='openweather-hourly'),
                dcc.Interval(
                    id='openweather_hourlyupdate',
                    interval=1*300000,
                    n_intervals=0,),
            ], style={'height': '200px'}),
        ]),

    )
])

# CARD 1C ------> LAST UPDATED TIME

card_1c = html.Div([
    dbc.Card(
        dbc.CardBody([
            html.H5(children="Last update:",
                    className="card-title", id='card1c-title'),
            html.P(id='last_update', style={'color': 'white'}),
            dcc.Interval(
                id='last_updatetime',
                interval=1*300000,
                n_intervals=0,)
        ], style={'height': '105px'}),

    )
])

theme = {
    'dark': True,
    'high': '#FF0000',
    'moderate': '#FFFB00',
    'low': '#7DFF00',
    'very_low': '#0C00FF',
}
theme_1 = {
    'dark': True,
    'detail': '#007439',
    'primary': '#00EA64',
    'secondary': '#6E6E6E',
}

# CARD 2A ------> TEMPERATURE

card_2a = html.Div([
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H5(children="Temperature:",
                                className="card-title", id='card2a-title', style={'textAlign': 'Center', 'margin': '0em'}),
                        html.Br(),
                    ]),
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        daq.DarkThemeProvider(
                            theme=theme_1,
                            children=daq.Thermometer(
                                id='outside_temp',
                                value=25,
                                max=60,
                                color='red',
                                label='Outside',
                                labelPosition='top',
                            ),
                        ),
                        html.Br(),
                        html.P(id='current_outside_temp',
                               style={'textAlign': 'Center', 'margin': '0em'}),
                        html.P(id='max_outside_temp', style={
                            'textAlign': 'Center', 'margin': '0em'}),
                        html.P(id='min_outside_temp', style={
                            'textAlign': 'Center', 'margin': '0em'}),
                        dcc.Interval(
                            id='last_outsidetemp',
                            interval=1*300000,
                            n_intervals=0,),
                    ]),
                ]),
                dbc.Col([
                    html.Div([
                        daq.DarkThemeProvider(
                            theme=theme_1,
                            children=daq.Thermometer(
                                id='inside_temp',
                                value=25,
                                max=60,
                                color='red',
                                label='Inside',
                                labelPosition='top',
                            ),
                        ),
                        html.Br(),
                        html.P(id='current_inside_temp',
                               style={'textAlign': 'Center', 'margin': '0em'}),
                        html.P(id='max_inside_temp', style={
                            'textAlign': 'Center', 'margin': '0em'}),
                        html.P(id='min_inside_temp', style={
                            'textAlign': 'Center', 'margin': '0em'}),
                        dcc.Interval(
                            id='last_insidetemp',
                            interval=1*300000,
                            n_intervals=0,),
                    ]),
                ]),
                dbc.Col([
                    html.Div([
                        daq.DarkThemeProvider(
                            theme=theme_1,
                            children=daq.Thermometer(
                                id='wind_chill',
                                value=25,
                                max=60,
                                color='red',
                                label='Wind Chill',
                                labelPosition='top',
                            ),
                        ),
                        html.Br(),
                        html.P(id='current_windchill',
                               style={'textAlign': 'Center', 'margin': '0em'}),
                        html.P(id='max_windchill', style={
                            'textAlign': 'Center', 'margin': '0em'}),
                        html.P(id='min_windchill', style={
                            'textAlign': 'Center', 'margin': '0em'}),
                        dcc.Interval(
                            id='last_windchill',
                            interval=1*300000,
                            n_intervals=0,),
                    ]),
                ]),
                dbc.Col([
                    html.Div([
                        daq.DarkThemeProvider(
                            theme=theme_1,
                            children=daq.Thermometer(
                                id='wet_bulb',
                                value=25,
                                max=60,
                                color='red',
                                label='Wet Bulb',
                                labelPosition='top',
                            ),
                        ),
                        html.Br(),
                        html.P(id='current_wetbulb',
                               style={'textAlign': 'Center', 'margin': '0em'}),
                        html.P(id='max_wetbulb', style={
                            'textAlign': 'Center', 'margin': '0em'}),
                        html.P(id='min_wetbulb', style={
                            'textAlign': 'Center', 'margin': '0em'}),
                        dcc.Interval(
                            id='last_wetbulb',
                            interval=1*300000,
                            n_intervals=0,),
                    ]),
                ]),
                dbc.Col([
                    html.Div([
                        html.Br(),
                        html.Br(),
                        daq.DarkThemeProvider(
                            theme=theme_1,
                            children=daq.Gauge(
                                id='humidity_out',
                                value=25,
                                max=100,
                                color={
                                    "ranges": {
                                        "red": [0, 40],
                                        "green": [40, 60],
                                        "blue": [60, 100],
                                    },
                                },
                                scale={
                                    "custom": {
                                        0: {"label": "Dry"},
                                        10: {"label": " "},
                                        20: {"label": " "},
                                        30: {"label": " "},
                                        40: {"label": " "},
                                        50: {"label": "Optimal"},
                                        60: {"label": " "},
                                        70: {"label": " "},
                                        80: {"label": " "},
                                        90: {"label": " "},
                                        100: {"label": "Humid"},
                                    }
                                },
                                label='Outside Humidity',
                                labelPosition='top',
                                size=140
                            ),
                        ),
                        html.P(id='current_hum', style={
                            'textAlign': 'Center', 'margin': '0em'}),
                        dcc.Interval(
                            id='last_humidity',
                            interval=1*300000,
                            n_intervals=0,),
                        html.Br(),
                    ]),
                ]),
                dbc.Col([
                    html.Div([
                        html.Br(),
                        html.Br(),
                        daq.DarkThemeProvider(
                            theme=theme_1,
                            children=daq.Gauge(
                                id='humidity_in',
                                value=25,
                                max=100,
                                color={
                                    "ranges": {
                                        "red": [0, 40],
                                        "green": [40, 60],
                                        "blue": [60, 100],
                                    },
                                },
                                scale={
                                    "custom": {
                                        0: {"label": "Dry"},
                                        10: {"label": " "},
                                        20: {"label": " "},
                                        30: {"label": " "},
                                        40: {"label": " "},
                                        50: {"label": "Optimal"},
                                        60: {"label": " "},
                                        70: {"label": " "},
                                        80: {"label": " "},
                                        90: {"label": " "},
                                        100: {"label": "Humid"},
                                    }
                                },
                                label='Inside Humidity',
                                labelPosition='top',
                                size=140
                            ),
                        ),
                        html.P(id='current_humin', style={
                            'textAlign': 'Center', 'margin': '0em'}),
                        dcc.Interval(
                            id='last_humidityin',
                            interval=1*300000,
                            n_intervals=0,),
                        html.Br(),
                    ]),
                ]),
                dbc.Col([
                    html.Div([
                        daq.DarkThemeProvider(
                            theme=theme_1,
                            children=daq.Thermometer(
                                id='heat_index',
                                value=25,
                                max=60,
                                color='red',
                                label='Heat Index',
                                labelPosition='top',
                            ),
                        ),
                        html.Br(),
                        html.P(id='current_heat_index',
                               style={'textAlign': 'Center', 'margin': '0em'}),
                        html.P(id='max_heat_index', style={
                            'textAlign': 'Center', 'margin': '0em'}),
                        html.P(id='min_heat_index', style={
                            'textAlign': 'Center', 'margin': '0em'}),
                        dcc.Interval(
                            id='last_heatindex',
                            interval=1*300000,
                            n_intervals=0,),
                    ]),
                ]),
                dbc.Col([
                    html.Div([
                        daq.DarkThemeProvider(
                            theme=theme_1,
                            children=daq.Thermometer(
                                id='dew_point',
                                value=25,
                                min=-10,
                                max=60,
                                color='red',
                                label='Dew Point',
                                labelPosition='top',
                            ),
                        ),
                        html.Br(),
                        html.P(id='current_dew_point',
                               style={'textAlign': 'Center', 'margin': '0em'}),
                        html.P(id='max_dew_point', style={
                            'textAlign': 'Center', 'margin': '0em'}),
                        html.P(id='min_dew_point', style={
                            'textAlign': 'Center', 'margin': '0em'}),
                        dcc.Interval(
                            id='last_dewpoint',
                            interval=1*300000,
                            n_intervals=0,),
                    ]),
                ]),
                dbc.Col([
                    html.Div([
                        daq.DarkThemeProvider(
                            theme=theme_1,
                            children=daq.Thermometer(
                                id='thsw_index',
                                value=25,
                                max=60,
                                color='red',
                                label='THSW Index',
                                labelPosition='top',
                            ),
                        ),
                        html.Br(),
                        html.P(id='current_thsw_index',
                               style={'textAlign': 'Center', 'margin': '0em'}),
                        html.P(id='max_thsw_index', style={
                            'textAlign': 'Center', 'margin': '0em'}),
                        html.P(id='min_thsw_index', style={
                            'textAlign': 'Center', 'margin': '0em'}),
                        dcc.Interval(
                            id='last_thsw_index',
                            interval=1*300000,
                            n_intervals=0,),
                    ]),
                ]),
                dbc.Col([
                    html.Div([
                        daq.DarkThemeProvider(
                            theme=theme_1,
                            children=daq.Thermometer(
                                id='thw_index',
                                value=25,
                                max=60,
                                color='red',
                                label='THW Index',
                                labelPosition='top',
                            ),
                        ),
                        html.Br(),
                        html.P(id='current_thw_index',
                               style={'textAlign': 'Center', 'margin': '0em'}),
                        html.P(id='max_thw_index', style={
                            'textAlign': 'Center', 'margin': '0em'}),
                        html.P(id='min_thw_index', style={
                            'textAlign': 'Center', 'margin': '0em'}),
                        dcc.Interval(
                            id='last_thw_index',
                            interval=1*300000,
                            n_intervals=0,),
                    ]),
                ]),
            ], style={'display': 'flex', 'justify-content': 'center', 'height': '424px'}),
        ]),
        dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Br(),
                    ]),
                ])
                ]),

    ])
]),

# CARD 2B ------> SITE CONDITION

card_2b = dbc.Card([
    html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H5(children="Site Conditions:",
                            className="card-title", id='card2b-title', style={'textAlign': 'Center', 'margin-top': '2.0em'}),
                    html.P(id='sunrise-data', style={
                           'textAlign': 'left', 'margin': '0.5em'}),
                    html.P(id='sunset-data', style={
                           'textAlign': 'left', 'margin': '0.5em'}),
                    html.P(id='cloud-description', style={
                           'textAlign': 'left', 'margin': '0.5em'}),
                    html.Br(),
                    dcc.Interval(
                        id='last_updatetime_card2b',
                        interval=1*300000,
                        n_intervals=0,)
                ])
            ])
        ])
    ])
], style={'display': 'flex', 'justify-content': 'center', 'height': '150px'})

# CARD 2C ------> SOLAR RADIATION

card_2c = dbc.Card([
    html.Div([
        dbc.Row([
            dbc.Col(html.Div([
                html.Br(),
                html.H5(children="Solar Radiation:",
                        className="card-title", id='card3a-title', style={'textAlign': 'Center'}),
            ]),
            ),
        ]),

        dbc.Row([
            dbc.Col([
                html.Div([
                    # html.Br(),
                    daq.DarkThemeProvider(
                        theme=theme_1,
                        children=daq.Gauge(
                            id='solar_val',
                            label=f'Irradiance W/m\N{SUPERSCRIPT TWO}',
                            value=0,
                            units='W/m2',
                            # showCurrentValue=True,
                            min=0,
                            max=2000,
                            color={"gradient": True, "ranges": {
                                "red": [0, 960], "green":[960, 1060], "#FF0000":[1060, 2000]}},
                            # color={"gradient": True, "ranges": {
                            #    "green": [940, 960], "yellow":[960, 1060], "red":[1060, 1110]}},
                            size=150
                        ),
                    ),
                    dcc.Interval(
                        id='last_updatetime2b',
                        interval=1*300000,
                        n_intervals=0,)

                ])
            ], style={'display': 'flex', 'justify-content': 'center', 'height': '208px'}),
        ]),
        dbc.Row([
            dbc.Col([
                html.P(id='current_solarstat', style={
                    'textAlign': 'center', 'margin': '0em', 'font-size': '15px'}),
                html.P(id='max_solarstat', style={
                    'textAlign': 'center', 'margin': '0em', 'font-size': '15px'}),
                html.P(id='min_solarstat', style={
                    'textAlign': 'center', 'margin': '0em', 'font-size': '15px'}),
            ]),
        ]),
        dbc.Row([
            html.Div(
                html.Br(),
            )
        ]),
    ])
])

# CARD 3A ------> BAROMETER

card_3a = dbc.Card([
    html.Div([
        dbc.Row([
            dbc.Col(html.Div([
                html.Br(),
                html.H5(children="Barometer:",
                        className="card-title", id='card2b-title', style={'textAlign': 'Center'}),
            ]),
            ),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    # html.Br(),
                    daq.DarkThemeProvider(
                        theme=theme_1,
                        children=daq.Gauge(
                            id='barometergraph',
                            label='Barometeric Pressure hPa',
                            value=0,
                            units='hPa',
                            # showCurrentValue=True,
                            min=0,
                            max=2000,
                            color={"gradient": True, "ranges": {
                                "red": [0, 960], "green":[960, 1060], "#FF0000":[1060, 2000]}},
                            # color={"gradient": True, "ranges": {
                            #    "green": [940, 960], "yellow":[960, 1060], "red":[1060, 1110]}},
                            size=150
                        ),
                    ),
                    dcc.Interval(
                        id='last_updatetime2c',
                        interval=1*300000,
                        n_intervals=0,)

                ])
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div(
                    children=[
                        html.Div(
                            id='arrow-container',
                            style={
                                'display': 'flex', 'justify-content': 'center', 'align-items': 'center'},
                            children=[
                                DashIconify(
                                    icon="material-symbols:trending-up",
                                    style={'position': 'absolute',
                                           'color': 'green'},
                                    width=30,
                                ),
                            ]
                        ),
                    ]
                )
            ]),

        ]),
        dbc.Row([
            dbc.Col([
                html.P(id='trend_status', style={
                       'textAlign': 'Center', 'margin': '0em'})
            ]),
        ]),
        dbc.Row([
            html.Div(
                html.Br(),
            )
        ]),
        dbc.Row([
            dbc.Col([
                    html.P(id='trend_status', style={
                        'textAlign': 'Center', 'margin': '0em'})
                    ]),
        ]),

        dbc.Row([
            dbc.Col([
                html.Div([
                    html.P(id='current_baro', style={
                           'textAlign': 'Center', 'margin': '0em'}),
                ])
            ]),
        ]),
        dbc.Row([
            html.Div(
                html.Br(),
            )
        ]),
        dbc.Row([
            html.Div(
                html.Br(),
            )
        ]),
    ])
], style={'display': 'flex', 'justify-content': 'center', 'height': '400px'})

# CARD 3B ------> WIND SPEED

card_3b = dbc.Card([
    html.Div([
        dbc.Row([
            dbc.Col(html.Div([
                html.Br(),
                html.H5(children="Wind Speed: ",
                        className="card-title", id='card3c-title', style={'textAlign': 'Center'}),
            ]),
            ),
        ]),

        dbc.Row([
            dbc.Col([
                html.Div([
                    # html.Br(),
                    daq.DarkThemeProvider(
                        theme=theme_1,
                        children=daq.Gauge(
                            id='wind_speed',
                            label=f'Wind speed m/sec',
                            value=0,
                            units='m/sec',
                            # showCurrentValue=True,
                            min=0,
                            max=40,
                            color={"gradient": True, "ranges": {
                                "yellow": [0, 6], "orange": [6, 8], "green": [8, 12], "pink":[12, 20], "red":[20, 30], "blue":[30, 40]}},
                            # color={"gradient": True, "ranges": {
                            #    "green": [940, 960], "yellow":[960, 1060], "red":[1060, 1110]}},
                            size=150
                        ),
                    ),
                    dcc.Interval(
                        id='last_updatetime3c',
                        interval=1*300000,
                        n_intervals=0,),
                    html.P(id='current_windspeed', style={
                        'textAlign': 'Center', 'margin': '0em'}),
                    html.P(id='max_windspeed', style={
                        'textAlign': 'Center', 'margin': '0em'}),
                    html.P(id='avg_windspeed', style={
                        'textAlign': 'Center', 'margin': '0em'}),

                ])
            ], style={'display': 'flex', 'justify-content': 'center', 'height': '316px'}),
        ]),

        dbc.Row([
            html.Div(
                html.Br(),
            )
        ]),
    ])
])

# CARD 3C ------> WIND DIRECTION

card_3c = dbc.Card([
    html.Div([
        dbc.Row([
            dbc.Col(html.Div([
                html.Br(),
                html.H5(children="Wind Direction: ",
                        className="card-title", id='card3c-title', style={'textAlign': 'Center'}),
            ]),
            ),
        ]),

        dbc.Row([
            dbc.Col([
                html.Div([
                    html.P(children="Wind direction degree",
                           id="wind_dir-title", style={'textAlign': 'Center'}),
                    dcc.Loading(
                        id='wind-dir-loading',
                        children=[dcc.Graph(id='wind_dir', style={
                            'width': '100%', 'height': '100%'})],
                        type='circle',
                    ),
                    dcc.Interval(
                        id='last_updatetime3d',
                        interval=1*300000,
                        n_intervals=0,),
                ]),
            ], style={'display': 'flex', 'justify-content': 'center', 'height': '292px'}),
        ]),
        dbc.Row([
            html.Br(),
            html.P(id='current_wind_dir', style={
                'textAlign': 'Center', 'margin': '0em'}),
        ]),
        dbc.Row([
            html.Div(
                html.Br(),
            )
        ]),
    ])
])

# CARD 3D ------> WIND ROSE

card_3d = dbc.Card([
    html.Div([
        dbc.Row([
            dbc.Col(html.Div([
                html.Br(),
                html.H5(children="Wind Rose: ",
                        className="card-title", id='card3d-title', style={'textAlign': 'Center'}),
            ]),
            ),
        ]),

        dbc.Row([
            dbc.Col([
                html.Div([
                    dcc.Loading(
                        id='windrose-loading',
                        children=[dcc.Graph(id='wind_rose')],
                        type='circle',
                    ),
                    dcc.Interval(
                        id='last_updatetime3e',
                        interval=1*300000,
                        n_intervals=0,),
                ]),
            ], style={'display': 'flex', 'justify-content': 'center', 'height': '340px'}),
        ]),
    ])
])

# CARD 3E ------> RAINFALL

card_3e = dbc.Card([
    html.Div([
        dbc.Row([
            dbc.Col([
                html.Br(),
                html.H5(children="Rainfall:", className="card-title",
                        id='card3f-title', style={'textAlign': 'Center'}),
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    daq.DarkThemeProvider(
                        theme=theme_1,
                        children=daq.Tank(
                            id='rainfall_daily',
                            value=1,
                            max=3,
                            color='blue',
                            label='Current Rainfall',
                            labelPosition='top',
                            scale={'interval': 1, 'labelInterval': 1},
                        ),
                    ),
                    html.Br(),
                    html.P(id='rainfall_daily_data',
                           style={'textAlign': 'Center', 'margin':
                                  '0em'}),
                    dcc.Interval(
                        id='last_rainfall_daily',
                        interval=1*300000,
                        n_intervals=0,),
                ])
            ]),
            dbc.Col([
                html.Div([
                    daq.DarkThemeProvider(
                        theme=theme_1,
                        children=daq.Tank(
                            id='rainfall_monthly',
                            value=1,
                            max=3,
                            color='blue',
                            label='Monthly Rainfall',
                            labelPosition='top',
                            scale={'interval': 1, 'labelInterval': 1},
                        ),
                    ),
                    html.Br(),
                    html.P(id='rainfall_monthly_data',
                           style={'textAlign': 'Center', 'margin':
                                  '0em'}),
                    dcc.Interval(
                        id='last_rainfall_monthly',
                        interval=1*300000,
                        n_intervals=0,),
                ])
            ]),
            dbc.Col([
                html.Div([
                    daq.DarkThemeProvider(
                        theme=theme_1,
                        children=daq.Tank(
                            id='rainfall_yearly',
                            value=1,
                            max=3,
                            color='blue',
                            label='Yearly Rainfall',
                            labelPosition='top',
                            scale={'interval': 4, 'labelInterval': 4},
                        ),
                    ),
                    html.Br(),
                    html.P(id='rainfall_yearly_data',
                           style={'textAlign': 'Center', 'margin':
                                  '0em'}),
                    dcc.Interval(
                        id='last_rainfall_yearly',
                        interval=1*300000,
                        n_intervals=0,),
                ])
            ]),
        ]),
        dbc.Row([
            html.Div(
                html.P(id="last_date", style={
                       'textAlign': 'Center', 'margin': '0em'})
            ),
        ]),
        dbc.Row([
            html.Div(
                html.Br(),
            )
        ]),
    ]),
], style={'display': 'flex', 'justify-content': 'center', 'height': '400px'},)


# Final layout position of all cards
layout = [
    dbc.Row([
            dbc.Col([
                dbc.Row([
                    dbc.Col(card_1a, width=12, lg=12),
                ]),
                html.Br(),
                dbc.Row([
                    dbc.Col(card_1c, width=12, lg=12),
                ]),
            ]),
            dbc.Col(card_1b, width=10, lg=10),
            ]),
    html.Br(),

    dbc.Row([
            dbc.Col(card_2a, xs=10, lg=10),
            dbc.Col([
                dbc.Row([
                    dbc.Col(card_2b, xs=12, lg=12),
                ]),
                html.Br(),
                dbc.Row([
                    dbc.Col(card_2c, xs=12, lg=12),
                ])
            ])
            ]),

    html.Br(),
    dbc.Row([
        dbc.Col(card_3a, width=2, lg=2),
        dbc.Col(card_3b, width=2, lg=2),
        dbc.Col(card_3c, width=2, lg=2),
        dbc.Col(card_3d, width=2, lg=2),
        dbc.Col(card_3e, width=4, lg=4),



    ]),
    html.Br(),
]

'''
CALL BACK FUNCTION FOR ALL CARD 
'''

# callback for card_1a-->WEATHER STATION TIME


@ callback(Output('current_time', 'children'),
           Input('currenttime_interval', 'n_intervals'))
def current_time(n):
    bris_Tz = pytz.timezone("Australia/Brisbane")
    timeInbris = datetime.now(bris_Tz)
    currentTime = timeInbris.strftime("%d/%m/%Y - %H:%M:%S")
    return currentTime

# callback for card_1b-->OPEN WEATHER HOURLY DATA


@callback(
    (Output('openweather-hourly', 'children')),
    (Input('openweather_hourlyupdate', 'n_intervals'))
)
def openweather_hourly(n):
    hourly_data_dict, hourly_data_df = open_weather()
    col_children_list = []
    for i in hourly_data_df.index:
        time = hourly_data_df['dt'][i]
        icon_val = hourly_data_df['weather_icon'][i]
        description = hourly_data_df['weather_descp'][i]
        temp = f"{hourly_data_df['temp'][i]}°C"
        col_children = (dbc.Col([
            html.P(id=f'time{i}', children=time, style={
                   'margin': '0em', 'textAlign': 'Center'}),
            html.Img(
                id=f'icon{i}', src=f"https://openweathermap.org/img/wn/{icon_val}@2x.png",
                style={'display': 'block',  'margin': 'auto'}),
            html.P(id=f'description{i}', children=description, style={
                'margin': '0em', 'top-margin': '0em', 'textAlign': 'Center'}),
            html.P(id=f'temp{i}', children=temp, style={
                'margin': '0em', 'top-margin': '0em', 'textAlign': 'Center'}),
        ]))
        col_children_list.append(col_children)

    return dbc.Row(col_children_list)


# callback for card_1c-->lAST UPDATED TIME

@ callback(Output('last_update', 'children'),
           Output('last_update', 'style'),
           Input('last_updatetime', 'n_intervals'))
def update_currentdata(n):
    df_today = currentdata()
    if df_today.empty:
        df_offline = last_data()
        updated_time = datetime.strptime(df_offline['ts'].iloc[-1:].astype(str).to_string(
            index=False).strip(), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%y - %H:%M:%S")
        style = {'color': 'red'}
        return f"{updated_time}", style
    else:
        # timestamp = df_currentdata['ts'].astype(str).to_string(index=False).strip()
        # updated_time = datetime.strptime(
        #   timestamp, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%y - %H:%M:%S")
        updated_time = datetime.strptime(df_today['ts'].iloc[-1:].astype(str).to_string(
            index=False).strip(), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%y - %H:%M:%S")
        style = {'color': 'white'}
        return updated_time, style


# callback for card_2a --->OUTSIDE-TEMPERATURE

@ callback(Output('outside_temp', 'value'),
           Output('outside_temp', 'color'),
           Output('current_outside_temp', 'children'),
           Output('max_outside_temp', 'children'),
           Output('min_outside_temp', 'children'),
           Input('last_outsidetemp', 'n_intervals'))
def updatetemp(n):
    df_currentdata = last_data()
    if df_currentdata.empty:
        current_outsidetemp = 0
        color_val = 'red'
        return current_outsidetemp, color_val, " ", " ", " "
    else:
        df_currentdata = currentdata()
        current_outsidetemp = float(df_currentdata['temp'].iloc[-1])

        if current_outsidetemp == 0 and current_outsidetemp <= 10:
            color_val = "blue"
        elif current_outsidetemp >= 10 and current_outsidetemp <= 25:
            color_val = "yellow"
        elif current_outsidetemp > 25 and current_outsidetemp <= 40:
            color_val = "green"
        else:
            color_val = "red"
        max_temp = float(df_currentdata['temp'].max())
        min_temp = float(df_currentdata['temp'].min())
        return current_outsidetemp, color_val, f'Current: {current_outsidetemp}°C', f'High: {max_temp}°C', f'Low: {min_temp}°C'

# callback for card_2a --->INSIDE-TEMPERATURE


@ callback(Output('inside_temp', 'value'),
           Output('inside_temp', 'color'),
           Output('current_inside_temp', 'children'),
           Output('max_inside_temp', 'children'),
           Output('min_inside_temp', 'children'),
           Input('last_insidetemp', 'n_intervals'))
def updatetemp(n):
    df_currentdata = last_data()
    if df_currentdata.empty:
        current_outsidetemp = 0
        color_val = 'red'
        return current_outsidetemp, color_val, " ", " ", " "
    else:
        df_currentdata = currentdata()
        current_outsidetemp = float(df_currentdata['temp_in'].iloc[-1])

        if current_outsidetemp == 0 and current_outsidetemp <= 10:
            color_val = "blue"
        elif current_outsidetemp >= 10 and current_outsidetemp <= 25:
            color_val = "yellow"
        elif current_outsidetemp > 25 and current_outsidetemp <= 40:
            color_val = "green"
        else:
            color_val = "red"
        max_temp = float(df_currentdata['temp_in'].max())
        min_temp = float(df_currentdata['temp_in'].min())
        return current_outsidetemp, color_val, f'Current: {current_outsidetemp}°C', f'High: {max_temp}°C', f'Low: {min_temp}°C'

# callback for card_2a --->WINDCHILL


@ callback(Output('wind_chill', 'value'),
           Output('wind_chill', 'color'),
           Output('current_windchill', 'children'),
           Output('max_windchill', 'children'),
           Output('min_windchill', 'children'),
           Input('last_windchill', 'n_intervals'))
def updatetemp(n):
    df_currentdata = last_data()
    if df_currentdata.empty:
        current_outsidetemp = 0
        color_val = 'red'
        return current_outsidetemp, color_val, " ", " ", " "
    else:
        df_currentdata = currentdata()
        current_outsidetemp = float(df_currentdata['wind_chill'].iloc[-1])

        if current_outsidetemp == 0 and current_outsidetemp <= 10:
            color_val = "blue"
        elif current_outsidetemp >= 10 and current_outsidetemp <= 25:
            color_val = "yellow"
        elif current_outsidetemp > 25 and current_outsidetemp <= 40:
            color_val = "green"
        else:
            color_val = "red"
        max_temp = float(df_currentdata['wind_chill'].max())
        min_temp = float(df_currentdata['wind_chill'].min())
        return current_outsidetemp, color_val, f'Current: {current_outsidetemp}°C', f'High: {max_temp}°C', f'Low: {min_temp}°C'

# callback for card_2a --->WET BULB


@ callback(Output('wet_bulb', 'value'),
           Output('wet_bulb', 'color'),
           Output('current_wetbulb', 'children'),
           Output('max_wetbulb', 'children'),
           Output('min_wetbulb', 'children'),
           Input('last_wetbulb', 'n_intervals'))
def updatetemp(n):
    df_currentdata = last_data()
    if df_currentdata.empty:
        current_outsidetemp = 0
        color_val = 'red'
        return current_outsidetemp, color_val, " ", " ", " "

    else:
        df_currentdata = currentdata()
        current_outsidetemp = float(df_currentdata['wet_bulb'].iloc[-1])

        if current_outsidetemp == 0 and current_outsidetemp <= 10:
            color_val = "blue"
        elif current_outsidetemp >= 10 and current_outsidetemp <= 25:
            color_val = "yellow"
        elif current_outsidetemp > 25 and current_outsidetemp <= 40:
            color_val = "green"
        else:
            color_val = "red"
        max_temp = float(df_currentdata['wet_bulb'].max())
        min_temp = float(df_currentdata['wet_bulb'].min())
        return current_outsidetemp, color_val, f'Current: {current_outsidetemp}°C', f'High: {max_temp}°C', f'Low: {min_temp}°C'

# callback for card_2a --->HEAT INDEX


@ callback(Output('heat_index', 'value'),
           Output('heat_index', 'color'),
           Output('current_heat_index', 'children'),
           Output('max_heat_index', 'children'),
           Output('min_heat_index', 'children'),
           Input('last_heatindex', 'n_intervals'))
def updatetemp(n):
    df_currentdata = last_data()
    if df_currentdata.empty:
        current_outsidetemp = 0
        color_val = 'red'
        return current_outsidetemp, color_val, " ", " ", " "

    else:
        df_currentdata = currentdata()
        current_outsidetemp = float(df_currentdata['heat_index_in'].iloc[-1])

        if current_outsidetemp == 0 and current_outsidetemp <= 10:
            color_val = "blue"
        elif current_outsidetemp >= 10 and current_outsidetemp <= 25:
            color_val = "yellow"
        elif current_outsidetemp > 25 and current_outsidetemp <= 40:
            color_val = "green"
        else:
            color_val = "red"
        max_temp = float(df_currentdata['heat_index_in'].max())
        min_temp = float(df_currentdata['heat_index_in'].min())
        return current_outsidetemp, color_val, f'Current: {current_outsidetemp}°C', f'High: {max_temp}°C', f'Low: {min_temp}°C'
# callback for card_2a --->DEW POINT


@ callback(Output('dew_point', 'value'),
           Output('dew_point', 'color'),
           Output('current_dew_point', 'children'),
           Output('max_dew_point', 'children'),
           Output('min_dew_point', 'children'),
           Input('last_dewpoint', 'n_intervals'))
def updatetemp(n):
    df_currentdata = last_data()
    if df_currentdata.empty:
        current_outsidetemp = 0
        color_val = 'red'
        return current_outsidetemp, color_val, " ", " ", " "
    else:
        df_currentdata = currentdata()
        current_outsidetemp = float(df_currentdata['dew_point'].iloc[-1])

        if current_outsidetemp == 0 and current_outsidetemp <= 10:
            color_val = "blue"
        elif current_outsidetemp >= 10 and current_outsidetemp <= 25:
            color_val = "yellow"
        elif current_outsidetemp > 25 and current_outsidetemp <= 40:
            color_val = "green"
        else:
            color_val = "red"
        max_temp = float(df_currentdata['dew_point'].max())
        min_temp = float(df_currentdata['dew_point'].min())
        return current_outsidetemp, color_val, f'Current: {current_outsidetemp}°C', f'High: {max_temp}°C', f'Low: {min_temp}°C'

# callback for card_2a --->THSW index


@ callback(Output('thsw_index', 'value'),
           Output('thsw_index', 'color'),
           Output('current_thsw_index', 'children'),
           Output('max_thsw_index', 'children'),
           Output('min_thsw_index', 'children'),
           Input('last_thsw_index', 'n_intervals'))
def updatetemp(n):
    df_currentdata = last_data()
    if df_currentdata.empty:
        current_outsidetemp = 0
        color_val = 'red'
        return current_outsidetemp, color_val, " ", " ", " "
    else:
        df_currentdata = currentdata()
        current_outsidetemp = float(df_currentdata['thsw_index'].iloc[-1])
        if current_outsidetemp == 0 and current_outsidetemp <= 10:
            color_val = "blue"
        elif current_outsidetemp >= 10 and current_outsidetemp <= 25:
            color_val = "yellow"
        elif current_outsidetemp > 25 and current_outsidetemp <= 40:
            color_val = "green"
        else:
            color_val = "red"
        max_temp = float(df_currentdata['thsw_index'].max())
        min_temp = float(df_currentdata['thsw_index'].min())
        return current_outsidetemp, color_val, f'Current: {current_outsidetemp}°C', f'High: {max_temp}°C', f'Low: {min_temp}°C'

# callback for card_2a --->THW index


@ callback(Output('thw_index', 'value'),
           Output('thw_index', 'color'),
           Output('current_thw_index', 'children'),
           Output('max_thw_index', 'children'),
           Output('min_thw_index', 'children'),
           Input('last_thw_index', 'n_intervals'))
def updatetemp(n):
    df_currentdata = last_data()

    if df_currentdata.empty:
        current_outsidetemp = 0
        color_val = 'red'
        return current_outsidetemp, color_val, " ", " ", " "
    else:
        df_currentdata = currentdata()
        current_outsidetemp = float(df_currentdata['thw_index'].iloc[-1])

        if current_outsidetemp == 0 and current_outsidetemp <= 10:
            color_val = "blue"
        elif current_outsidetemp >= 10 and current_outsidetemp <= 25:
            color_val = "yellow"
        elif current_outsidetemp > 25 and current_outsidetemp <= 40:
            color_val = "green"
        else:
            color_val = "red"
        max_temp = float(df_currentdata['thw_index'].max())
        min_temp = float(df_currentdata['thw_index'].min())
        return current_outsidetemp, color_val, f'Current: {current_outsidetemp}°C', f'High: {max_temp}°C', f'Low: {min_temp}°C'


# callback for card_2a --->Humidity out


@ callback(Output('humidity_out', 'value'),
           Output('current_hum', 'children'),
           Input('last_humidity', 'n_intervals'))
def updatetemp(n):
    df_currentdata = last_data()
    if df_currentdata.empty:
        current_outsidetemp = 0
        return current_outsidetemp, " "
    else:
        df_currentdata = currentdata()
        current_outsidetemp = float(df_currentdata['hum'].iloc[-1])
        return current_outsidetemp, f'Current: {current_outsidetemp}%'


# callback for card_2a --->Humidity in


@ callback(Output('humidity_in', 'value'),
           Output('current_humin', 'children'),
           Input('last_humidityin', 'n_intervals'))
def updatetemp(n):
    df_currentdata = last_data()
    if df_currentdata.empty:
        current_outsidetemp = 0
        return current_outsidetemp, " "
    else:
        df_currentdata = currentdata()
        current_outsidetemp = float(df_currentdata['hum_in'].iloc[-1])
        return current_outsidetemp, f'Current: {current_outsidetemp}%'

# callback for 2b---> OPENWEATHER DATA SITE CONDITIONS


@callback(
    (Output('sunrise-data', 'children')),
    (Output('sunset-data', 'children')),
    (Output('cloud-description', 'children')),
    (Input('last_updatetime_card2b', 'n_intervals'))
)
def openweather(n):
    dict_openweather = open_weather()
    return f"Sunrise: {list(dict_openweather[0].values())[0][0]}", f"Sunset: {list(dict_openweather[0].values())[1][0]}", f" Description: {list(dict_openweather[0].values())[2][0]}"


# callback for card_2c --->SOLAR RADIATION


@ callback(Output('solar_val', 'value'),
           Output('current_solarstat', 'children'),
           Output('max_solarstat', 'children'),
           Output('min_solarstat', 'children'),
           Input('last_updatetime2b', 'n_intervals'))
def updatesolar(n):
    df_currentdata = last_data()

    if df_currentdata.empty:
        current_solar = 0
        return current_solar, " ", " ", " "

    else:
        df_currentdata = currentdata()
        current_solar = float(df_currentdata['solar_rad'].iloc[-1])
        max_solar = float(df_currentdata.solar_rad.max())
        min_solar = float(
            df_currentdata['solar_rad'][df_currentdata['solar_rad'] != 0].min())
        return current_solar, f"Current: {current_solar}W/m\N{SUPERSCRIPT TWO}", f"High: {max_solar}W/m\N{SUPERSCRIPT TWO}", f"Low: {min_solar}W/m\N{SUPERSCRIPT TWO}"

# callback for card_3a --->BAROMETER


@ callback(Output('barometergraph', 'value'),
           Output('current_baro', 'children'),
           Output('arrow-container', 'children'),
           Output('trend_status', 'children'),
           Output('trend_status', 'style'),
           Input('last_updatetime2c', 'n_intervals'))
def barometer_graph(n):
    df_currentdata = last_data()
    if df_currentdata.empty:
        value = 0
        new_arrow = DashIconify(
            icon="eva:minus-outline",
            style={'color': 'red', 'position': 'absolute'},
            width=30,
        )
        trend_style = {'textAlign': 'Center',
                       'margin': '0em', 'color': 'red'}
        return value, " ", new_arrow, " ", trend_style

    else:
        df_currentdata = currentdata()
        value = float((df_currentdata['bar_sea_level']).iloc[-1])

        if float((df_currentdata['bar_trend']).iloc[-1]) < 0:
            new_arrow = DashIconify(
                icon="material-symbols:trending-down",
                style={'color': 'red', 'position': 'absolute'},
                width=30,
            )
            status = f"Falling by {float((df_currentdata['bar_trend']).iloc[-1])}hPa"
            trend_style = {'textAlign': 'Center',
                           'margin': '0em', 'color': 'red'}

        else:
            new_arrow = DashIconify(
                icon="material-symbols:trending-up",
                style={'color': 'green', 'position': 'absolute'},
                width=30,
            )
            status = f"Rising by {float((df_currentdata['bar_trend']).iloc[-1])}hPa"
            trend_style = {'textAlign': 'Center',
                           'margin': '0em', 'color': 'green'}
        return value, f"Current: {value}hPa", new_arrow, status, trend_style


# callback for card_3b ---> WIND SPEED


@callback(Output('wind_speed', 'value'),
          Output('current_windspeed', 'children'),
          Output('max_windspeed', 'children'),
          Output('avg_windspeed', 'children'),
          Input('last_updatetime3c', 'n_intervals'))
def wind_speed(n):
    df_currentdata = last_data()
    if df_currentdata.empty:
        current_speed = 0
        return current_speed, " ", "", ""

    else:
        df_currentdata = currentdata()
        current_speed = float((df_currentdata['wind_speed_last']).iloc[-1])
        max_windspeed = float(df_currentdata.wind_speed_last.max())
        avg_windspeed = float(
            (df_currentdata['wind_speed_avg_last_10_min']).iloc[-1])
        return current_speed, f"Current: {current_speed}m/sec", f"Max: {max_windspeed}m/sec", f"Average 10 mins: {avg_windspeed}m/sec"


# callback for card_3c ---> WIND DIRECTION


@ callback(Output('wind_dir', 'figure'),
           Output('current_wind_dir', 'children'),
           Input('last_updatetime3d', 'n_intervals'))
def winddir_graph(n):
    df_currentdata = last_data()
    if df_currentdata.empty:
        current_dir = 0
    else:
        df_currentdata = currentdata()
        current_dir = float((df_currentdata['wind_dir_last']).iloc[-1])
        current_speed = float((df_currentdata['wind_speed_last']).iloc[-1])
    fig = go.Figure(go.Barpolar(
        r=[current_speed],
        theta=[current_dir],
        width=[15],
        marker_color=["#E4FF87"],
        marker_line_color="black",
        marker_line_width=2,
        opacity=0.8,
        hovertemplate='Wind Speed: %{r}<br>Wind Direction: %{theta}'
    ))
    fig = fig.update_layout(
        template="plotly_dark",
        polar=dict(
            radialaxis=dict(range=[0, 3], showticklabels=False, ticks=''),
            angularaxis=dict(showticklabels=True, ticks='', rotation=90,       direction="clockwise",
                             tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                             ticktext=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']),
        ),
        margin=dict(l=20, r=20, t=20, b=20),
        width=200,
        height=200,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    return fig, f"Current: {current_dir}°"


# callback for card_3d ---> WIND ROSE

@callback(Output('wind_rose', 'figure'),
          Input('last_updatetime3e', 'n_intervals'))
def windrose_graph(n):
    WR = WindRose()
    WR.df = currentdata()
    if WR.df.empty:
        fig = px.bar_polar(
            WR.df, color_discrete_sequence=px.colors.sequential.Plasma_r)
        fig = fig.update_layout(template="plotly_dark",
                                width=350,
                                height=300,
                                showlegend=False,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                polar=dict(
                                    radialaxis=dict(
                                         showticklabels=False, ticks=''),
                                ),
                                )
        return fig

    else:
        names = {
            'wind_speed_last': 'ws',
            'wind_dir_last': 'wd'
        }
        WR.calc_stats(normed=False, bins=6, variable_names=names)
        windrose_data = WR.wind_df.loc[-1:]
        fig = px.bar_polar(windrose_data, r="frequency", theta="direction",
                           color="speed", color_discrete_sequence=px.colors.sequential.Plasma_r)
        fig = fig.update_layout(template="plotly_dark",
                                width=350,
                                height=300,
                                polar=dict(
                                    radialaxis=dict(
                                        showticklabels=False, ticks=''),
                                ),
                                showlegend=False,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                legend=dict(
                                    orientation="v",
                                    entrywidth=10,
                                    yanchor="top",
                                    y=1.5,
                                    xanchor="left",
                                    x=1.2,
                                    font=dict(
                                        size=10,

                                    )
                                )

                                )
        return fig

# callback for card_3e ---> RAINFALL


@callback(
    (Output('rainfall_daily', 'value')),
    (Output('rainfall_daily', 'max')),
    (Output('rainfall_daily_data', 'children')),
    (Input('last_rainfall_daily', 'n_intervals')),
)
def rainfalldaily(n):
    df_currentdata = last_data()
    current_rainfall_daily = float(
        df_currentdata['rainfall_daily_mm'].iloc[-1])
    max_value_scale = round(current_rainfall_daily+2, 0)
    return current_rainfall_daily, max_value_scale, f"Current rainfall: {current_rainfall_daily}mm"


# Callback for card_3e ---> RAINFALL MONTHLY

@callback(
    (Output('rainfall_monthly', 'value')),
    (Output('rainfall_monthly', 'max')),
    (Output('rainfall_monthly_data', 'children')),
    (Input('last_rainfall_monthly', 'n_intervals')),
)
def rainfalldaily(n):
    df_currentdata = last_data()
    current_rainfall_monthly = float(
        df_currentdata['rainfall_monthly_mm'].iloc[-1])
    max_value_scale = round(current_rainfall_monthly+2, 0)
    return current_rainfall_monthly, max_value_scale, f"Monthly rainfall: {current_rainfall_monthly}mm"

# Callback for card_3e ---> RAINFALL YEARLY


@callback(
    (Output('rainfall_yearly', 'value')),
    (Output('rainfall_yearly', 'max')),
    (Output('rainfall_yearly_data', 'children')),
    (Output('last_date', 'children')),
    (Input('last_rainfall_yearly', 'n_intervals')),
)
def rainfalldaily(n):
    df_currentdata = last_data()
    current_rainfall_yearly = float(
        df_currentdata['rainfall_year_mm'].iloc[-1])
    max_value_scale = round(current_rainfall_yearly+10, 0)
    last_storm_date = datetime.strptime(df_currentdata['rain_storm_last_start_at'].iloc[-1:].astype(str).to_string(
        index=False).strip(), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%y - %H:%M:%S")
    return current_rainfall_yearly, max_value_scale, f"Yearly rainfall: {current_rainfall_yearly}mm", f"Last storm: {last_storm_date}"
