import numpy as np

import plotly.graph_objects as go
from plotly.subplots import make_subplots

colors = {
    'grid': "rgba(255,255,255,0.2)",
    'graph_font': "#f0f8ff",
    'plot_area': "rgba(50,50,50,0.9)",
    'plot_background': "rgba(50,50,50,0.2)",
}

def electro_chart(data, time):
    error = 100 * (data.gen_power - data.DG) / data.DG
    MIN = data.gen_power.min() * 0.9
    MAX = data.gen_power.max() * 1.1

    t = data.Date.iloc[-1].replace(hour=time, minute=00)
    gen_power_view = data[data.Date <= t].gen_power
    error = error[gen_power_view.index]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.18, row_width=[0.2, 0.3])
    fig.add_trace(go.Scatter(x=data.Date, y=gen_power_view, mode='lines+markers', fill='tozeroy', fillcolor='rgba(102,178,255,0.7)',
                             line=dict(color='steelblue', width=2), name='Мощность'),
                  row=1, col=1)  # fill down to xaxis
    fig.add_trace(go.Scatter(x=data.Date, y=data.DG, fill='tozeroy', fillcolor='rgba(241,241,241,0.4)',
                             line=dict(color='grey', width=2, dash='dash'), name='ДГ'), row=1,
                  col=1)  # fill to trace0 y  #fill='tonexty'
    fig.add_trace(
        go.Scatter(x=data.Date, y=error, mode='lines+markers', fill='tozeroy', fillcolor='rgba(255,255,204,0.35)',
                   line=dict(color='lightsalmon', width=2), name='Отклонение, %'), row=2, col=1)

    fig.update_layout(height=450,
                      xaxis=dict(gridcolor=colors['grid'], range=[data.Date.iloc[-48], data.Date.iloc[-1]]),
                      xaxis2=dict(gridcolor=colors['grid']),
                      yaxis=dict(gridcolor=colors['grid'], range=[MIN, MAX]),
                      yaxis2=dict(gridcolor=colors['grid'], tickvals=[-4, -2, 0, 2, 4]),
                      font_color=colors['graph_font'],
                      title_text='Электрическая мощность, МВт',
                      xaxis_rangeslider_visible=True,
                      xaxis_rangeslider_thickness=0.1,
                      hovermode="x unified",
                      plot_bgcolor=colors['plot_area'],
                      paper_bgcolor=colors['plot_background'],
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                      margin=dict(l=20, r=20, b=30, t=80, pad=1),
                      )

    fig['layout']['xaxis'].update(
        rangeselector=dict(
            bgcolor=colors['plot_area'],
            xanchor="left",  # x=1,
            yanchor="bottom",  # y=1.02,
            buttons=list([
                dict(count=1, label="24 часа", step="day", stepmode="backward"),
                dict(count=3, label="72 часа", step="day", stepmode="todate"),
                dict(count=7, label="Неделя", step="day", stepmode="todate"),
                #dict(count=7, label="Неделя", step="day", stepmode="backward"),
                #dict(count=1, label="Месяц", step="month", stepmode="todate"),
                # dict(label="Все", step="all")
            ])
        )
    )
    return fig


def electro_bar(data, time):
    # current power
    t = data.Date.iloc[-1].replace(hour=time, minute=00)
    power = data[data.Date <= t].gen_power.iloc[-1]
    plan = data[data.Date <= t].DG.iloc[-1]
    percent = f'{np.round(100 * power / plan, 2)}%'

    # day power
    day = data.Date.iloc[-1].date().strftime('%Y-%m-%d')
    day_power = (data[(data.Date >= day) & (data.Date <= t)].gen_power * 0.5).sum()
    day_plan = (data[(data.Date >= day) & (data.Date <= t)].DG * 0.5).sum()
    percent_day = f'{np.round(100 * day_power / day_plan, 2)}%'

    def get_color(power, plan):
        if power < plan:
            color = abs(power / plan) * 255
            color = f'rgba(255,{color},0,0.4)'
        else:
            color = abs(power / plan) * 128
            color = f'rgba({color},255,0,0.4)'
        return color

    fig = make_subplots(rows=2, cols=1, shared_xaxes=False, vertical_spacing=0.25,
                        subplot_titles=("Значение мощности <br>на текущий период, <br>МВт",
                                        "Производство ЭЭ <br>на текущие сутки, <br>МВтч"))
    fig.add_trace(
        go.Bar(x=['Мощность'], y=[plan], marker_color='rgba(211,211,211,0.9)', name='Плановая'),
        row=1, col=1)
    fig.add_trace(
        go.Bar(x=['Мощность'], y=[power], marker_color=get_color(power, plan), name='Текущая', width=[0.65],
               text=[percent], textposition='auto'),
        row=1, col=1)

    fig.add_trace(
        go.Bar(x=['Выработка'], y=[day_plan], marker_color='rgba(211,211,211,0.9)', name='Плановая'),
        row=2, col=1)
    fig.add_trace(
        go.Bar(x=['Выработка'], y=[day_power], marker_color=get_color(day_power, day_plan), name='Текущая',
               width=[0.65],
               text=[percent_day], textposition='auto'),
        row=2, col=1)

    fig.update_layout(yaxis=dict(gridcolor=colors['grid']),
                      yaxis2=dict(gridcolor=colors['grid']),
                      font_color=colors['graph_font'],
                      barmode='overlay',
                      height=450,
                      paper_bgcolor=colors['plot_background'],
                      plot_bgcolor=colors['plot_area'],
                      margin=dict(l=20, r=20, b=30, t=80, pad=1),
                      showlegend=False,
                      )

    return fig


#### HEAT POWER#####

def heat_chart(data, time):
    error = 100 * (data.gkal - data.gkal_plan) / data.gkal_plan
    MIN = data.gkal.min() * 0.9
    MAX = data.gkal.max() * 1.1

    t = data.Date.iloc[-1].replace(hour=time, minute=00)
    heat_power_view = data[data.Date <= t].gkal
    error = error[heat_power_view.index]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.18, row_width=[0.2, 0.3])
    fig.add_trace(go.Scatter(x=data.Date, y=heat_power_view, mode='lines+markers', fill='tozeroy',
                             fillcolor='rgba(0,255,127,0.7)', line=dict(color='#40826d', width=2), name='ТЭ факт'),
                  row=1, col=1)  # fill down to xaxis
    fig.add_trace(go.Scatter(x=data.Date, y=data.gkal_plan, fill='tozeroy', fillcolor='rgba(241,241,241,0.4)',
                             line=dict(color='grey', width=2, dash='dash'), name='ТЭ план'), row=1,
                  col=1)  # fill to trace0 y  #fill='tonexty'
    fig.add_trace(
        go.Scatter(x=data.Date, y=error, mode='lines+markers', fill='tozeroy', fillcolor='rgba(255,255,204,0.35)',
                   line=dict(color='lightsalmon', width=2), name='Отклонение, %'), row=2, col=1)

    fig.update_layout(height=450,
                      xaxis=dict(gridcolor=colors['grid'], range=[data.Date.iloc[-48], data.Date.iloc[-1]]),
                      xaxis2=dict(gridcolor=colors['grid']),
                      yaxis=dict(gridcolor=colors['grid'], range=[MIN, MAX]),
                      yaxis2=dict(gridcolor=colors['grid']),  # , tickvals = [-4,-2,0,2,4]
                      font_color=colors['graph_font'],
                      title_text='Тепловая энергия, Гкал',
                      xaxis_rangeslider_visible=True,
                      xaxis_rangeslider_thickness=0.1,
                      hovermode="x unified",
                      plot_bgcolor=colors['plot_area'],
                      paper_bgcolor=colors['plot_background'],
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                      margin=dict(l=20, r=20, b=30, t=80, pad=1),
                      )

    fig['layout']['xaxis'].update(
        rangeselector=dict(
            bgcolor=colors['plot_area'],
            xanchor="left",
            yanchor="bottom",
            buttons=list([
                dict(count=1, label="24 часа", step="day", stepmode="backward"),
                dict(count=3, label="72 часа", step="day", stepmode="todate"),
                dict(count=7, label="Неделя", step="day", stepmode="todate"),
                # dict(label="Все", step="all")
            ])
        )
    )
    return fig


def heat_bar(data, time):
    # current power
    t = data.Date.iloc[-1].replace(hour=time, minute=00)
    power = data[data.Date <= t].gkal.iloc[-1]
    plan = data[data.Date <= t].gkal_plan.iloc[-1]
    percent = f'{np.round(100 * power / plan, 2)}%'

    # temperature
    TEMP = data[data.Date <= t].temp.iloc[-1]

    def get_color(power, plan):
        if power < plan:
            color = abs(power / plan) * 255
            color = f'rgba(255,{color},0,0.4)'
        else:
            color = abs(power / plan) * 128
            color = f'rgba({color},255,0,0.4)'
        return color

    fig = make_subplots(rows=2, cols=1, shared_xaxes=False, vertical_spacing=0.25,
                        subplot_titles=("Значение ТЭ <br>на текущий период, <br>Гкал",
                                        "Температура <br>теплоносителя"))
    fig.add_trace(
        go.Bar(x=['ТЭ'], y=[plan], marker_color='rgba(211,211,211,0.9)', name='Плановая'),
        row=1, col=1)
    fig.add_trace(
        go.Bar(x=['ТЭ'], y=[power], marker_color=get_color(power, plan), name='Текущая', width=[0.65],
               text=[percent], textposition='auto'),
        row=1, col=1)

    fig.add_trace(
        go.Bar(x=['Температура'], y=[TEMP], marker_color=f'rgba(255,{int(255 - TEMP * 1.5)},51,0.9)',
               name='Температура',
               text=[f'{int(TEMP)}°C'], textposition='auto'),
        row=2, col=1)

    fig.update_layout(yaxis=dict(gridcolor=colors['grid']),
                      yaxis2=dict(gridcolor=colors['grid'], range=[0, 120]),
                      font_color=colors['graph_font'],
                      barmode='overlay',
                      height=450,
                      paper_bgcolor=colors['plot_background'],
                      plot_bgcolor=colors['plot_area'],
                      margin=dict(l=20, r=20, b=30, t=80, pad=1),
                      showlegend=False,
                      )

    return fig


def dg_graph(data, n):
    rtd_data = data[1]
    data = data[0]

    MIN = data.dg.min() * 0.9
    MAX = data.dg.max() * 1.1

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.18, row_width=[0.2, 0.3])
    fig.add_trace(go.Scatter(x=rtd_data.index, y=rtd_data.power, mode='lines', #fill='tozeroy', fillcolor='rgba(102,178,255,0.7)',
                             line=dict(color='#0a84ff', width=2), name='Мощность'),
                  row=1, col=1)  # fill down to xaxis
    fig.add_trace(go.Scatter(x=data.index, y=data.dg, mode='lines+markers', #fill='tozeroy', fillcolor='rgba(231,231,231,0.2)',
                             line=dict(color='grey', width=2, dash='dash'), name='ДГ'),
                  row=1, col=1)  # fill to trace0 y  #fill='tonexty'
    fig.add_trace(go.Scatter(x=data.index, y=data.udg, mode='lines+markers', #fill='tozeroy', fillcolor='rgba(241,241,241,0.3)',
                             line=dict(color='lightgrey', width=2, dash='dash'), name='УДГ'),
                  row=1, col=1)  # fill to trace0 y  #fill='tonexty'

    fig.add_trace(
        go.Scatter(x=rtd_data.index, y=rtd_data.error_power, mode='lines', fill='tozeroy', fillcolor='rgba(255,255,204,0.35)',
                   line=dict(color='lightsalmon', width=2), name='Отклонение, %'), row=2, col=1)

    fig.update_layout(height=450,
                      xaxis=dict(gridcolor=colors['grid']),
                      xaxis2=dict(gridcolor=colors['grid']),
                      yaxis=dict(gridcolor=colors['grid'], range=[MIN, MAX]),
                      yaxis2=dict(gridcolor=colors['grid'],), #tickvals=[-4, -2, 0, 2, 4]),
                      font_color=colors['graph_font'],
                      title={'text': 'График электрической мощности, МВт', 'x': 0.5, 'xanchor': 'center'},
                      xaxis_rangeslider_visible=True,
                      xaxis_rangeslider_thickness=0.1,
                      hovermode="x unified",
                      plot_bgcolor=colors['plot_area'],
                      paper_bgcolor=colors['plot_background'],
                      legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="right", x=1),
                      margin=dict(l=20, r=20, b=30, t=30, pad=1),
                      )

    #default position of xaxis_rangeslider on page load
    if n<1:
        fig['layout']['xaxis'].update(range=[data.index[-48], data.index[-1]])

    fig['layout']['xaxis'].update(
        rangeselector=dict(
            bgcolor=colors['plot_area'],
            xanchor="left",  # x=1,
            yanchor="bottom",  # y=1.02,
            buttons=list([
                dict(count=1, label="24 часа", step="day", stepmode="backward"),
                dict(count=3, label="72 часа", step="day", stepmode="todate"),
                dict(count=7, label="Неделя", step="day", stepmode="todate")
            ])
        )
    )
    return fig

def temp_graph(data, n):

    rtd_data = data

    MIN = data.backward.min() - 15
    MAX = data.forward.max() + 15

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.18, row_width=[0.2, 0.3])
    fig.add_trace(go.Scatter(x=data.index, y=data.fact_forward, mode='lines', #fill='tozeroy', fillcolor='rgba(102,178,255,0.7)',
                             line=dict(color='#ff0039', width=2), name='t°C в подающем'),
                  row=1, col=1)  # fill down to xaxis

    fig.add_trace(go.Scatter(x=data.index, y=data.fact_backward, mode='lines', #fill='tozeroy', fillcolor='rgba(102,178,255,0.7)',
                             line=dict(color='#ff9400', width=2), name='t°C в обратном'),
                  row=1, col=1)  # fill down to xaxis

    fig.add_trace(go.Scatter(x=data.index, y=data.forward, mode='lines', #fill='tozeroy', fillcolor='rgba(102,178,255,0.7)',
                             line=dict(color='rgba(255,0,57,0.7)', width=1, dash='dash'), name='Целевая t°C в подающем'),
                  row=1, col=1)  # fill down to xaxis

    fig.add_trace(go.Scatter(x=data.index, y=data.backward, mode='lines', #fill='tozeroy', fillcolor='rgba(102,178,255,0.7)',
                             line=dict(color='rgba(255,148,0,0.7)', width=1,  dash='dash'), name='Целевая t°C в обратном'),
                  row=1, col=1)  # fill down to xaxis

    fig.add_trace(
        go.Scatter(x=data.index, y=data.error_forward, mode='lines', fill='tozeroy', fillcolor='rgba(255,255,204,0.2)',
                   line=dict(color='lightsalmon', width=2), name='Откл. в подающем, %'), row=2, col=1)
    fig.add_trace(
        go.Scatter(x=data.index, y=data.error_backward, mode='lines', fill='tozeroy', fillcolor='rgba(255,255,204,0.2)',
                   line=dict(color='DeepSkyBlue', width=2), name='Откл. в обратном, %'), row=2, col=1)

    fig.update_layout(height=450,
                      xaxis=dict(gridcolor=colors['grid']),
                      xaxis2=dict(gridcolor=colors['grid']),
                      yaxis=dict(gridcolor=colors['grid'], range=[MIN, MAX]),
                      yaxis2=dict(gridcolor=colors['grid'],), #tickvals=[-4, -2, 0, 2, 4]),
                      font_color=colors['graph_font'],
                      title={'text': 'Температурный график, °C', 'x': 0.5, 'xanchor': 'center'},
                      xaxis_rangeslider_visible=True,
                      xaxis_rangeslider_thickness=0.1,
                      hovermode="x unified",
                      plot_bgcolor=colors['plot_area'],
                      paper_bgcolor=colors['plot_background'],
                      legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="right", x=1),
                      margin=dict(l=20, r=20, b=35, t=30, pad=1),
                      )

    # default position of xaxis_rangeslider on page load
    if n<1:
        fig['layout']['xaxis'].update(range=[data.index[-24], data.index[-1]])

    fig['layout']['xaxis'].update(
        rangeselector=dict(
            bgcolor=colors['plot_area'],
            xanchor="left",  #x=1,
            yanchor="bottom",  #y=1.02,
            buttons=list([
                dict(count=1, label="24 часа", step="day", stepmode="backward"),
                dict(count=3, label="72 часа", step="day", stepmode="todate"),
                dict(count=7, label="Неделя", step="day", stepmode="todate")
            ])
        )
    )
    return fig


def dg_graph_mini(data):

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                        subplot_titles=("Электрическая мощность, МВт", "Отклонение от графика, %"))
    fig.add_trace(go.Scatter(x=data.index, y=data.power, mode='lines',
                             line=dict(color='#0a84ff', width=2), name='Мощность'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data.dg, mode='lines',
                             line=dict(color='grey', width=2, dash='dash'), name='ДГ'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data.udg, mode='lines',
                             line=dict(color='lightgrey', width=2, dash='dash'), name='УДГ'), row=1, col=1)


    fig.add_trace(
        go.Scatter(x=data.index, y=data.error_power, mode='lines', fill='tozeroy', fillcolor='rgba(255,255,204,0.2)',
                   line=dict(color='lightsalmon', width=2), name='Отклонение, %'), row=2, col=1)

    fig.update_layout(
                      xaxis=dict(gridcolor=colors['grid']),
                      xaxis2=dict(gridcolor=colors['grid'], tickformat='%H:%M'),
                      yaxis=dict(gridcolor=colors['grid']),
                      yaxis2=dict(gridcolor=colors['grid']),
                      font_color=colors['graph_font'],
                      hovermode="x unified",
                      plot_bgcolor=colors['plot_area'],
                      paper_bgcolor=colors['plot_background'],
                      showlegend=False,
                      margin=dict(l=20, r=20, b=35, t=40, pad=1),
                      )

    return fig

def temp_graph_mini(data):

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                        subplot_titles=("Температура теплоносителя, °C", "Отклонение от графика, %"))
    fig.add_trace(go.Scatter(x=data.index, y=data.fact_forward, mode='lines',
                             line=dict(color='#ff0039', width=2), name='t°C в подающем'), row=1, col=1)

    fig.add_trace(go.Scatter(x=data.index, y=data.fact_backward, mode='lines',
                             line=dict(color='#ff9400', width=2), name='t°C в обратном'), row=1, col=1)

    fig.add_trace(
        go.Scatter(x=data.index, y=data.forward, mode='lines',
                   line=dict(color='rgba(255,0,57,0.6)', width=1, dash='dash'), name='Целевая t°C в подающем'),
        row=1, col=1)

    fig.add_trace(
        go.Scatter(x=data.index, y=data.backward, mode='lines',
                   line=dict(color='rgba(255,148,0,0.6)', width=1, dash='dash'), name='Целевая t°C в обратном'),
        row=1, col=1)

    fig.add_trace(
        go.Scatter(x=data.index, y=data.error_forward, mode='lines',
                   line=dict(color='lightsalmon', width=2), name='Откл. в подающем, %'), row=2, col=1)
    fig.add_trace(
        go.Scatter(x=data.index, y=data.error_backward, mode='lines',
                   line=dict(color='DeepSkyBlue', width=2), name='Откл. в обратном, %'), row=2, col=1)

    fig.update_layout(
                      xaxis=dict(gridcolor=colors['grid']),
                      xaxis2=dict(gridcolor=colors['grid'], tickformat='%H:%M'),
                      yaxis=dict(gridcolor=colors['grid']),
                      yaxis2=dict(gridcolor=colors['grid']),
                      font_color=colors['graph_font'],
                      hovermode="x unified",
                      plot_bgcolor=colors['plot_area'],
                      paper_bgcolor=colors['plot_background'],
                      showlegend=False,
                      margin=dict(l=20, r=20, b=40, t=40, pad=1),
                      )

    return fig
