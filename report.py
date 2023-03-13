import os
from datetime import date

import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output

import dash_bootstrap_components as dbc

from sdk import Sedmax, SedmaxHeader, ElectricalArchive

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

s = Sedmax("https://demo.sedmax.ru")

try:
    username = os.environ['SEDMAX_USERNAME']
    password = os.environ['SEDMAX_PASSWORD']
except:
    username = 'demo'
    password = 'demo'

s.login(username, password)

el = ElectricalArchive(s)

row = html.Div(
    [
        dbc.Row(dbc.Col(dcc.DatePickerRange(
            id='date-picker-range',
            initial_visible_month=date(2021, 1, 26),
            start_date=date(2021, 1, 20),
            end_date=date(2021, 1, 26)
        ))),
        html.Br(),
        dbc.Row(dcc.Dropdown(
            id='device_pick',
            options=[
                {'label': 'Device 101', 'value': '101'},
                {'label': 'Device 102', 'value': '102'},
                {'label': 'Device 104', 'value': '104'}],
            value='101',
        ), style={'width': '300px'}),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(dash_table.DataTable(
                    id='table',
                    columns=[{'id': 'index', 'name': 'Timestamp'},
                             {'id': 'Value30min', 'name': 'Energy'}, ],
                    page_size=10,
                    style_cell={'height': 40, 'font-size': 16}
                )),
            ]
        ),
    ]
)

app.layout = html.Div(children=[
    SedmaxHeader(title='Report example', logo='sedmax'),
    row,
])


@app.callback(
    Output('table', 'data'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('device_pick', 'value'),
)
def update_table(start_date, end_date, device):
    #channels = [{'device': device, 'channel': "ea_imp"}]
    channels = ['dev-' + device + "_ea_imp"]
    df = el.get_data(channels,
                                     period=["30min"],
                                     begin=start_date,
                                     end=end_date)

    df.rename(columns={df.columns[0]: "Value30min"}, inplace=True)
    data = df.groupby(by=[df.index.date]).sum().reset_index().to_dict('records')

    return data
