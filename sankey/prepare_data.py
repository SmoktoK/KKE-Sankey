import numpy as np
import pandas as pd
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

colors = {
    'grid': "#b9b9b9",
    'graph_font': "#000000",
    'plot_area': "#ffffff",
    'plot_background': "#fafafa",
    'active_link': 'rgba(200,200,200,0.7)',
    'disabled_link': 'rgba(250,100,100,0.7)',
    'node': 'rgba(200,200,200,0.7)',
}

#generate color
def generate_random_color(size=3):
    r, g, b = np.random.randint(low=10, high=255, size=size)
    return f'rgba({r}, {g}, {b}, 0.2)'


def load_data(el, start_date, end_date):
    # df = el.get_data(["dev-101_ea_imp","dev-109_ea_imp","dev-110_ea_imp",
    #                 "dev-111_ea_imp","dev-112_ea_imp","dev-114_ea_imp",
    #                 "dev-108_ea_imp","dev-102_ea_imp","dev-103_ea_imp",
    #                 "dev-104_ea_imp","dev-105_ea_imp","dev-106_ea_imp",
    #                 "dev-107_ea_imp","dev-202_ea_imp","dev-201_ea_imp",
    #                 "dev-113_ea_imp","dev-116_ea_imp","dev-117_ea_imp"], ['30min'],
    #                  start_date, end_date)

    s = el
    # devices = ['device-101', 'device-109', 'device-110', 'device-111', 'device-112', 'device-114', 'device-108',
    #            'device-102', 'device-103', 'device-104', 'device-105', 'device-106', 'device-107', 'device-202',
    #            'device-201', 'device-113', 'device-116', 'device-117']

    devices = ['device-101', 'device-102', 'device-103', 'device-104', 'device-105', 'device-106', 'device-107', 'device-108',
               'device-109', 'device-110', 'device-111', 'device-112', 'device-113', 'device-114', 'device-116',
               'device-117', 'device-201', 'device-202']

    channels = ['electro-1-' + x.split('-')[-1] for x in devices]

    req = {
        "begin": start_date,
        "end": end_date,
        #"function": "sum",
        #"groupby": "30m",
        "groupby": "off",
        "nodes": channels
    }

    data = s.get_data(s.host + '/sedmax/archive/archive', req)
    df = pd.DataFrame(data['tableRows'])
    df.set_index('dt', inplace=True)
    df.index = pd.to_datetime(df.index)

    for i, channel in enumerate(channels):
        df[channel] = df.cells.map(lambda x: x[i]['value'])
        df[channel] = pd.to_numeric(df[channel], errors='coerce')
    df.drop('cells', axis=1, inplace=True)

    df.columns = devices

    #tree = el.devices_tree()

    device_list = s.get_data(s.host + '/sedmax/archive/channels_tree', {"treeType": "devices"})
    device_list = pd.DataFrame(device_list['tree'])
    tree = device_list.rename(columns={'parentCode': 'parent', 'code': 'id'})
    # остваить только электрические объекты и устройства
    tree = tree[(tree.classCode == 'object') | (tree.classCode == 'device')].loc[:232]

    parents = tree.parent.unique()

    names = tree.name.values.tolist()
    #names.append('object-0')
    map_dict = tree.id.values.tolist()
    #map_dict.append('object-0')
    map_dict = dict([(v,k) for (k,v) in enumerate(map_dict)])

    power_data = df.sum()
    # power_data.index = [x.split('_')[0].replace('dev', 'device') for x in power_data.index]
    # power_data['device-110'] = power_data['device-110']/1000

    power_data.index = power_data.index.map(map_dict)
    tree.id = tree.id.map(map_dict)

    # records = [
    #     {'dev': 23, 'children': [8]},
    #     {'dev': 8, 'children': [1]},
    #     {'dev': 1, 'children': [15, 16, 17, 18, 25]},
    #     {'dev': 24, 'children': [9]},
    #     {'dev': 9, 'children': [2]},
    #     {'dev': 2, 'children': [10, 11, 12, 13, 14]},
    #     {'dev': 12, 'children': [20]},
    #     {'dev': 18, 'children': [19]},
    #     {'dev': 14, 'children': [19]},
    #     {'dev': 19, 'children': [21]},
    #     {'dev': 20, 'children': [22]},
    # ]

    records = [
        {'dev': 17, 'children': [2]},
        {'dev': 2, 'children': [5, 3, 4, 7, 8]},
        {'dev': 19, 'children': [10]},
        {'dev': 10, 'children': [11, 12, 13, 14, 15]},
        {'dev': 5, 'children': [21]},
        {'dev': 21, 'children': [23]},
        {'dev': 15, 'children': [6]},
        {'dev': 6, 'children': [24]},
        {'dev': 12, 'children': [21]},
    ]
    # devices = ['device-101', 'device-102', 'device-103', 'device-104',
    #           'device-105', 'device-106', 'device-107', 'device-108',
    #            'device-109', 'device-110', 'device-111', 'device-112',
    #            'device-113', 'device-114', 'device-116', 'device-117',
    #            'device-201', 'device-202']
    # records = [
    #     {'dev': 17, 'children': [1]},
    #     {'dev': 1, 'children': [10, 11, 12, 8, 9]},
    #     {'dev': 12, 'children': [13]},
    #     {'dev': 13, 'children': [15]},
    #     {'dev': 18, 'children': [2]},
    #     {'dev': 2, 'children': [3, 4, 5, 6, 7]},
    #     {'dev': 7, 'children': [13]},
    #     {'dev': 5, 'children': [14]},
    #     {'dev': 14, 'children': [17]},
    # ]

    def flatten(t):
        return [item for sublist in t for item in sublist]

    source = []
    target = []
    value = []
    sourse_colors = []
    link_colors = []
    dev = {i+1:generate_random_color() for i in range(len(map_dict))}
    # for i in map_dict:
    #     print(i)
    #     sourse_colors.append(dev[map_dict[i]])
    # pass


    for record in records:
        children = record['children']
        device = record['dev']
        values = []
        sColor = dev[device]  # color sourse
        if len(children) <= 1:
            if device in power_data.index:
                if power_data[device] != 0:
                    values.append(power_data[device])
                    link_colors.append(sColor)
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
                        link_colors.append(sColor)
                    else:
                        values.append(0.01)
                        link_colors.append(colors['disabled_link'])
                else:
                    values.append(0.01)
                    link_colors.append(colors['disabled_link'])
        node = [record['dev']] * len(children)
        source.append(node)
        # sourse_colors.append(dev[node])
        target.append(children)
        value.append(values)


    source = flatten(source)
    target = flatten(target)
    value = flatten(value)
    labels = names

    return [{"source": source, "target": target, "value": value, "labels": labels, "link_colors": link_colors, "sourse_colors": sourse_colors}]


def sankey_plot(data):

    fig = go.Figure(go.Sankey(
        valuesuffix=" кВтч",
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=data["labels"],
            color=colors['node'],
            # color=data["sourse_colors"]
            # x= [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            # y= [0.2, 0.1, 0.5, 0.7, 0.3, 0.5],
            # color = "blue"
        ),
        link=dict(
            source=data["source"],  # indices correspond to labels, eg A1, A2, A1, B1, ...
            target=data["target"],
            value=data["value"],
            color=data["link_colors"],
            # arrowlen=15,
        )))
    fig.update_layout(height=700,
                      font_color=colors['graph_font'],
                      font_size=10,
                      #title_text='Электроснабжение офиса. Активная электроэнергия',
                      #plot_bgcolor=colors['plot_area'],
                      paper_bgcolor=colors['plot_background'],
                      #margin=dict(l=20, r=20, b=30, t=30, pad=1),
                      )

    return fig
