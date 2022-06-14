import dash
from dash import dcc, html, Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
# from dash.dependencies import Output, Input
import plotly.express as px
import plotly.graph_objects as go
from uw_wx import *
# Units Dictionary
UNITS_DICT = {'Gust': 'kts',
    'Pressure': 'hPa',
    'Radiation': 'W/m^2',
    'Rain': 'in.',
    'Relative Humidity': '%',
    'Temperature': u'\N{DEGREE SIGN}F',
    'Wind Direction': u'\N{DEGREE SIGN}',
    'Wind Speed': 'kts'}

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
        "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
    dbc.themes.BOOTSTRAP
]

# Intialize the Dash object that serves everything
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "UW ATG Rooftop Wx"

app.layout = html.Div(
    children=[
    html.Div([
        html.Div(
            children=[
                html.Img(src='assets\\uw_logo.png',
                    className="center",
                    style={'height':'50%', 'width':'50%'}),
                html.H1(
                    children="UW ATG Rooftop Weather Analysis", className="header-title"
                    )
                ],
                className="header-description",
                ),
        html.Div(
            children=[
                html.Ul(
                    children=[
                        html.Li('Created by Alex Hewett'),
                        html.Li('UW ATG rooftop data provided by University of'
                            ' Washington Atmospheric Sciences Department'),
                        html.Li('Current weather and forecast from Openweather')
                        ],
                    )
                ],
                className='page-description'
                ),
            ],
            className="header"
            ),
        # ATG Obs section
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Parameter", className="menu-title"),
                        # Dropdown for parameter
                        dcc.Dropdown(
                            id="parameter-filter",
                            options=[
                                {"label": parameter, "value": parameter}
                                for parameter in ['Gust', 'Pressure',
                                    'Radiation', 'Rain', 'Relative Humidity',
                                    'Temperature', 'Wind Direction',
                                    'Wind Speed']
                            ],
                            value="Temperature",
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
                        # Date range
                        html.Div(
                            children=[
                                html.Div(
                                    children="Date Range",
                                    className="menu-title"
                                    ),
                                dcc.DatePickerRange(
                                    id="date-range"
                                ),
                            ]
                        ),
                        dbc.Button(
                            "Refresh Data",
                            color='#7e0ead',
                            id='refresh-data',
                            className="button",
                            n_clicks=0
                        )
                    ],
                    className="menu",
                ),
                # Div for plots
                html.Div(
                    children=[
                        html.Div(
                            children=dcc.Graph(
                                id="parameter-chart",
                            ),
                            className="card",
                        ),
                    ],
                    className="wrapper",
                ),
                # Current Wx section
                dbc.Container(
                    id='current-weather',
                    className='current-wx-container'
                ),
                dbc.Container(
                    id='forecast-wx',
                    className='forecast-wx'
                ),
                # dbc.Container(
                #     dbc.Tabs(
                #         [
                #             dbc.Tab(label='Temperature', tab_id='temperature'),
                #             dbc.Tab(label='Pressure', tab_id='pressure'),
                #             dbc.Tab(label='Relative Humidity', tab_id='relative humidity'),
                #             dbc.Tab(label='Wind Speed', tab_id='speed'),
                #             dbc.Tab(label='Wind Direction', tab_id='direction'),
                #             dbc.Tab(label='Pop', tab_id='pop')
                #         ],
                #         id='forecast-plots',
                #         active_tab='Temperature',
                #         className='forecast-plots'
                #     )
                # ),
                # The interval determines the UW data update interval.
                dcc.Interval(
                    id='interval-component',
                    interval=24*36e5, #update daily, 1 day in ms
                    n_intervals=0
                ),
                # The store is the component that holds the updated data
                dcc.Store(id='uw-data', data=[], storage_type='session'),
                dcc.Store(id='forecast-data', data=[], storage_type='session'),
            ]
        )
# Fetch and update the current weather from the Openweather API
@app.callback(
    [
        Output('current-weather', 'children'),
        Output('forecast-wx', 'children'),
        Output('forecast-data', 'data')
    ],
    [
        Input('interval-component', 'n_intervals'),
        Input('refresh-data', 'n_clicks')
    ]
)
def update_wx(num, n_clicks):
    # Make the API call and load the data
    api_key = get_api_key()
    # Build the URL
    current_wx_URL = (
            f"{BASE_WEATHER_API_URL}?q=Seattle"
            f"&units=Imperial&appid={api_key}"
        )
    current_data = get_weather_data(current_wx_URL)
    data = get_current_wx(current_data)
    # Get the forecast data
    fcast_data = get_forecast_data(current_data, imperial=True)
    forecast_wx = get_forecast_dataframe(fcast_data)
    # Make the layout to serve
    current_wx_layout =  [html.H3("Seattle Current Weather", className='current-wx-title'),
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col('Date/Time'),
                        dbc.Col('Sunrise/Sunset'),
                        dbc.Col('Weather'),
                    ],
                className='current-wx-names'
                ),
                dbc.Row(
                    [
                        dbc.Col(f"{data['date']}|{data['time']}"),
                        dbc.Col(f"{data['Sunrise']}/{data['Sunset']}"),
                        dbc.Col(f"{data['wx']}")
                    ],
                    className='current-wx-values'
                )
            ]
        ),
        html.Br(),
        html.Div(
            [
                dbc.Row(
                    [
                    dbc.Col('Temperature'),
                    dbc.Col('Pressure'),
                    dbc.Col('Wind Speed/Direction'),
                    dbc.Col('Relative Humidity')
                    ],
                    className='current-wx-names'
                ),
                dbc.Row(
                    [
                        dbc.Col(f"{data['temperature']}{UNITS_DICT['Temperature']}"),
                        dbc.Col(f"{data['pressure']} hPa"),
                        dbc.Col(f"{data['wind speed']} mph/{data['wind dir']}"
                            f"{UNITS_DICT['Wind Direction']}"),
                        dbc.Col(f"{data['humidity']}%")
                    ],
                    className='current-wx-values'
                )
            ]
        )

        ]
# Build the forecast table layout
    fcast_layout = [
        html.H3("Seattle 5-Day Forecast (3 Hourly)", className='current-wx-title'),
        dbc.Table.from_dataframe(forecast_wx,
            striped=True, bordered=True,
            hover=True)
        ]
    return current_wx_layout, fcast_layout, forecast_wx.to_dict('records')
# # Make and serve the forecast plots
# @app.callback(
#     Output('forecast-plots', 'children'),
#     [
#         Input('forecast-plots', 'active_tab'),
#         Input('forecast-data', 'data')
#     ]
# )
# def update_forecast_plots(active_tab, data):
#     # Load the Store data in to dataframe
#     data = pd.DataFrame(data)
#     # Do some word magic to get the right string for indexing data
#     parameter = [word.capitalize() for word in active_tab.split(' ')]
#     if len(parameter) > 1:
#         parameter = f"{parameter[0]} {parameter[1]}"
#     else:
#         parameter = f"{parameter[0]}"
#     if active_tab and data is not None:
#         # Wind direction, do scatter plot
#         if active_tab == 'direction':
#             figure = px.scatter(data,
#                 x='Date',
#                 y=f'{parameter}',
#                 labels={
#                     f"{parameter}" : f"{parameter} ({UNITS_DICT[parameter]})",
#                     'Date': 'Time'
#                 },
#                 title = f'{parameter}'
#                 )
#             figure.update_layout(
#                 title_font_size=28,
#                 title_x = 0.5,
#                 hovermode= 'x unified'
#             )
#             figure.update_traces(marker_color='#7e0ead')
#             return dcc.Graph(figure=figure)
#     # Probability of precip (pop)
#         elif active_tab == 'pop':
#                 figure = px.bar(data,
#                     x='Date',
#                     y=f'{parameter}',
#                     labels={
#                         f"{parameter}" : f"{parameter})",
#                         'Date': 'Time'
#                     },
#                     title = f'{parameter}'
#                     )
#                 figure.update_layout(
#                     title_font_size=28,
#                     title_x = 0.5,
#                     hovermode= 'x unified'
#                 )
#                 figure.update_traces(marker_color='#7e0ead')
#                 return dcc.Graph(figure=figure)
#         else:
#             figure = px.line(data,
#                 x='Date',
#                 y=f'{parameter}',
#                 labels={
#                     f"{parameter}" : f"{parameter} ({UNITS_DICT[parameter]})",
#                     'Date': 'Time'
#                 },
#                 title = f'{parameter}'
#                 )
#             figure.update_layout(
#                 title_font_size=28,
#                 title_x = 0.5,
#                 hovermode= 'x unified'
#             )
#             figure.update_traces(line_color='#7e0ead')
#
#             return dcc.Graph(figure=figure)
# update the UW ATG rooftop data periodically and automatically.
@app.callback(
    Output('uw-data', 'data'),
    [
        Input('interval-component', 'n_intervals'),
        Input('refresh-data', 'n_clicks')
    ]
)
def update_uw_data(num, n_clicks):
    data = load_uw_data()
    return data.to_dict('records')
# Update the datepicker range when data updates
@app.callback(
    [
        Output('date-range', 'min_date_allowed'),
        Output('date-range', 'max_date_allowed'),
        Output('date-range', 'start_date'),
        Output('date-range', 'end_date')
    ],
    [
        Input('interval-component', 'n_intervals'),
        Input('refresh-data', 'n_clicks')
    ]
)
def update_date_range(num, n_clicks):
    THEN = datetime.now() - timedelta(weeks=1)
    NOW = datetime.now() + timedelta(hours=7)
    return THEN, NOW, THEN, NOW

@app.callback(
    Output("parameter-chart", "figure"),
    [
        Input('uw-data', 'data'),
        Input("parameter-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_charts(data, parameter, start_date, end_date):
    # Get the right data
    # Load the data from the memory store
    data = pd.DataFrame(data)
    # Convert dates back to datetimes
    data['Date'] = pd.to_datetime(data['Date'])
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    mask = (
        (data.Date >= start_date)
        & (data.Date <= end_date)
    )
    filtered_data = data.loc[mask, :]

    if parameter == 'Wind Direction':
        parameter_chart_figure = px.scatter(filtered_data,
            x='Time',
            y=f'{parameter}',
            labels={
                f"{parameter}" : f"{parameter} ({UNITS_DICT[parameter]})",
                'Time': 'Time (UTC)'
            },
            title = f'{parameter}'
            )
        parameter_chart_figure.update_layout(
            title_font_size=28,
            title_x = 0.5,
            hovermode= 'x unified'
        )
        parameter_chart_figure.update_traces(marker_color='#7e0ead')

    elif parameter == 'Radiation':
        parameter_chart_figure = px.area(filtered_data,
            x='Time',
            y=f'{parameter}',
            labels={
                f"{parameter}" : f"{parameter} ({UNITS_DICT[parameter]})",
                'Time': 'Time (UTC)'
            },
            title = f'{parameter}'
             )
        parameter_chart_figure.update_layout(
            title_font_size=28,
            title_x = 0.5,
            hovermode= 'x unified'
        )
        parameter_chart_figure.update_traces(line_color='#7e0ead')

    else:
        parameter_chart_figure = px.line(filtered_data,
            x='Time',
            y=f'{parameter}',
            labels={
                f"{parameter}" : f"{parameter} ({UNITS_DICT[parameter]})",
                'Time': 'Time (UTC)'
            },
            title = f'{parameter}'
             )
        parameter_chart_figure.update_layout(
            title_font_size=28,
            title_x = 0.5,
            hovermode= 'x unified'
        )
        parameter_chart_figure.update_traces(line_color='#7e0ead')

    return parameter_chart_figure

if __name__ == "__main__":
    app.run_server(debug=True)
