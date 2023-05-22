'''
DASH PYTHON PAGE - 2 ---> Historical Data Visualisation
'''
import datetime
import dash
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, callback, Input, Output
import time
import pandas as pd
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
from urllib.parse import quote
import plotly.express as px
import os
from dotenv import load_dotenv
import plotly.graph_objects as go

load_dotenv()
'''
DASH AND MAKE THIS PAGE AS PAGE 2
'''

dash.register_page(__name__, name='Historical data')

'''
FUNCTIONS
'''

# Function to return the custom query data


def currentdata(custom_query):
    # Connect to database
    username = os.getenv('username-postgres')
    password = os.getenv('password-postgres')
    port = 5432
    host = os.getenv('host-postgres-wl')
    db_name = os.getenv('db-name-postgres')

    engine = create_engine(
        f'postgresql://{username}:{password}@{host}/{db_name}')

    # Loop through ls_table and collect the last data from the database
    list_currentdata = []
    # query = f'SELECT * FROM {i} ORDER BY ts DESC LIMIT 450'
    query = custom_query
    result = engine.execute(query)
    headers = [col[0] for col in result.cursor.description]
    data = [dict(zip(headers, row)) for row in result]
    list_currentdata.append(data)

    # Create a emply list, add all the data from list and save it to "df_last_current_data" dataframe
    df_custom = pd.concat([pd.DataFrame(data)
                           for data in list_currentdata], axis=1)
    df_custom = df_custom.loc[:, ~df_custom.columns.duplicated(keep='first')]

    return df_custom

# Function to return the rain graph


def display_rain_graph():
    query = "Select rain_storm_last_end_at, rain_storm_last_mm FROM sensor_type_43_15min "
    df = currentdata(query)
    unique_rain_day = df['rain_storm_last_end_at'].unique()
    data = {}
    for days in unique_rain_day:
        rain_storm = df.loc[df['rain_storm_last_end_at']
                            == days, 'rain_storm_last_mm'].iloc[0]
        data[days] = rain_storm
    new_unique_rain_day = pd.DataFrame(list(data.items()), columns=[
                                       'rain_storm_last_end_at', 'rain_storm_last_mm'])
    if not new_unique_rain_day.empty:
        new_unique_rain_day.columns = [
            'Rain storm last end at', 'Rainfall (mm)']
    start_date = "2023/01/01"
    end_date = "2023/12/31"
    dates = pd.date_range(start_date, end_date, freq='D')
    df = pd.DataFrame({'Rain storm last end at': dates})
    df['Rainfall (mm)'] = 0
    data = new_unique_rain_day.to_dict(orient='dict')
    df['Month'] = df['Rain storm last end at'].dt.month

    rainfall_data = {}

    for key, value in data['Rain storm last end at'].items():
        date = value.strftime('%Y/%m/%d')
        rainfall = data['Rainfall (mm)'][key]
        rainfall_data[date] = rainfall

    for date, rainfall in rainfall_data.items():
        df.loc[df['Rain storm last end at'] ==
               pd.to_datetime(date), 'Rainfall (mm)'] = rainfall

    df = df.reset_index(drop=True)
    grouped = df.groupby('Month')['Rainfall (mm)'].apply(list)
    date_ls = []
    rainfall_data = [grouped[month] for month in grouped.index]
    for i in range(1, 32, 1):
        date_ls.append(i)

    fig = go.Figure(data=go.Heatmap(
        z=[grouped[month] for month in grouped.index],
        x=date_ls,
        y=['January', 'February', 'March', 'April', 'May', 'June', 'July',
           'August', 'September', 'October', 'November', 'December'],
        hoverongaps=False,
        hovertemplate='Date: %{x}<br>Month: %{y}<br>Rainfall(mm): %{z}<extra></extra>',
        colorscale='sunset',
        texttemplate="%{z}",
    ))
    fig.update_layout(
        legend_title="Rainfall(mm)",
        yaxis_title="Month",
        xaxis_title="Day",
        template="plotly_dark",
        title_x=0.5,
        height=600,
    )
    return fig


'''
RADIO BUTTON
'''

radio_options = [
    {'label':
     html.Div([
         'Today'],
         style={
         "margin-right": "10px",
         "margin-left": "10px",
         'text-align': 'center',
         'display': 'inline-block'
     }
     ),
        'value': 'today'},

    {'label':
        html.Div([
            'Yesterday'],
            style={
            "margin-right": "10px",
            "margin-left": "10px",
            'text-align': 'center',
            'display': 'inline-block'
        }
        ),
        'value': 'yesterday'},

    {'label':
     html.Div([
         'Custom Date'],
         style={
         "margin-right": "10px",
         "margin-left": "10px",
         'text-align': 'center',
         'display': 'inline-block'
     }
     ),
        'value': 'custom'},
]

today = datetime.today()
last_week_start = datetime.strptime(
    str(today - timedelta(days=7)).split()[0], '%Y-%m-%d')
last_week_end = last_week_start + timedelta(days=6)

# Solar Page
solar_page = html.Div([
    dbc.Row(
        html.Br(),
    ),
    dbc.Row(
        html.P(children=f"Solar Irradiance (W/m\N{SUPERSCRIPT TWO})",
               style={'textAlign': 'Center'}
               ),
    ),
    dbc.Row(
        dcc.RadioItems(
            id='solar-date-radio',
            options=radio_options,
            value='today',
            style={'textAlign': 'Center',
                   'right-margin': '0.5em'},
            inline=True
        ),
    ),
    dbc.Row(
        dcc.DatePickerRange(
            id='solar-date-range',
            min_date_allowed=date(1990, 1, 1),
            max_date_allowed=date(2040, 12, 31),
            display_format='DD/MM/YYYY',
            start_date=last_week_start,
            end_date=last_week_end,
            style={'display': 'none'}

        )
    ),
    dbc.Row(
        html.P(
            id='solar-date-selection',
            style={'textAlign': 'Center',
                   'margin-top': '1%'}
        ),
    ),
    dbc.Row(
        html.Br(),
    ),
    dbc.Row(
        dcc.Loading(
            id='solar-loading',
            children=[dcc.Graph(id='solar-graph')],
            type='graph',
        )

    ),
    dbc.Row(
        html.Br(),
    ),
])

# Barometer Page
barometer_page = html.Div([
    dbc.Row(
        html.Br(),
    ),
    dbc.Row(
        html.P(children=f"Barometric Pressure (hPa)",
               style={'textAlign': 'Center'}
               ),
    ),
    dbc.Row(
        dcc.RadioItems(
            id='barometer-date-radio',
            options=radio_options,
            value='today',
            style={'textAlign': 'Center',
                   'right-margin': '0.5em'},
            inline=True
        ),
    ),
    dbc.Row(
        dcc.DatePickerRange(
            id='barometer-date-range',
            min_date_allowed=date(1990, 1, 1),
            max_date_allowed=date(2040, 12, 31),
            display_format='DD/MM/YYYY',
            start_date=last_week_start,
            end_date=last_week_end,
            style={'display': 'none'}

        )
    ),
    dbc.Row(
        html.P(
            id='barometer-date-selection',
            style={'textAlign': 'Center',
                   'margin-top': '1%'}
        ),
    ),
    dbc.Row(
        html.Br(),
    ),
    dbc.Row(
        dcc.Loading(
            id='baro-loading',
            children=[dcc.Graph(id='barometer-graph')],
            type='graph'
        ),
    ),
    dbc.Row(
        html.Br(),
    ),
])

# Temperature Page
temp_page = html.Div([
    dbc.Row(
        html.Br(),
    ),
    dbc.Row(
        html.P(children=f"Temperature (°C)",
               style={'textAlign': 'Center'}
               ),
    ),
    dbc.Row(
        dcc.RadioItems(
            id='temp-date-radio',
            options=radio_options,
            value='today',
            style={'textAlign': 'Center',
                   'right-margin': '0.5em'},
            inline=True
        ),
    ),
    dbc.Row(
        dcc.DatePickerRange(
            id='temp-date-range',
            min_date_allowed=date(1990, 1, 1),
            max_date_allowed=date(2040, 12, 31),
            display_format='DD/MM/YYYY',
            start_date=last_week_start,
            end_date=last_week_end,
            style={'display': 'none'}

        )
    ),
    dbc.Row(
        html.P(
            id='temp-date-selection',
            style={'textAlign': 'Center',
                   'margin-top': '1%'}
        ),
    ),
    dbc.Row(
        html.Br(),
    ),
    dbc.Row(
        dcc.Loading(
            id='temp-loading',
            children=[dcc.Graph(id='temp-graph')],
            type='graph'
        ),
    ),
    dbc.Row(
        html.Br(),
    ),
])

# Rainfall Page
rain_page = html.Div([
    dbc.Row(
        html.Br(),
    ),
    dbc.Row(
        html.P(children=f"Rainfall (mm)",
               style={'textAlign': 'Center'}
               ),
    ),
    dbc.Row(
        dcc.Loading(
            id='rain-loading',
            children=[dcc.Graph(id='rain-graph', figure=display_rain_graph())],
            type='graph'
        ),
    ),
    dbc.Row(
        html.Br(),
    ),
])

# layout
layout = html.Div([
    dbc.Tabs([
        dbc.Tab(solar_page, label='Solar Irradiance', id='sol-page'),
        dbc.Tab(barometer_page, label='Barometer', id='baro-page'),
        dbc.Tab(temp_page, label='Temperature', id='temp-page'),
        dbc.Tab(rain_page, label='Rainfall', id='rain-page'),

    ])
])


# CallBack ------> SOLAR PAGE

@callback(
    Output('solar-date-range', 'style'),
    Input('solar-date-radio', 'value'),
)
def display_datepicker(radio_value):
    if radio_value == 'custom':
        return {'display': 'block', 'textAlign': 'Center',
                'margin-top': '1%',
                'border': 'none',
                'background-color':
                'transparent',
                'font-size': '10px'
                }
    else:
        return {'display': 'none'}


@callback(
    Output('solar-date-selection', 'children'),
    Input('solar-date-range', 'start_date'),
    Input('solar-date-range', 'end_date'),
    Input('solar-date-radio', 'value'),
)
def display_selection(start_date, end_date, radio_value):
    if radio_value == 'today':
        today = date.today().strftime("%d/%m/%Y")
        display_val = f"Date: {today}"

    elif radio_value == 'yesterday':
        today = date.today()
        yesterday = (today - timedelta(days=1)).strftime("%d/%m/%Y")
        display_val = f"Date: {yesterday}"

    else:
        dt_obj = datetime.fromisoformat(start_date)
        start_date = dt_obj.strftime("%d/%m/%Y")
        dt_obj = datetime.fromisoformat(end_date)
        end_date = dt_obj.strftime("%d/%m/%Y")
        display_val = f"Date: {start_date} - {end_date}"

    return display_val


@callback(
    Output('solar-graph', 'figure'),
    Input('solar-date-range', 'start_date'),
    Input('solar-date-range', 'end_date'),
    Input('solar-date-radio', 'value'),
)
def display_graph(start_date, end_date, radio_value):
    if radio_value == 'today':
        end_time = datetime.now()
        start_time = datetime.combine(date.today(), datetime.min.time())

    elif radio_value == 'yesterday':
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        start_time = datetime(
            yesterday.year, yesterday.month, yesterday.day, 0, 0, 0)
        end_time = datetime(
            now.year, now.month, now.day, 0, 0, 0)
    else:
        start_time = start_date
        end_time = end_date

    custom_query = f"SELECT ts, solar_rad FROM sensor_type_43_15min WHERE ts BETWEEN '{start_time}' AND '{end_time}'ORDER BY ts ASC"

    df = currentdata(custom_query)
    if not df.empty:
        df.columns = ['Time', 'Solar Irradiance']
        fig = px.line(df, x='Time',
                      y="Solar Irradiance", template="plotly_dark")

    else:
        fig = px.line(template="plotly_dark")

    fig.update_layout(title_text='Solar Irradiance (W/m2)', title_x=0.5)
    time.sleep(2)

    return fig


# CallBack ------> BAROMETER PAGE

@callback(
    Output('barometer-date-range', 'style'),
    Input('barometer-date-radio', 'value'),
)
def display_datepicker(radio_value):
    if radio_value == 'custom':
        return {'display': 'block', 'textAlign': 'Center',
                'margin-top': '1%',
                'border': 'none',
                'background-color':
                'transparent',
                'font-size': '10px'
                }
    else:
        return {'display': 'none'}


@callback(
    Output('barometer-date-selection', 'children'),
    Input('barometer-date-range', 'start_date'),
    Input('barometer-date-range', 'end_date'),
    Input('barometer-date-radio', 'value'),
)
def display_selection(start_date, end_date, radio_value):
    if radio_value == 'today':
        today = date.today().strftime("%d/%m/%Y")
        display_val = f"Date: {today}"

    elif radio_value == 'yesterday':
        today = date.today()
        yesterday = (today - timedelta(days=1)).strftime("%d/%m/%Y")
        display_val = f"Date: {yesterday}"

    else:
        dt_obj = datetime.fromisoformat(start_date)
        start_date = dt_obj.strftime("%d/%m/%Y")
        dt_obj = datetime.fromisoformat(end_date)
        end_date = dt_obj.strftime("%d/%m/%Y")
        display_val = f"Date: {start_date} - {end_date}"

    return display_val


@callback(
    Output('barometer-graph', 'figure'),
    Input('barometer-date-range', 'start_date'),
    Input('barometer-date-range', 'end_date'),
    Input('barometer-date-radio', 'value'),
)
def display_graph(start_date, end_date, radio_value):
    if radio_value == 'today':
        end_time = datetime.now()
        start_time = datetime.combine(date.today(), datetime.min.time())

    elif radio_value == 'yesterday':
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        start_time = datetime(
            yesterday.year, yesterday.month, yesterday.day, 0, 0, 0)
        end_time = datetime(
            now.year, now.month, now.day, 0, 0, 0)
    else:
        start_time = start_date
        end_time = end_date

    custom_query = f"SELECT ts, bar_sea_level FROM sensor_type_242_15min WHERE ts BETWEEN '{start_time}' AND '{end_time}' ORDER BY ts ASC"
    df_barometer = currentdata(custom_query)
    if not df_barometer.empty:
        df_barometer.columns = ['Time', 'Bar Sea Level']
        fig = px.line(df_barometer, x='Time',
                      y="Bar Sea Level", template="plotly_dark")
    else:
        fig = px.line(template="plotly_dark")

    fig.update_layout(title_text='Barometeric Pressure (hPa)',
                      title_x=0.5)
    time.sleep(2)
    return fig


# CallBack ------> TEMPERATURE PAGE


@callback(
    Output('temp-date-range', 'style'),
    Input('temp-date-radio', 'value'),
)
def display_datepicker(radio_value):
    if radio_value == 'custom':
        return {'display': 'block', 'textAlign': 'Center',
                'margin-top': '1%',
                'border': 'none',
                'background-color':
                'transparent',
                'font-size': '10px'
                }
    else:
        return {'display': 'none'}


@callback(
    Output('temp-date-selection', 'children'),
    Input('temp-date-range', 'start_date'),
    Input('temp-date-range', 'end_date'),
    Input('temp-date-radio', 'value'),
)
def display_selection(start_date, end_date, radio_value):
    if radio_value == 'today':
        today = date.today().strftime("%d/%m/%Y")
        display_val = f"Date: {today}"

    elif radio_value == 'yesterday':
        today = date.today()
        yesterday = (today - timedelta(days=1)).strftime("%d/%m/%Y")
        display_val = f"Date: {yesterday}"

    else:
        dt_obj = datetime.fromisoformat(start_date)
        start_date = dt_obj.strftime("%d/%m/%Y")
        dt_obj = datetime.fromisoformat(end_date)
        end_date = dt_obj.strftime("%d/%m/%Y")
        display_val = f"Date: {start_date} - {end_date}"

    return display_val


@callback(
    Output('temp-graph', 'figure'),
    Input('temp-date-range', 'start_date'),
    Input('temp-date-range', 'end_date'),
    Input('temp-date-radio', 'value'),
)
def display_graph(start_date, end_date, radio_value):
    if radio_value == 'today':
        end_time = datetime.now()
        start_time = datetime.combine(date.today(), datetime.min.time())

    elif radio_value == 'yesterday':
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        start_time = datetime(
            yesterday.year, yesterday.month, yesterday.day, 0, 0, 0)
        end_time = datetime(
            now.year, now.month, now.day, 0, 0, 0)
    else:
        start_time = start_date
        end_time = end_date

    custom_query_tempout = f"SELECT ts, wind_chill, thw_index, wet_bulb, dew_point, heat_index,temp, thsw_index FROM sensor_type_43_15min WHERE ts BETWEEN '{start_time}' AND '{end_time}' ORDER BY ts ASC"
    df_in_temp = currentdata(custom_query_tempout)

    custom_query_tempin = f"SELECT ts, temp_in, heat_index_in, dew_point_in FROM sensor_type_243_15min WHERE ts BETWEEN '{start_time}' AND '{end_time}' ORDER BY ts ASC"
    df_out_temp = currentdata(custom_query_tempin)

    if not df_out_temp.empty:
        df_out_temp = df_out_temp.drop(columns=['ts'])

    temp = [df_in_temp, df_out_temp]
    df_temp = pd.concat(temp, axis=1)
    if not df_temp.empty:
        df_temp.columns = ['Time', 'Wind chill', 'THW index', 'Wet bulb', 'Dew point', 'Outside Heat Index',
                           'Outside Temperature', 'THSW index', 'Inside Temperature', 'Inside heat Index', 'Inside Dew point']
        fig = px.line(df_temp, x='Time', y=df_temp.columns[1:11])

    else:
        fig = px.line(template="plotly_dark")

    fig.update_layout(title_text='Temperature(°C)',
                      title_x=0.5,
                      template="plotly_dark",
                      legend_title="Legend",
                      yaxis_title="Temperature"

                      )
    time.sleep(2)
    return fig
