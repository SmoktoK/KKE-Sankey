import datetime
import time

import pandas as pd
import math

# time_ran = '30 days 05:49:58'
# time_ran1 = '10 days 05:49:58'
# x = pd.to_timedelta(time_ran)
# y = pd.to_timedelta(time_ran1)
# print(x - y)

report = pd.read_csv('report_template.csv')
report_old = pd.read_csv('report_template_old.csv')
column_names = (report.columns.tolist())
name = column_names.pop(0)
my_df = pd.DataFrame(columns=column_names)


def time_delta(i, z, data, data_old):
    if z in ['Uptime_percent', 'outage_percent']:
        if float(data) > float(data_old):
            my_df.loc[i, z] = f'{data}%, лучше в {round(float(data) / float(data_old), 2)} раз(а)'
        elif float(data) < float(data_old):
            my_df.loc[i, z] = f'{data}%, хуже в {round(float(data_old) / float(data), 2)}раз(а)'
        elif float(data) == float(data_old):
            my_df.loc[i, z] = f'{data}%, значения равны'

    elif z in ['Uptime', 'outage_time', 'outage_min', 'outage_max', 'MTBF', 'MTTR']:

        if 'д' in data:
            data = data.replace('д', 'days')
            data = pd.to_timedelta(data)
        if 'д' in data_old:
            data_old = data_old.replace('д', 'days')
            data_old = pd.to_timedelta(data_old)
        if pd.isna(data) == True:
            data = '00:00:00'
        if pd.isna(data_old) == True:
            data_old = '00:00:00'
        if 'д' in data:
            data = data.replace('д', 'days')
            data = pd.to_timedelta(data)
        if 'д' in data_old:
            data_old = data_old.replace('д', 'days')
            data_old = pd.to_timedelta(data_old)
        if data == 'NaT' or data == pd.NaT:
            data = '00:00:00'
        if data_old == 'NaT' or data_old == pd.NaT:
            data_old = '00:00:00'

        if data > data_old and data_old != '00:00:00' or data_old != pd.Timedelta('0 days 00:00:00'):
            my_df.loc[i, z] = f'{str(data).replace('days', 'д')}, лучше в {round(data / data_old, 2)} раз(а)'
        elif data < data_old and data != '00:00:00' or data != pd.Timedelta('0 days 00:00:00'):
            my_df.loc[i, z] = f'{str(data).replace('days', 'д')}, хуже в {round(data_old / data, 2)} раз(а)'
        elif data == data_old:
            my_df.loc[i, z] = f'{str(data).replace('days', 'д')}, значения равны'
        elif data > data_old and data_old == '00:00:00':
            my_df.loc[i, z] = f'{str(data).replace('days', 'д')} в прошлом периоде {data_old}'
        elif data < data_old and data == '00:00:00':
            my_df.loc[i, z] = f'{str(data).replace('days', 'д')} в прошлом периоде {data_old}'

    elif z in ['events']:
        if int(data) > int(data_old):
            my_df.loc[i, z] = f'{data}, лучше на {int(data) - int(data_old)}'
        elif int(data) < int(data_old):
            my_df.loc[i, z] = f'{data}, хуже на {int(data_old) - int(data)}'
        elif int(data) == int(data_old):
            my_df.loc[i, z] = f'{data}, значения равны'
    return my_df

#
# print((column_names))
for i in range(report['Присоединение'].size):
    for z in column_names:
        data = report[z][i]
        data_old = report_old[z][i]
        time_delta(i, z, data, data_old)
print(my_df)
