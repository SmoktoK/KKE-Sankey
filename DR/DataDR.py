import pandas as pd
import random
import numpy as np
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots


colors = {
    'grid': "rgba(255,255,255,0.2)",
    'graph_font': "#f0f8ff",
    'plot_area': "rgba(50,50,50,0.9)",
    'plot_background': "rgba(50,50,50,0.2)",
}

def power_chart_rtd(data, power_rtd, error):
    #error = 100 * (data.gen_power - data.DG) / data.DG
#   MIN = data['установленная мощность'].min() * 0.9
#   MAX = data['установленная мощность'].max() * 1.1

    #t = data.Date.iloc[-1].replace(hour=time, minute=00)
    #gen_power_view = data[data.Date <= t].gen_power
    #error = error[gen_power_view.index]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_width=[1, 1], subplot_titles=('Электрическая мощность, МВт', "Отклонение, %"))
    # make_subplots - создает кординаты графика
    # rows - количество строк в матреце графиков/2 графика по вертикали
    # cols- количество столбцов в матреце графиков/1 график по горизонтали
    # shared_xaxes стекирование графиков с осью х
    # subplot_titles- подпись графиков
    # row_width заменена в новой документации на row_heights, остаеться для обратной совместимости
    # row_heights задает высоты графиков в виде соотношения сторон
    fig.add_trace(go.Scatter(x=data.index, y=data['DR'], mode='lines+markers', fill='tozeroy',
    #  add_trace - методот добовляет линию графика в поле координат
    # mode режим отображения линии/ точки графика соеденены линиями
                fillcolor='rgba(241,241,241,0.5)', line=dict(color='grey', width=2, dash='dash'), line_shape='hv', name='DR'),
                                row=1, col=1)
    #  row, col - номера графика в матрице графиков

    fig.add_trace(go.Scatter(x=data.index, y=data['Заявка'], mode='lines',
                 line=dict(color='lightgrey', width=2, dash='dash'), line_shape='hv', name='Заявка'),
                                row=1, col=1)


    # график с ртд данными
    fig.add_trace(go.Scatter(x=power_rtd.index, y=power_rtd['power'],  #fill='tozeroy', fillcolor='rgba(241,241,241,0.4)',
                             line=dict(color='steelblue', width=3), name='Мощность'), row=1, col=1)

    fig.add_trace( go.Scatter(x=error.index, y=error.values, mode='lines', fill='tozeroy', fillcolor='rgba(255,255,204,0.35)',
                   line=dict(color='lightsalmon', width=2), name='Отклонение, %'), row=2, col=1)

    fig.update_layout(height=450,
    # update_layout - метод для изменения свойств поля координат и графиков на нем
                      xaxis=dict(gridcolor=colors['grid']), #range=[data.index[0], data.index[-1]]),
                      # xaxis свойство оси х , range - диапазон оси
                      xaxis2=dict(gridcolor=colors['grid']),
                      #xaxis2 свойство оси х второго рафика
                      yaxis=dict(gridcolor=colors['grid'], range=[100, 200]), #, range=[data.Min, data.Max]),
                      # уaxis свойство оси у
                      yaxis2=dict(gridcolor=colors['grid']), #tickvals=[-4, -2, 0, 2, 4]),
                      # уaxis2 свойство оси у второго рафика
                        #tickvals атрибут устанавливает деоения на оси у
                      font_color=colors['graph_font'],
                      #title_text='Электрическая мощность, МВт',

                      #xaxis_rangeslider_visible=True,
                      # показывает маштаб графика
                      #xaxis_rangeslider_thickness=0.1,
                      hovermode="x unified",
                      #hovermode - атрибут для управления свойствами подсказки на линии графика
                      plot_bgcolor=colors['plot_area'],
                      paper_bgcolor=colors['plot_background'],
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                      # legend - атрибут для установки свойств отображения легенды
                      margin=dict(l=20, r=20, b=30, t=70, pad=1),
                      # margin - атрибут  для отступов графика /
                      # l — отступ слева, r — отступ справа, t — отступ сверху, b — отступ снизу
                      #
                      )

    # отступ для названий графиков
    fig.layout.annotations[0].update(x=0.15)
    fig.layout.annotations[1].update(x=0.1)


#    fig['layout']['xaxis'].update(
#       rangeselector=dict(
#            bgcolor=colors['plot_area'],
#           xanchor="left",  # x=1,
#            yanchor="bottom",  # y=1.02,
#            buttons=list([
#                dict(count=1, label="Сутки", step="day", stepmode="backward"),
#                dict(count=7, label="Неделя", step="day", stepmode="backward"),
 #               dict(count=1, label="Месяц", step="month", stepmode="todate"),
                # dict(label="Все", step="all")
 #           ])
 #       )
 #   )
    return fig


def power_bar(data, power_rtd):

    hour_power = data[data.index == power_rtd.hour.item()]

    fig = make_subplots()#subplot_titles=('Мощность'), row_width=[1, 1],vertical_spacing=0.18, rows=1, cols=1, shared_xaxes=True,

    fig.add_trace(go.Bar(x=['Мощность'], y = power_rtd.power, text= power_rtd.power,
                         textposition='outside', marker_color='steelblue', name='Мощность'), row=1, col=1)
    fig.add_trace(go.Bar(x=['DR'], y=hour_power['DR'],
                         text= hour_power['DR'],
                         textposition='outside', marker_color= 'grey', name= 'DR'))
    fig.add_trace(go.Bar(x=['Заявка'], y=hour_power['Заявка'],
                         text=hour_power['Заявка'],
                         textposition='outside', marker_color='lightsalmon', name='Заявка'))

    fig.update_layout(yaxis=dict(gridcolor=colors['grid'], range=[110, 200]),
                      yaxis2=dict(gridcolor=colors['grid']),
                      font_color=colors['graph_font'],
                      barmode='overlay',
                      height=450,
                      title = 'Целевое значение мощности <br>на текущий час',
                      title_x=0.5,
                      title_y=0.93,
                      paper_bgcolor=colors['plot_background'],
                      plot_bgcolor=colors['plot_area'],
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                      margin=dict(l=20, r=20, b=30, t=100, pad=1),
                      showlegend=True,
                      )
    return fig
