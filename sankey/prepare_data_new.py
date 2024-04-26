import datetime

import numpy as np
from pandas import DataFrame
import plotly.graph_objects as go

from sdk import Sedmax
from settings import SankeyColor


def prepare_arch_request(devices, start_time: datetime, end_time: datetime) -> list[dict]:
    thirty_min_count = 10000 // (len(devices) * 2)
    start = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    dif_time = end - start
    total_count_30min = int(dif_time.total_seconds() // 1800 * len(devices) * 2)
    asks = (total_count_30min // 10000) + 1
    thirty_min_timestamps = [start + i * datetime.timedelta(minutes=thirty_min_count * 30) for i in range(asks)]
    thirty_min_timestamps.append(end_time)
    channels_recive = ['el-dev-' + str(dev) + '-ea_imp-30m' for dev in devices]
    channels_trans = ['el-dev-' + str(dev) + '-ea_exp-30m' for dev in devices]
    final_req = []
    for i in range(len(thirty_min_timestamps) - 1):
        req = {
            "channels": channels_recive + channels_trans,
            "begin": str(thirty_min_timestamps[i]),
            "end": str(thirty_min_timestamps[i+1]),
        }
        final_req.append(req)
    # print(final_req)
    return final_req


def getting_arch_from_api_for_sankey(s: Sedmax, req: list[dict]) -> dict:
    sum_energy = {}
    url = s.host + '/sedmax/archive_webapi/archive'
    for ask in req:
        raw_data = s.get_data(url, ask)
        if len(raw_data) == 0:
            for id in ask['channels']:
                if 'ea_imp-30m' in id:
                    sum_energy[id.lstrip('el-dev-').rstrip('ea_imp-30m')] = 0.01
                else:
                    sum_energy[id.lstrip('el-dev-').rstrip('ea_exp-30m')] = 0.01
            return sum_energy
        for chanel in raw_data:
            dev, _, side = chanel['channel'].lstrip('el-dev-').rstrip('-30m').partition('-')
            dev = int(dev)
            total = sum([x['v'] for x in chanel['data']])
            if sum_energy.get(dev):
                if side == 'ea_imp':
                    sum_energy[dev] = sum_energy[dev] + total
                elif side == 'ea_exp':
                    sum_energy[dev] = sum_energy[dev] - total
                else:
                    print(f'Ошибка приёма ')
            else:
                if side == 'ea_imp':
                    sum_energy[dev] = total
                elif side == 'ea_exp':
                    sum_energy[dev] = -(total)
                else:
                    print(f'Ошибка приёма ')
    return sum_energy


def prepare_label(s: Sedmax) -> list:
    return [key for key in s.node]


def cleaning_data(df: DataFrame) -> DataFrame:
    for row in df.itertuples():
        if row[4] == 0:
            df.at[row[0], 'sum_energy'] = 0.01
        elif row[4] < 0:
            val = row[4]
            start = row[2]
            end = row[3]
            df.at[row[0], 'sum_energy'] = abs(val)
            df.at[row[0], 'start_node'] = end
            df.at[row[0], 'end_node'] = start
    return df


def prepare_source_target(label: list, s: Sedmax, df: DataFrame):
    label_index = [s.node[x] for x in label]
    source = []
    target = []
    for row in df.itertuples():
        source.append(label_index.index(row[2]))
        target.append(label_index.index(row[3]))
    return source, target


def generate_link_color(s: Sedmax, source: list) -> list:
    return [s.link_color[i] for i in source]


def load_data(s: Sedmax, start_date: datetime, end_date: datetime) -> list[dict]:
    labels = prepare_label(s)
    request = prepare_arch_request(s.channel.index.tolist(), start_date, end_date)
    arch_data = getting_arch_from_api_for_sankey(s, request)
    data_df = s.channel.copy()
    data_df['sum_energy'] = data_df.index.map(arch_data).fillna(0)
    data_df = cleaning_data(data_df)
    value = data_df['sum_energy'].tolist()
    source, target = prepare_source_target(labels, s, data_df)
    node_colors = s.node_color
    link_colors = generate_link_color(s, source)

    return [{"source": source, "target": target, "value": value, "labels": labels, "link_colors": link_colors,
             "sourse_colors": node_colors, 'node_color': node_colors}]


def sankey_plot(data):
    fig = go.Figure(go.Sankey(
        valuesuffix=" кВтч",
        node=dict(
            pad=45,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=data["labels"],
            color=data['node_color'],
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
        )))
    fig.update_layout(height=700,
                      font_color=SankeyColor.GRAPH_FONT.value,
                      font_size=10,
                      # title_text='Электроснабжение офиса. Активная электроэнергия',
                      # plot_bgcolor=colors['plot_area'],
                      paper_bgcolor=SankeyColor.PLOT_BACKGROUND.value,
                      # margin=dict(l=20, r=20, b=30, t=30, pad=1),
                      )
    return fig
