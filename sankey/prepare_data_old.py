import numpy as np
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

colors = {
    'grid': "#b9b9b9",
    'graph_font': "#000000",
    'plot_area': "#ffffff",
    'plot_background': "transparent",
    # 'plot_background': "#fafafa",
    'active_link': 'rgba(200,200,200,0.7)',
    'disabled_link': 'rgba(250,100,100,0.7)',
}

def load_data(el, start_date, end_date):
    df = el.get_data(["dev-101_ea_imp","dev-109_ea_imp","dev-110_ea_imp",
                    "dev-111_ea_imp","dev-112_ea_imp","dev-114_ea_imp",
                    "dev-108_ea_imp","dev-102_ea_imp","dev-103_ea_imp",
                    "dev-104_ea_imp","dev-105_ea_imp","dev-106_ea_imp",
                    "dev-107_ea_imp","dev-202_ea_imp","dev-201_ea_imp",
                    "dev-113_ea_imp","dev-116_ea_imp","dev-117_ea_imp"], ['30min'],
                     start_date, end_date)

    tree = el.devices_tree()
    parents = tree.parent.unique()

    names = tree.name.values.tolist()
    #names.append('object-0')
    map_dict = tree.id.values.tolist()
    #map_dict.append('object-0')
    map_dict = dict([(v,k) for (k,v) in enumerate(map_dict)])

    power_data = df.sum()
    power_data.index = [x.split('_')[0].replace('dev', 'device') for x in power_data.index]
    power_data['device-110'] = power_data['device-110']/1000

    power_data.index = power_data.index.map(map_dict)
    tree.id = tree.id.map(map_dict)

    records = [
        {'dev': 23, 'children': [8]},
        {'dev': 8, 'children': [1]},
        {'dev': 1, 'children': [15, 16, 17, 18, 25]},
        {'dev': 24, 'children': [9]},
        {'dev': 9, 'children': [2]},
        {'dev': 2, 'children': [10, 11, 12, 13, 14]},
        {'dev': 12, 'children': [20]},
        {'dev': 18, 'children': [19]},
        {'dev': 14, 'children': [19]},
        {'dev': 19, 'children': [21]},
        {'dev': 20, 'children': [22]},
    ]

    def flatten(t):
        return [item for sublist in t for item in sublist]

    source = []
    target = []
    value = []
    link_colors = []

    for record in records:
        children = record['children']
        device = record['dev']
        values = []

        if len(children) <= 1:
            if device in power_data.index:
                if power_data[device] != 0:
                    values.append(power_data[device])
                    link_colors.append(colors['active_link'])
                else:
                    values.append(0.01)
                    link_colors.append(colors['disabled_link'])
            else:
                values.append(0.01)
                link_colors.append(colors['disabled_link'])
        else:
            for child in children:
                if child in power_data.index:
                    if power_data[child] != 0:
                        values.append(power_data[child])
                        link_colors.append(colors['active_link'])
                    else:
                        values.append(0.01)
                        link_colors.append(colors['disabled_link'])
                else:
                    values.append(0.01)
                    link_colors.append(colors['disabled_link'])

        node = [record['dev']] * len(children)

        source.append(node)
        target.append(children)
        value.append(values)

    source = flatten(source)
    target = flatten(target)
    value = flatten(value)
    labels = names

    return [{"source": source, "target": target, "value": value, "labels": labels, "link_colors":link_colors}]


def sankey_plot(data):

    fig = go.Figure(go.Sankey(
        valuesuffix=" кВтч",
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=data["labels"],
            #x= [0.2, 0.1, 0.5, 0.7, 0.3, 0.5],
            #y= [0.2, 0.1, 0.5, 0.7, 0.3, 0.5],
            # color = "blue"
        ),
        link=dict(
            source=data["source"],  # indices correspond to labels, eg A1, A2, A1, B1, ...
            target=data["target"],
            value=data["value"],
            color=data["link_colors"],
        )))

    fig.update_layout(height=700,
                      font_color=colors['graph_font'],
                      font_size=10,
                      #title_text='Электроснабжение офиса. Активная электроэнергия',
                      plot_bgcolor=colors['plot_area'],
                      paper_bgcolor=colors['plot_area'],
                      margin=dict(l=0, r=0, b=30, t=30, pad=1),
                      )

    return fig
