import os
import pandas as pd
import dash
import datetime
from dash import dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

from sdk import SedmaxHeader, Sedmax, EnergyArchive, ElectricalArchive, RTDArchive
from DG_UDG.graphs import dg_graph, temp_graph, dg_graph_mini, temp_graph_mini

config_plots = dict(locale='ru')

#assets_path = ''

# Create a dash application
app = dash.Dash(__name__, external_stylesheets=['DG_UDG/assets/bootstrap.min.css']) #, assets_folder=assets_path

#app.scripts.append_script({"external_url": "https://cdn.plot.ly/plotly-locale-ru.js"})

s = Sedmax('https://sdk.sedmax.ru')

username = os.environ['SEDMAX_USERNAME']
password = os.environ['SEDMAX_PASSWORD']
s.login(username, password)

en = EnergyArchive(s)
el = ElectricalArchive(s)
r = RTDArchive(s)

temp_table = pd.read_csv('DG_UDG/content/temp_table.csv')


def load_data_new(days, minutes):


    time_now = datetime.datetime.now()
    week_ago = time_now - pd.Timedelta(days=days)
    rtd_end = datetime.datetime.combine(time_now.date(), datetime.time(23, 59, 59)).strftime("%Y-%m-%d %H:%M:%S")
    rtd_start = datetime.datetime.combine(week_ago.date(), datetime.time(00, 00, 00)).strftime("%Y-%m-%d %H:%M:%S")

    #electro
    df1 = el.get_data(['dev-4_ea_exp', 'dev-3_ea_exp', 'dev-2_ea_exp'], ['30min'], week_ago.strftime("%Y-%m-%d"),
                      time_now.strftime("%Y-%m-%d"), multiplier=1e-3)
    df1 = df1.rename(columns={'dev-4_ea_exp': "udg", 'dev-3_ea_exp': "dg", 'dev-2_ea_exp': "ea"})

    # rtd archive
    df2 = r.get_data(["par-1001", "par-1002", "par-1003"], 10, rtd_start, rtd_end)
    df2 = df2.rename(columns={'par-1001-value': 'power', 'par-1002-value': 'fact_forward', 'par-1003-value': 'fact_backward'})
    df2['ambient'] = 3
    df2 = df2.reset_index().merge(temp_table, on='ambient').set_index('dt')

    df2['dt_rounded30'] = df2.index.ceil('30min')
    df2 = df2.reset_index().merge(df1[['dg', 'udg']], left_on='dt_rounded30', right_index=True, how='left').set_index('dt')
    df2['error_power'] = 100 * (df2['power'] - df2['udg']) / df2['udg']

    df2['dt_rounded60'] = df2.index.ceil('60min')

    df2['error_forward'] = 100 * (df2['fact_forward'] - df2['forward']) / df2['forward']
    df2['error_backward'] = 100 * (df2['fact_backward'] - df2['backward']) / df2['backward']

    # rtd for last hour
    past_hour = time_now - pd.Timedelta(minutes=minutes)
    df3 = r.get_data(["par-1001", "par-1002", "par-1003"], 10, past_hour.strftime("%Y-%m-%d %H:%M:%S"), time_now.strftime("%Y-%m-%d %H:%M:%S"))
    df3 = df3.rename(columns={'par-1001-value': 'power', 'par-1002-value': 'fact_forward', 'par-1003-value': 'fact_backward'})

    df3['dt_rounded30'] = df3.index.ceil('30min')
    df3 = df3.reset_index().merge(df1[['dg', 'udg']], left_on='dt_rounded30', right_index=True, how='left').set_index('dt')
    df3['error_power'] = 100 * (df3['power'] - df3['udg']) / df3['udg']

    df3['dt_rounded60'] = df3.index.ceil('60min')
    #df3 = df3.reset_index().merge(df2[['forward', 'backward', 'dt_rounded60']].drop_duplicates(), on='dt_rounded60', how='left').set_index('dt')
    df3['ambient'] = 3
    df3 = df3.reset_index().merge(temp_table, on='ambient').set_index('dt')

    df3['error_forward'] = 100 * (df3['fact_forward'] - df3['forward']) / df3['forward']
    df3['error_backward'] = 100 * (df3['fact_backward'] - df3['backward']) / df3['backward']

    df3 = df3.dropna(subset=['fact_forward', 'fact_backward', 'power'])

    return [df1.to_json(), df2.to_json(), df3.to_json()]




#меню настроек
offcanvas = html.Div(
    [
        dbc.Button("Настройки", id="open-offcanvas", n_clicks=0, className="btn btn-secondary",
                  # style={'backgroundColor': 'rgba(50,50,50,0.9)'}
                   ),
        dbc.Offcanvas(
            [
            html.P("Глубина диспетчерских графиков, дней"),
            dcc.Slider(id='slider_1', min=1, max=7, step=1,
                       marks=dict([(x, str(x)) for x in range(1,8)]), value=5),

            html.P("Глубина оперативных графиков, минут"),
            dcc.Slider(id='slider_2', min=1, max=30, step=1,
                       marks={1:'1', 5:'5', 10:'10', 15:'15', 20:'20', 25:'25', 30:'30'}, value=15)
            ],

            id="offcanvas", title="Настройки", is_open=False),
    ]
)

# Create an app layout
body = dbc.Container([dcc.Store(id='memory-output'),

                            dcc.Interval(
                                        id='interval-component',
                                        interval=5*1000, # 5 seconds in milliseconds
                                        n_intervals=0),


                                html.Br(),

                                dbc.Row([
                                    dbc.Col(dcc.Graph(id='chart', config={'locale': 'ru'}, animate=True), width=9),
                                    dbc.Col(dcc.Graph(id='chart_mini', config={'displayModeBar': False, 'locale': 'ru'}), width=3),
                                ], style = {'display':'flex', 'flex-flow': 'row nowrap'}),

                                html.Br(),

                                dbc.Row([
                                    dbc.Col(dcc.Graph(id='heat_chart', config={'locale': 'ru'}, animate=True), width=9),
                                    dbc.Col(dcc.Graph(id='heat_mini', config={'displayModeBar': False, 'locale': 'ru'}), width=3),
                                ], style={'display': 'flex', 'flex-flow': 'row nowrap'}),

                                html.Br(),
                                offcanvas,
                                html.Br(),
                                ], fluid=True, style = {'background-color': '#5f8dab'})


app.layout = html.Div(children=[
    SedmaxHeader(title='Контроль диспетчерского графика ТЭЦ'),
    body,
])


@app.callback(Output(component_id='memory-output', component_property='data'),
              [Input(component_id='interval-component', component_property='n_intervals'),
               Input(component_id='slider_1', component_property='value'),
               Input(component_id='slider_2', component_property='value')]

              )
def update_global_var(n, days, minutes):
   return load_data_new(days, minutes)

@app.callback(
    [Output(component_id='chart', component_property='figure'),
    Output(component_id='heat_chart', component_property='figure'),
     Output(component_id='chart_mini', component_property='figure'),
     Output(component_id='heat_mini', component_property='figure')
     ],
    [Input(component_id='memory-output', component_property='data'),
    Input(component_id='interval-component', component_property='n_intervals')]
 )
def chart(data, n):
    el_archive = pd.read_json(data[0])
    rtd_archive = pd.read_json(data[1])
    rtd = pd.read_json(data[2])

    fig1 = dg_graph([el_archive, rtd_archive], n)
    fig2 = temp_graph(rtd_archive, n)
    fig3 = dg_graph_mini(rtd)
    fig4 = temp_graph_mini(rtd)

    return [fig1, fig2, fig3, fig4]

@app.callback(
    Output("offcanvas", "is_open"),
    Input("open-offcanvas", "n_clicks"),
    [State("offcanvas", "is_open")],
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open