import os
import time

import pandas as pd
import numpy as np
import dash
import datetime
from dash import dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

from sdk import SedmaxHeader, Sedmax, ElectricalArchive
# from sankey.prepare_data import load_data, sankey_plot
from sankey.prepare_data_new import load_data, sankey_plot

# Выгрузка хоста из файла конфигурации
with open('host.cfg', 'r') as host:
    x = host.read()
with open('login_data.cfg', 'r') as host:
    t = host.read()
    y = t.split()

# Create a dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# app = dash.Dash(__name__, external_stylesheets=['sankey/assets/bootstrap.min.css'])
app.title = 'Диаграмма Sankey'
s = Sedmax(x)

username = y[0] #os.environ['SEDMAX_USERNAME']
password = y[1] #os.environ['SEDMAX_PASSWORD']
s.login(username, password)
cur_start_time = ''
cur_end_time = ''
el = ElectricalArchive(s)

#background_color = '#5f8dab'
background_color = '#ffffff'


update_button = dbc.Button("Обновить", id="update_", n_clicks=0, className="ant-electro-btn-primary")
day_button = dbc.Button('День', title='Выбрать текущий день', id='day_button', className="ant-electro-btn-primary")
week_button = dbc.Button('Неделя', title='Выбрать текущую неделю', id='week_button', className="ant-electro-btn-primary")
month_button = dbc.Button('Месяц', title='Выбрать текущий месяц', id='month_button', className="ant-electro-btn-primary")

# date_picker = html.Div([
#     html.B(' Электроснабжение офиса. Диаграмма Sankey распределения активной энергии',
#            style={'text-align': 'center', 'color': '#ffffff', 'font-size': 22, 'font-family': 'sans-serif', 'margin-left': '20px'}),
#     html.Div([update_button,
#         dcc.DatePickerRange(
#             id='date-picker-range',
#             initial_visible_month=datetime.datetime.now().date(),
#             start_date=(datetime.datetime.now() - pd.Timedelta(days=2)).date(),
#             end_date=datetime.datetime.now().date(),
#             # month_format='MMMM YYYY',
#             # display_format='DD MMMM YYYY',
#             #month_format='MM/YYYY',
#             )], title='Выберите период отчёта',
#              style={'float': 'right', 'padding': '1px'}),
#     html.Div(
#         [
#             day_button
#         ], style={'float': 'right', 'padding': '1px', 'margin': '0px 0px 0px 0px'}),
#     html.Div(
#         [
#             week_button
#         ], style={'float': 'right', 'padding': '1px', 'margin': '0px 0px 0px 0px'}),
#     html.Div(
#         [
#             month_button
#         ], style={'float': 'right', 'padding': '1px', 'margin': '0px 0px 0px 0px'}),
#     style={'margin-top': '1px', 'margin-bottom': '0px',
#                     'backgroundColor': "grey", 'box-shadow': '0 0 2px 2px rgba(0,0,0,0.3)'}])
#

start_date = (datetime.datetime.now() - pd.Timedelta(days=30)).date()
end_date = datetime.datetime.now().date()


date_picker = html.Div([
    html.B('Диаграмма Sankey распределения активной энергии',
           style={'text-align': 'center', 'color': '#ffffff', 'font-size': 22, 'font-family': 'sans-serif',
                  'margin-left': '20px'}),
    html.Div([month_button, week_button, day_button, update_button,
              dcc.DatePickerRange(
                  id='date-picker-range',
                  # initial_visible_month=(datetime.datetime.now() - pd.Timedelta(days=30)).date(),
                  initial_visible_month=datetime.datetime.now().date(),
                  start_date=start_date,
                  end_date=end_date,
                  # min_date_allowed=(datetime.datetime.now() - pd.Timedelta(days=365)).date(),
                  min_date_allowed=(datetime.datetime.now() - pd.Timedelta(days=730)).date(),
                  max_date_allowed=datetime.datetime.now().date(),
                  # number_of_months_shown=2,
                  # month_format='MMMM YYYY',
                  # display_format='DD MMMM YYYY',
              )], title='Выберите период отчёта',
             style={'float': 'right', 'padding': '1px', 'margin': '0px 0px 0px 0px'}),

    # html.Div(
    #     [
    #         day_button
    #     ], style={'float': 'right', 'padding': '1px', 'margin': '0px 0px 0px 0px'}),
    # html.Div(
    #     [
    #         week_button
    #     ], style={'float': 'right', 'padding': '1px', 'margin': '0px 0px 0px 0px'}),
    # html.Div(
    #     [
    #         month_button
    #     ], style={'float': 'right', 'padding': '1px', 'margin': '0px 0px 0px 0px'}),

], style={'margin': '1px 0px 0px 0px', 'padding': '0px', 'backgroundColor': "grey",
          'box-shadow': '0 0 2px 2px rgba(0,0,0,0.3)'}
)


# Create an app layout
def ubdate_Sankey(data):
    fig = sankey_plot(data)
    body = dbc.Container([
        dbc.Row([dcc.Graph(id='sankey_plot', animate=False, figure=fig,
                           config={'displaylogo': False})], style={'padding': '5px'}),
        html.Br()
        ], fluid=True, style = {'background-color': background_color})
    return body

#
body = dbc.Container([
        dbc.Row([dcc.Graph(id='sankey_plot', animate=False,
                           config={'displaylogo': False})], style={'padding': '5px'}),
        html.Br()
        ], fluid=True, style = {'background-color': background_color})


app.layout = html.Div(children=[
    dcc.Store(id='memory-output'),
    dbc.Row([SedmaxHeader(title='', logo='sedmax')]),
    dbc.Row(date_picker, style = {'background-color': background_color}),
    dcc.Loading(type="circle", children=[html.Div(id='app_body', children=[body],
             style={'height': 'calc(100vh - 98px)', 'overflowY': 'auto',
                 'box-shadow': '0 1px 4px 1px rgba(0,0,0,0.2)', 'margin': '5px', 'border-radius': '2px'})]),
], style={'position': 'fixed', 'width': '100%', 'z-index': '0'})



@app.callback(
    [Output("date-picker-range", "start_date"),
     Output("date-picker-range", "end_date"),
     Output("update_", "n_clicks")],
    [Input("day_button", 'n_clicks'),
     Input("week_button", 'n_clicks'),
     Input("month_button", 'n_clicks')]

)
def on_button_click(n_day, n_week, n_month):    # Фильтрация по горячим кнопкам
    global cur_start_time
    global cur_end_time
    end_date = datetime.datetime.now().date()
    ctx = callback_context.triggered[0]['prop_id']
    if ctx == '.':
        delta = 30
        n = 1
    else:
        delta = 0
        if 'day_button' in ctx:
            delta = 1
            n = n_day
        elif 'week_button' in ctx:
            delta = 6
            n = n_week
        elif 'month_button' in ctx:
            delta = 30
            n = n_month
        # start_date = (datetime.datetime.now() - pd.Timedelta(days=delta)).date()
    start_date = (datetime.datetime.now() - pd.Timedelta(days=delta)).date()
    cur_start_time = start_date
    cur_end_time = end_date
    return start_date, end_date, n

@app.callback([Output(component_id='memory-output', component_property='data'),
               Output(component_id='app_body', component_property='children')],
              [State('date-picker-range', 'start_date'),
               State('date-picker-range', 'end_date'),
              Input('update_', 'n_clicks')])
def update_data(start_date, end_date, n):
    global cur_start_time
    global cur_end_time
    # print(cur_start_time)
    # print(cur_end_time)
    # print(start_date)
    # print(end_date)
    cur_start_time = start_date
    cur_end_time = end_date
    start_date = start_date + ' 00:00:00'
    end_date = end_date + ' 23:59:59'
    data = load_data(s, start_date, end_date)
    body = ubdate_Sankey(data[0])
    return data, body

# @app.callback(Output(component_id='app_body', component_property='children'),
#     Input(component_id='memory-output', component_property='data'))
# def sankey_figure(data):
#     print("Finish")
#     print(data)
#     body = ubdate_Sankey(data)
#     return body


@app.callback(Output(component_id='update_', component_property='className'),
              [Input('date-picker-range', 'start_date'),
               Input('date-picker-range', 'end_date'),
               Input('update_', 'n_clicks')], prevent_initial_call=True)
def update_button_style(start_date, end_date, n):
    global cur_start_time
    global cur_end_time
    print(start_date, cur_start_time, end_date, cur_end_time)
    time.sleep(0.5)
    if cur_start_time != start_date or cur_end_time != end_date:
        return "ant-electro-btn-primary_alarm"
    else:
        print('ok')
        return "ant-electro-btn-primary"



