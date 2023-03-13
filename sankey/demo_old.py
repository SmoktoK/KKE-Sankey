import os
import pandas as pd
import numpy as np
import dash
import datetime
from dash import dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

from sdk import SedmaxHeader, Sedmax, ElectricalArchive
from sankey.prepare_data import load_data, sankey_plot


# Create a dash application
app = dash.Dash(__name__, external_stylesheets=['uptime_report/assets/bootstrap.min.css'])

s = Sedmax('https://demo.sedmax.ru')

username = 'demo' #os.environ['SEDMAX_USERNAME']
password = 'demo' #os.environ['SEDMAX_PASSWORD']
s.login(username, password)

el = ElectricalArchive(s)

#background_color = '#5f8dab'
background_color = '#ffffff'


update_button = dbc.Button("Обновить", id="update_", n_clicks=0, className="ant-electro-btn-primary",
            style={'margin-right': '3px', 'font-size': '14px'}
           )

date_picker = html.Div([
    html.B(' Электроснабжение офиса. Активная электроэнергия',
           style={'textAlign': 'center', 'color': '#ffffff','font-size': 22, 'margin-left': '1%'}),
    html.Div([
    update_button,
    dcc.DatePickerRange(
            id='date-picker-range',
            initial_visible_month=datetime.datetime.now().date(),
            start_date=(datetime.datetime.now() - pd.Timedelta(days=0)).date(),
            end_date=datetime.datetime.now().date(),
            #month_format='MM/YYYY',
            )], style={'float': 'right', 'padding': '1px'})
            ],
            style={'margin-top': '5px', 'margin-bottom': '5px',
                    'backgroundColor': "grey", 'box-shadow': '2px 2px 2px rgba(0,0,0,0.3)'}
        )

# Create an app layout
body = dbc.Container([
    dbc.Row([dcc.Graph(id='sankey_plot', animate=False,
                       config={'displaylogo': False})], style={'padding': '5px'}),
    html.Br()
    ], fluid=True, style = {'background-color': background_color})


app.layout = html.Div(children=[
    dcc.Store(id='memory-output'),
    SedmaxHeader(title='Sankey Diagram', logo = 'sedmax'),
    dbc.Row(date_picker, style = {'background-color': background_color}),
    html.Div(id='app_body', children=[body]),
])


@app.callback([Output(component_id='memory-output', component_property='data')],
              [Input('date-picker-range', 'start_date'),
               Input('date-picker-range', 'end_date'),
              Input('update_', 'n_clicks')]
              )
def update_data(start_date, end_date, n):
    data = load_data(el, start_date, end_date)
    return data

@app.callback(
    [Output(component_id='sankey_plot', component_property='figure')],
    [Input(component_id='memory-output', component_property='data')]
 )
def sankey_figure(data):

    fig = sankey_plot(data)
    return [fig]
