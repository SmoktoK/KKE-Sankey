import pandas as pd
import dash
from dash import dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from sdk import SedmaxHeader

from graphs import electro_chart, electro_bar, heat_chart, heat_bar

# Create a dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

data = pd.read_csv('content/data.csv')[-7*24*2:]
data['Date']=pd.to_datetime(data.Date)

#функция для генерации данных на завтрашний день, сейчас не используется
def next_day(df):
    copy_day = df.Date.iloc[-1].date() - pd.to_timedelta(6, unit='D')
    next_day = df[df.Date >= copy_day.strftime("%Y-%m-%d")][:48].copy()
    next_day['Date'] = next_day.Date + pd.to_timedelta(7, unit='D')

    df = pd.concat([df, next_day])
    return df


# Create an app layout
app.layout = dbc.Container([
                                dbc.Row([
                                dbc.Col(SedmaxHeader(title='Контроль диспетчерского графика ТЭЦ')),
                                dbc.Col(dcc.Dropdown(
                                        id='dropdown',
                                        className="nav-link dropdown-toggle",
                                        options=[{'label': f'{x}:00', 'value': x} for x in range(24)],
                                        value=0
                                    ), width=2)
                                ]),

                                html.Br(),

                                dbc.Row([
                                    dbc.Col(dcc.Graph(id='chart', animate=True), width=10),
                                    dbc.Col(dcc.Graph(id='target_electro'), width=2),
                                ], style = {'display':'flex', 'flex-flow': 'row nowrap'}),

                                html.Br(),

                                dbc.Row([
                                    dbc.Col(dcc.Graph(id='heat_chart', animate=True), width=10),
                                    dbc.Col(dcc.Graph(id='target_heat'), width=2),
                                ], style={'display': 'flex', 'flex-flow': 'row nowrap'}),

                                html.Br(),


                                ], fluid=True, style = {'background-color': '#5f8dab'})


@app.callback(
    [Output(component_id='chart', component_property='figure'),
    Output(component_id='target_electro', component_property='figure'),
    Output(component_id='heat_chart', component_property='figure'),
    Output(component_id='target_heat', component_property='figure'),
     ],
    Input(component_id='dropdown', component_property='value')
 )
def chart(time):
    fig1 = electro_chart(data, time)
    fig2 = electro_bar(data, time)
    fig3 = heat_chart(data, time)
    fig4 = heat_bar(data, time)

    return [fig1, fig2, fig3, fig4]

