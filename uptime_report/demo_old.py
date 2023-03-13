import os
import pandas as pd
import numpy as np
import dash
import datetime
from dash import dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

from sdk import SedmaxHeader, Sedmax, ElectricalArchive, EventJournal
from uptime_report.graphs import out_time_scatter, out_table


# Create a dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

s = Sedmax('https://demo.sedmax.ru')

username = 'demo' #os.environ['SEDMAX_USERNAME']
password = 'demo' #os.environ['SEDMAX_PASSWORD']
s.login(username, password)

el = ElectricalArchive(s)
j = EventJournal(s)

background_color = '#5f8dab'

def report_by_device(df, start, end):
    # full period time
    total_time = (end - start).total_seconds()
    # Outage time by device, seconds
    outage_time = np.round(df.groupby('common-device')['pq-duration'].sum(), 3)
    # Uptime by device, seconds
    uptime = total_time - outage_time

    data = uptime.to_frame().rename(columns={'pq-duration': 'uptime'})
    data['uptime_percent'] = np.round((100 * uptime / total_time), 2)
    data['outage_time'] = outage_time
    data['outage_percent'] = np.round((100 * outage_time / total_time), 2)
    data['events'] = df.groupby('common-device')['common-number'].count()

    data['outage_max'] = df.groupby('common-device')['pq-duration'].max()
    data['outage_min'] = df.groupby('common-device')['pq-duration'].min()

    # MTBF and MTTR for report
    data['MTBF'] = df.groupby('common-device')['TBF'].mean().dt.round(freq='T').astype('str') # minute
    data['MTTR'] = np.round((df.groupby('common-device')['pq-duration'].mean()), 2)

    return data


def report(df, start, end):
    total_time = (end - start).total_seconds()

    data = pd.DataFrame.from_dict(
        {'Период': start.strftime("%d %b %Y") + " - " + end.strftime("%d %b %Y"),
         'Количество секунд': f'{int(total_time)}, сек',
         'Outage': f'{df["pq-duration"].sum().round(3)}, сек',
         'Uptime': f'{(total_time - df["pq-duration"].sum()).round(3)}, сек',
         'Количество событий': df["common-number"].count(),
         'Количество устройств': len(df["common-device"].unique()),
         'MTBF Total': df["TBF"].mean().round(freq="s").__str__(),
         'MTTR Total': f'{pd.to_timedelta(df["pq-duration"].mean(), unit="s").round(freq="s").__str__()}'
         },
        orient='Index')
    data = data.rename(columns={0:'value'})

    return data

def uptime_table(df, start, end):
    data = df.groupby(['common-device', 'date']).count().reset_index()
    days = pd.date_range(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), freq='D')

    for device in data['common-device'].unique():
        data = data.merge(pd.DataFrame({'date': days.date, 'common-device': device}), on=['date', 'common-device'], how='outer')

    data = data.pivot(index='common-device', columns='date')['common-number']
    data = data.fillna(0).astype(int)

    return data


def load_data(start_date, end_date):

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    start_date = datetime.datetime.combine(start_date, datetime.time(00, 00, 00))
    end_date = datetime.datetime.combine(end_date, datetime.time(23, 59, 59))

    end = end_date.strftime("%Y-%m-%d %H:%M:%S")
    start = start_date.strftime("%Y-%m-%d %H:%M:%S")

    df = j.get_data(88, start, end, filters={'common-message': ['провал']})
        #if there is no data for selected period the dataframe is empty
    if df.empty:
        return df.to_json()

    df = df.sort_index(ascending=True)
    # time between eventa by device
    df['TBF'] = df.reset_index().groupby('common-device')['dt'].diff().values
    # casting str to float

    df[['pq-duration', 'pq-magnitude', 'pq-reference']] = df[['pq-duration',
                                        'pq-magnitude', 'pq-reference']].replace('', 0).astype('float')


    # event_end
    df['end'] = df.index + pd.to_timedelta(df['pq-duration'], unit='s')
    # event_date
    df['date'] = df.index.date

    device_report = report_by_device(df, start_date, end_date)
    common_report = report(df, start_date, end_date)
    table = uptime_table(df, start_date, end_date)

    return [df.reset_index().to_json(), device_report.to_json(), common_report.to_json(), table.to_json()]


def update_table(df):
    df = df.reset_index()
    data = df.to_dict('records')
    columns = [{"name": i, "id": i, } for i in (df.columns)]
    return dash_table.DataTable(data=data, columns=columns,
                style_cell={'font-size': 12, 'overflow': 'hidden', 'backgroundColor': "rgba(50,50,50,0.2)"},
                style_data_conditional=[
                                    {
                                        "if": {"state": "selected"},  # 'active' | 'selected'
                                        "backgroundColor": "rgba(0, 116, 217, 0.3)",
                                        "border": "1px solid blue",
                                    },
                                ]
                                )


common_table = html.Div(dash_table.DataTable(
                    id='common_table',
                    columns=[{'id': 'index', 'name': 'Характеристка'},
                             {'id': 'value', 'name': 'Значение'}],
                    style_cell={'font-size': 13, 'overflow': 'hidden', 'backgroundColor': "rgba(50,50,50,0.2)"},
                ), style={'padding': '5px'})


date_picker = html.Div(dcc.DatePickerRange(
            id='date-picker-range',
            initial_visible_month=datetime.datetime.now().date(),
            start_date=(datetime.datetime.now() - pd.Timedelta(days=30)).date(),
            end_date=datetime.datetime.now().date(),
            #month_format='MM/YYYY',
            ), style={'margin-top': '5px', 'margin-bottom': '5px'})

# Create an app layout
body = dbc.Container([
                                dbc.Row([
                                    dbc.Col(html.Div(id="common_table"), width=3,
                                            style={'display': 'inline-table', 'padding': '5px', 'backgroundColor': "rgba(50,50,50,0.2)"}),
                                    dbc.Col(html.Div(id="device_table"), width=9,
                                            style={'display': 'inline-table', 'padding': '5px', 'backgroundColor': "rgba(50,50,50,0.2)"}),

                                ], style = {'display':'flex', 'flex-flow': 'row nowrap'}),

                                html.Br(),

                                dbc.Row([
                                      dbc.Col(dcc.Graph(id='out_table', animate=False,
                                                        config= {'displayModeBar': False, 'locale': 'ru', 'staticPlot': True}), width=12),
                                  ], style={'padding': '5px', 'display': 'flex', 'flex-flow': 'row nowrap'}),

                                #html.Br(),

                                dbc.Row([dcc.Graph(id='out_time_scatter', animate=False,
                                                   config= {'displaylogo': False,  'locale': 'ru'})], style={'padding': '5px'}),
                                #html.Br(),

                                #offcanvas,
                                html.Br(),
                                ], fluid=True, style = {'background-color': background_color})


no_data = dbc.Container([
    dbc.Row(html.B('Отсутствуют данные для отображения'),
                                style = {'height':'200px', 'text-align': 'center', 'align-items': 'center'})],
    fluid=True, style = {'background-color': background_color})


app.layout = html.Div(children=[
    dcc.Store(id='memory-output'),
    SedmaxHeader(title='UpTime Report'),
    dbc.Row(date_picker, style = {'background-color': background_color}),
    html.Div(id='app_body', children=[body]),
])


@app.callback([Output(component_id='memory-output', component_property='data'),
               Output(component_id='app_body', component_property='children')],
              [Input('date-picker-range', 'start_date'),
               Input('date-picker-range', 'end_date')]
              )
def update_global_var(start_date, end_date):
    df = load_data(start_date, end_date)
    if type(df) is list:
        app_body = body
    else:
        app_body = no_data

    return [df, app_body]

@app.callback(
    [Output(component_id='common_table', component_property='children'),
    Output(component_id='device_table', component_property='children'),
    Output(component_id='out_table', component_property='figure'),
    Output(component_id='out_time_scatter', component_property='figure'),
    ],
    [Input(component_id='memory-output', component_property='data'),
 ]
 )
def show_report(data):

    if type(data) is list:
        #графики
        df = pd.read_json(data[0]).set_index('dt')
        df.index = pd.to_datetime(df.index, unit='ms')
        table = pd.read_json(data[3])

        scatter = out_time_scatter(df)
        heatmap = out_table(table)

        #таблицы
        device_report = update_table(pd.read_json(data[1]))
        common_report = update_table(pd.read_json(data[2]))

        return [common_report, device_report, heatmap, scatter]
    else:
        pass
