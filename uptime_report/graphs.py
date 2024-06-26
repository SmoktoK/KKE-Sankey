import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff

import matplotlib.colors as mcolors

colors = {
    'grid': "#b9b9b9",
    'graph_font': "#000000",
    'plot_area': "#ffffff",
    'plot_background': "#fafafa",
}

def out_time_scatter(df):
    df = df[df.index.notnull()]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.01, row_width=[0.4, 1])

    #device_colors = ['rgb(220,20,60)', 'rgb(204,204,0)', 'rgb(20,60,220)']
    device_colors = list(mcolors.TABLEAU_COLORS.values())

    for i, device in enumerate(df['common-device'].unique()):

        color_id = i - len(device_colors) if i >= len(device_colors) else i

        data = df[df['common-device'] == device]
        # summary = data.groupby(data.index.date).agg('sum')
        summary = data.groupby(data.index.date).sum(numeric_only=True)
        sum_date = [datetime.datetime.strptime(str(dt), '%Y-%m-%d').date() for dt in summary.index]

        # Расчет масштаба графиков
        sum_max = max(summary['pq-duration'])
        if (sum_max / 60) >= 60:
            delta = 60
            delta_time = 'мин'
            if (sum_max / 3600) >= 1:
                delta = 3600
                delta_time = 'ч'
        else:
            delta = 60
            delta_time = 'мин'



        fig.add_trace(go.Scatter(x=data.index, y=data['pq-duration']/delta, name=device, opacity=0.6,
            legendgroup=f'group{i + 1}', showlegend=False,
                mode='markers', marker=dict(size=12, color=device_colors[color_id], line=dict(width=1, color='white')),
                                 ), row=1, col=1)
        # Отрисовка осей на графике

        fig.add_trace(go.Bar(x=summary.index, y=summary['pq-duration']/delta,
        # fig.add_trace(go.Bar(x=sum_date, y=summary['pq-duration'],
        #                     xperiodalignment="start",
                             xperiodalignment='middle',
                             xperiod=86400000,
                             opacity=1,
                             # slector=dict(type='bar'),
                             base='base',
                             # text=summary.index, textposition='outside', textfont=dict(size=20),
                             name=device, marker_color=device_colors[color_id], legendgroup=f'group{i + 1}'), row=2, col=1,)

    fig.update_layout(height=720,
                      # barmode='overlay',
                      # barmode='stack',

                      xaxis=dict(gridcolor=colors['grid'],
                                 # dtick = pd.to_timedelta(1, unit="D"),
                                 showline=True, linewidth=1, linecolor=colors['grid'], mirror=True),
                      xaxis2=dict(gridcolor=colors['grid'],
                                  # dtick = pd.to_timedelta(1, unit="D"),
                                 showline=True, linewidth=1, linecolor=colors['grid'], mirror=True),
    #                   yaxis=dict(gridcolor=colors['grid'], zeroline=False,
    #                              showline=True, linewidth=1, linecolor=colors['grid'], mirror=True),
    #                   yaxis2=dict(gridcolor=colors['grid'], zeroline=False,
    #                              showline=True, linewidth=1, linecolor=colors['grid'], mirror=True),
    #                   xaxis_range=(df.date.min()-datetime.timedelta(days=1), df.date.max()+datetime.timedelta(days=1)),
    #                   xaxis2_range=(df.date.min() - datetime.timedelta(days=1), df.date.max() + datetime.timedelta(days=1)),
    #                   yaxis1_title=f"Продолжительность, {delta_time}",
                      yaxis1_title=dict(text=f'Продолжительность, {delta_time}'),
                      yaxis2_title=f"Общее время, {delta_time}",
                      font_color=colors['graph_font'],
                      title_text='Продолжительность сбоев',
                      titlefont=dict(size=20),
                      # plot_bgcolor=colors['plot_area'],
                      # paper_bgcolor=colors['plot_background'],
                      hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                      margin=dict(l=50, r=0, b=30, t=80, pad=1),
                      )

    fig.update_traces(
        # hoverinfo="all",
        # xperiodalignment="start",
        # xperiod=86400000, slector=dict(type='bar')
        )
    fig.update_yaxes(
        title_standoff=3,
        title_font={"size": 12})


    return fig


def out_table(df):
    df = df.fillna(0).astype(int)

    x = [x.strftime("%b, %d") for x in df.columns.to_list()]
    y = df.index.to_list()
    z_text = [list(df.iloc[i].values) for i in range(len(y))]
    z = np.array(z_text).clip(0, 10)
    # x = [1]
    # y = [0, 1, 5, 2]
    # z = ['r', 'r', 't', 'f']
    # z_text = y

    colorscale = [[0, 'rgb(0,200,0)'],
                  [0.1, 'rgb(100, 200, 0)'],
                  [0.2, 'rgb(150, 200, 0)'],
                  [0.3, 'rgb(200, 200, 0)'],
                  [0.4, 'rgb(220, 200, 0)'],
                  [0.5, 'rgb(255, 200, 0)'],
                  [0.6, 'rgb(255, 150, 0)'],
                  [0.7, 'rgb(255, 100, 0)'],
                  [0.8, 'rgb(255, 50, 0)'],
                  [0.9, 'rgb(255, 0, 0)'],
                  [1, 'rgb(220, 0, 0)']]

    fig = ff.create_annotated_heatmap(z, x=x, y=y, colorscale=colorscale, xgap=1, ygap=1,
                                      annotation_text=z_text, text=z_text, hoverinfo='text',
                                      # colorbar=dict(title='')
                                      )

    height = max(85 * len(df), 250)
    width = len(df.columns) * 50
    fig.update_layout(height=height,
                      width=width,
                      xaxis=dict(showgrid=False, side='top'),
                      yaxis=dict(showgrid=False),
                      font_color=colors['graph_font'],
                      # plot_bgcolor=colors['plot_area'],
                      # paper_bgcolor=colors['plot_background'],
                      title_text='Тепловая карта сбоев',
                      titlefont=dict(size=20),
                      margin=dict(l=0, r=0, b=30, t=140, pad=1)
                      )
    return fig
