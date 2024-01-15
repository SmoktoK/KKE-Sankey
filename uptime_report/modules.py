import pandas as pd
import numpy as np
import datetime
from datetime import timedelta

def pq_devices(s, nodes, protocol_Id):
    df = s.devices_list(nodes)
    if df.empty:
        return df
    df['protocols'] = df['protocols'].apply(lambda x: [(k, v) for d in x for k, v in d.items()])
    df['PQ'] = df['protocols'].apply(lambda x: True if ('protocolId', protocol_Id) in x else False)
    df_pq = df[df['PQ']]
    return df_pq


def report_by_device(df, devs_list, start, end):

    total_time = (end - start).total_seconds()

    # Шаблон отчета по утройствам
    report_template = pd.DataFrame({'Присоединение': devs_list})
    # nullt = datetime.timedelta(seconds=0)
    report_template[['Uptime', 'Uptime_percent', 'outage_time', 'outage_percent']] = total_time, 100, 0, 0
    # report_template[['events', 'outage_min', 'outage_max', 'MTBF', 'MTTR']] = 0, 0, 0, 0, 0
    report_template[['events', 'outage_min', 'outage_max', 'MTBF', 'MTTR']] = 0, np.NaN, np.NaN, pd.NaT, np.NaN
    # report_template[['events', 'outage_min', 'outage_max', 'MTBF', 'MTTR']] = 0, np.NaN, np.NaN, np.NaN, np.NaN

    report_template = report_template.reset_index().drop('index', axis=1)

    def features(df):
        outage_time = df.groupby('common-device')['pq-duration'].sum().item()
        # outage_time = 10
        events = df.groupby('common-device')['common-number'].count().item()
        outage_min = np.round(df.groupby('common-device')['pq-duration'].fillna(0).min().item(), 2)
        outage_max = np.round(df.groupby('common-device')['pq-duration'].fillna(0).max().item(), 2)
        MTBF = (str(df.groupby('common-device')['TBF'].mean().fillna(0).dt.round(freq='S').item()).replace('days', 'д'))  # seconds
        # MTBF = start
        MTTR = str(datetime.timedelta(seconds=df.groupby('common-device')['pq-duration'].mean().fillna(0).item()))

        return outage_time, events, outage_min, outage_max, MTBF,  MTTR

    def calc_features(df):
        df['Uptime'] = total_time - df['outage_time']
        df['Uptime_percent'] = 100 * df['Uptime'] / total_time
        df['outage_percent'] = 100 * df['outage_time'] / total_time

        df['Uptime'] = pd.to_timedelta(df['Uptime'], unit='s').dt.round('s').astype('str').str.replace('days', 'д')
        df['outage_time'] = pd.to_timedelta(df['outage_time'], unit='s').dt.round('s').astype('str').str.replace('days', 'д')
        df['outage_min'] = pd.to_timedelta(df['outage_min'], unit='s').dt.round('s').astype('str').str.replace('days', 'д')
        df['outage_max'] = pd.to_timedelta(df['outage_max'], unit='s').dt.round('s').astype('str').str.replace('days', 'д')
        df.fillna(0)
        return df

    for i, row in report_template.iterrows():
        obj = row['Присоединение']
        subset = df[df['common-device'] == obj]
        if len(subset) > 0:
            report_template.loc[i, ['outage_time', 'events', 'outage_min', 'outage_max', 'MTBF', 'MTTR']] = features(
                subset)

    report_template = calc_features(report_template).round(3)
    report_template[['outage_percent', 'Uptime_percent']] = report_template[['outage_percent', 'Uptime_percent']].astype(str)
    return report_template

# функция возвращает общее время сбоев/без сбоев с учётом наложения событий
def fault(events_lists, bfault=True):
    events = []
    for k in events_lists:
        ev = events_lists[k]
        for i in range(len(ev)):
            events.append(ev[i], 1 - 2*(i%2))
    events.sort()
    cnt = 0
    st = -1
    el_t = 0
    for e in events:
        cnt += e[1]
        if cnt == 3:
            st = e[0]
        if cnt == 2 and st>0:
            el_t += e[0] - st
            st = -1
    return el_t

#возвращает время пересечения интервалов сбоев
def interval(event):
    dev = []
    for i,v in enumerate(event):
      datbegin= event.index[i]
      intervali = v
      dateend =  datbegin + timedelta(seconds=intervali)
      dev.append({'b':datbegin,'e':dateend})
    total_rez = 0.0
    de = pd.DataFrame(dev)
    de[['b', 'e']] = de[['b', 'e']].apply(pd.to_datetime)
    de.sort_values(by=['b','e'], inplace=True)
    de.reset_index(drop=True)
    for i, data in de.iterrows():
        b = data['b']
        e = data['e']
        rezul = de.query('@b <= e and @e >= b')
        for i, rez in rezul.iterrows():
            delete = rez.name
            de.drop(labels=[delete],axis=0,inplace=True)
        if rezul.empty == False:
            if rezul.shape[0]>1:
                #print(rezul)
                u=1
                ind = rezul.shape[0]-1
                ind = int(ind)
                for end in rezul['e']:
                        begin = rezul['b'].iloc[u]
                        u += 1
                        if end > begin:
                            rez = end - begin
                            rez = timedelta.total_seconds(rez)
                            total_rez = total_rez + rez
                        if u > ind:
                            break
    return total_rez


# Собираем таблицу с общими данными
def report(df, device_list, start, end, df_old):
    # Данные за текущий период
    data = df[df['common-device'].isin(device_list)]
    total_time = (end - start).total_seconds()
    outage_time = np.round(data["pq-duration"].sum(), 3)
    intersec = interval(data["pq-duration"])
    outage_time = (outage_time - intersec)
    outage_proc = np.round(100 * outage_time / total_time, 3)
    tot_int = str(datetime.timedelta(seconds=total_time)).replace('days,', 'д')
    # Данные за предыдущий период
    x_y = end - start
    data_old = df_old[df_old['common-device'].isin(device_list)]
    total_time_old = ((end - x_y) - (start - x_y)).total_seconds()
    tot_int_old = str(datetime.timedelta(seconds=total_time_old)).replace('days,', 'д')
    outage_time_old = np.round(data_old["pq-duration"].sum(), 3)
    intersec_old = interval(data_old["pq-duration"])
    outage_time_old = (outage_time_old - intersec_old)
    outage_proc_old = np.round(100 * outage_time_old / total_time_old, 3)

    total = pd.DataFrame.from_dict(
        {'Выбранный период анализа': [start.strftime("%d %b %Y") + " - " + end.strftime("%d %b %Y"),
                                      (start - x_y).strftime("%d %b %Y") + " - " + start.strftime("%d %b %Y")],
         # 'Секунд в выбранном периоде': f'{int(total_time)}, сек',
         'Время выбранного периода': [f'{tot_int}', f'{tot_int_old}'],
         # 'Outage': f'{outage_time}, сек',
         'Общее время сбоев': [f'{outage_proc}, %', f'{outage_proc_old}, %'],
         # 'Uptime': f'{total_time - outage_time}, сек',
         'Общее время без сбоев': [f'{np.round(100 * (total_time - outage_time) / total_time, 3)}, %',
                                   f'{np.round(100 * (total_time_old - outage_time_old) / total_time_old, 3)}, %'],
         'Количество событий': [data["common-number"].count(), data_old["common-number"].count()],
         'Количество устройств': [len(device_list), len(device_list)],
         'Общая наработка на отказ (MTBF):': [str(data["TBF"].mean().round(freq="T")).replace('days', 'д'),
                                              str(data_old["TBF"].mean().round(freq="T")).replace('days', 'д')],
         'Общее среднее время восстановления (MTTR):': [f'{str(datetime.timedelta(seconds=np.round(data["pq-duration"].mean(), 3))).replace("days", "д")}',
                                                        f'{str(datetime.timedelta(seconds=np.round(data_old["pq-duration"].mean(), 3))).replace("days", "д")}']
         },
        orient='Index')
    total = total.reset_index()
    total = total.rename(columns={'index': 'Характеристика', 0: 'Значение', 1: 'Значение1'})

    return total


def uptime_table(df, devs_list, start, end, EMPTY_JOURNAL):
    # Шаблон для таблицы отказов

    days = pd.date_range(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), freq='D')
    outer_template = pd.DataFrame({'date': days.date})
    for dev in devs_list:
        outer_template[dev] = np.NaN

    if EMPTY_JOURNAL:
        outer_template = outer_template.set_index('date').transpose().fillna(0)
        outer_template = outer_template.astype('int')
    else:
        # События из журнала
        events = df.groupby(['common-device', 'date']).count().reset_index()
        data = outer_template.merge(events[['common-device', 'date', 'common-number']], how='left')
        data = data.pivot(index='date', columns='common-device')['common-number']

        # Добавить события в шаблон
        for dev in data:
            if dev in outer_template.columns:
                outer_template[dev] = data[dev].to_numpy()

        outer_template = outer_template.set_index('date').transpose().fillna(0)
        outer_template = outer_template.astype('int')

    return outer_template



def empty_plot():
    return {
        "layout": {
            "heigth": "500px",
            "width": "500px",
            "xaxis": {
                "visible": False
            },
            "yaxis": {
                "visible": False
            },
            "annotations": [
                {
                    "text": "Отсутствуют данные для отображения",
                    "align": "center",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {
                        "size": 28,
                        "color": "gray"
                    }
                }
            ]
        }
    }

