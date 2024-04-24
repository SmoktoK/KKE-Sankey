import collections
import os
import datetime
import locale
import pathlib
import sys
import logging

import dash
import dash_bootstrap_components as dbc
import dash_treeview_antd
import pandas as pd
from dash import dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State
from dateutil.parser import parse as data_parse

from sdk import SedmaxHeader, Sedmax, ElectricalArchive, EventJournal
from uptime_report.graphs import out_time_scatter, out_table
from uptime_report.modules import pq_devices, report_by_device, report, uptime_table, empty_plot
from dotenv import load_dotenv


logging.basicConfig(level=logging.DEBUG,
                    filename='my_log.log',
                    format='%(asctime)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s',
                    datefmt='%H:%M:%S')

# locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
locale.setlocale(locale.LC_ALL, ('ru_RU', 'UTF-8'))
# locale.setlocale(locale.LC_ALL, '')
# locale.setlocale(locale.LC_ALL, 'Russian')

# Выгрузка хоста из файла конфигурации
# dotenv_path = os.path.abspath(os.curdir)
load_dotenv()


with open('host.cfg', 'r') as host:
    x = host.read()
with open('login_data.cfg', 'r') as host:
    t = host.read()
    y = t.split()


# Create a dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# app = dash.Dash(__name__, external_stylesheets=['uptime_report/assets/bootstrap.min.css'])
app.title = 'Отчёт ККЭ'
# s = Sedmax(os.getenv('HOST_NAME'))
s = Sedmax(x)

username = y[0] #os.environ['SEDMAX_USERNAME']
password = y[1] #os.environ['SEDMAX_PASSWORD']

# username = os.getenv('LOGIN')  # os.environ['SEDMAX_USERNAME']
# password = os.getenv('PASS')  # os.environ['SEDMAX_PASSWORD']
s.login(username, password)

el = ElectricalArchive(s)
j = EventJournal(s)

background_color = '#ffffff'
journal_id = 88
journal_id = 100004  # смена id журнала после обновления API
db_name = 'KKE_parameters.db'
script_path = pathlib.Path(sys.argv[0]).parent
filter_option = []
def_value = []
devs_id = {}
raw_data = pd.DataFrame([])
old_raw_data = pd.DataFrame([])
cur_start_time = ''
cur_end_time = ''
cur_selected = []


# def load_kke_parameters():
#     with closing(sqlite3.connect(script_path / db_name)) as db_conn:
#         kke_parameters = pd.read_sql('''SELECT parameters FROM Data''', db_conn)
#         # kke_parameters.set_index('parameters_id', inplace=True)
#         value = kke_parameters.values
#         # print(kke_parameters)
#         # print(value)
#         return value


def load_raw_data(start_date, end_date, selected, filtermessage):
    global filter_option
    global def_value
    global devs_id
    global raw_data
    global cur_start_time
    global cur_end_time
    global cur_selected

    # обновляем текущее время начал и конца выборки и выделенные узлы дерева
    if cur_start_time != start_date:
        cur_start_time = start_date
    if cur_end_time != end_date:
        cur_end_time = end_date
    if collections.Counter(cur_selected) != collections.Counter(selected):
        cur_selected = selected

    # Преобразовываем в формат даты и времени
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # добавляем время к дате и преобразовываем к требуемому для API запроса формату
    start_date = datetime.datetime.combine(start_date, datetime.time(00, 00, 00))
    end_date = datetime.datetime.combine(end_date, datetime.time(23, 59, 59))
    # end_date = datetime.datetime.combine(end_date, datetime.time(23, 00, 00))
    end = end_date.strftime("%Y-%m-%d %H:%M:%S")
    start = start_date.strftime("%Y-%m-%d %H:%M:%S")
    old_date = end_date - start_date
    old_start = (start_date - old_date).strftime("%Y-%m-%d %H:%M:%S")
    old_end = (start_date - datetime.timedelta(0, 1, 0)).strftime("%Y-%m-%d %H:%M:%S")
    # перечень устройств с протоколом 106 (SATEC ККЭ)
    devs = pq_devices(s, ['obj-1'], 106)
    devs = devs.rename(columns={'name': 'common-device'})
    devs_list = devs['common-device'].tolist()

    # разбор выбранных в tree устройств
    selected = [x for x in selected if x in devs_list]
    if len(selected) == 0:
        raw_data = None
        filtermessage = []
        filter_option = {}
        return None, filtermessage, filter_option
    filterdevice = []
    for i in selected:
        try:
            filterdevice.append('common-device=' + devs_id[i])
        except:
            pass

    # =Запрос журнала по выделенным устройствам за указанный период и такой-же прошлый период для сравнения=============
    df = j.get_data(journal_id, start, end, filters={'common-device': filterdevice})
    df_old = j.get_data(journal_id, old_start, old_end, filters={'common-device': filterdevice})
    # df.to_csv(r'pandas.csv', header=None, index=None, sep=' ', mode='w')
    # пагинация при выборе очень большой даты
    cur_date = pd.to_datetime(df.index[-1])
    bdf_empty = df.empty
    i = 0
    # while cur_date < end or i < 100:
    while not bdf_empty:
        cur_date = cur_date + datetime.timedelta(seconds=1)
        cur = cur_date.strftime("%Y-%m-%d %H:%M:%S")
        df1 = j.get_data(journal_id, cur, end, filters={'common-device': filterdevice})
        bdf_empty = df1.empty
        if bdf_empty == True or i > 1000:
            break
        df = pd.concat([df, df1])
        # df = df.append(df1)
        if df1.shape[0] < 100:
            break
        cur_date = pd.to_datetime(df1.index[-1])
        i += 1
    # =================================================================================

    # перечень уникальных записей журнала
    filter_option = df['common-message'].tolist()
    filter_option = list(set(filter_option))

    # проверка наличия выбранных значений фильтра в новом журнале
    if not type(filtermessage) is list:
        filtermessage = [filtermessage]
    for i in filtermessage:
        if not i in filter_option:
            filtermessage.remove(i)
    if len(filtermessage) == 0:
        filtermessage = [filter_option[0]]

    # Журнал всех событий за временной диапазон для выбранных устройств
    raw_data = df
    return df, filtermessage, filter_option, df_old


def load_data(df, start_date, end_date, selected, filtermessage, old_df):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    start_date = datetime.datetime.combine(start_date, datetime.time(00, 00, 00))
    end_date = datetime.datetime.combine(end_date, datetime.time(23, 59, 59))

    # перечень устройств с протоколом 106 (SATEC ККЭ)
    devs = pq_devices(s, ['obj-1'], 106)
    devs = devs.rename(columns={'name': 'common-device'})
    devs_list = devs['common-device'].tolist()

    # разбор выбранных в tree устройств

    selected = [x for x in selected if x in devs_list]

    try:
        if df == None or len(selected) == 0:
            return None
    except:
        pass

    if df.empty:
        EMPTY_JOURNAL = True
        cols = ['dt', 'common-class', 'common-color', 'common-device', 'common-element',
                'common-level', 'common-message', 'common-number', 'common-type',
                'pq-duration', 'pq-magnitude', 'pq-reference', 'TBF', 'end', 'date']
        df[cols] = 0
        df['common-device'] = selected
        df['TBF'] = pd.NaT
        old_df[cols] = 0
        old_df['common-device'] = selected
        old_df['TBF'] = pd.NaT

    else:
        EMPTY_JOURNAL = False
        df['common-device'] = df['common-device'].map(lambda x: x.split('/')[-1])
        old_df['common-device'] = old_df['common-device'].map(lambda x: x.split('/')[-1])
        df = df.sort_index(ascending=True)
        old_df = old_df.sort_index(ascending=True)
        # столбец с временными метками для фильтрации повторяющихся записей
        df['common-tm'] = df.index
        old_df['common-tm'] = old_df.index
        # фильтрация по имени события в журнале
        df = df.loc[df['common-message'].isin(filtermessage)]
        old_df = old_df.loc[old_df['common-message'].isin(filtermessage)]
        # фильтрация повторяющихся в журнале событий по столбцам - время, имя устройства, имя события
        df = df.drop_duplicates(subset=['common-device', 'common-tm'])
        old_df = old_df.drop_duplicates(subset=['common-device', 'common-tm'])
        # df = df.drop_duplicates(subset=['common-device', 'common-message', 'common-tm'])
        # фильтрация по выделенным в дереве устройствам
        df = df[df['common-device'].isin(selected)]
        old_df = old_df[old_df['common-device'].isin(selected)]

        if df.empty:
            EMPTY_JOURNAL = True

            # time between eventa by device
        df['TBF'] = df.reset_index().groupby('common-device')['dt'].diff().values
        old_df['TBF'] = old_df.reset_index().groupby('common-device')['dt'].diff().values
        # casting str to float
        df[['pq-duration', 'pq-magnitude', 'pq-reference']] = df[
            ['pq-duration', 'pq-magnitude', 'pq-reference']].replace("", 0).astype('float')
        old_df[['pq-duration', 'pq-magnitude', 'pq-reference']] = old_df[
            ['pq-duration', 'pq-magnitude', 'pq-reference']].replace("", 0).astype('float')
        # event_end
        df['end'] = df.index + pd.to_timedelta(df['pq-duration'], unit='s')
        old_df['end'] = old_df.index + pd.to_timedelta(old_df['pq-duration'], unit='s')
        # event_date
        df['date'] = df.index.date
        old_df['date'] = old_df.index.date

    device_report = report_by_device(df, selected, start_date, end_date, old_df)
    common_report = report(df, selected, start_date, end_date, old_df)
    table = uptime_table(df, selected, start_date, end_date, EMPTY_JOURNAL)

    return [df.reset_index().to_json(), device_report.to_json(), common_report.to_json(), table.to_json()]


def update_table(df, ccolumns=None, tablename=''):
    # df = df.reset_index()
    df = df.fillna('-').replace('NaT', '-')
    data = df.to_dict('records')
    columns = ccolumns if ccolumns is not None else [{"name": i, "id": i} for i in (df.columns)]

    return html.Div([
        html.Div(tablename, style={'font-size': '20px'}),
        dash_table.DataTable(data=data,
                             columns=columns,
                             # export_format="xlsx",
                             fill_width=False,
                             filter_action='native',
                             style_table={'border': '1px solid rgba(0,0,0,0.03)', 'height': '325px', 'overflow': 'auto',
                                          'min-width': '350px'},
                             style_cell={'font-size': 12, 'minWidth': 20, 'font-color': 'rgba(0, 0, 0, 1)',
                                         'whiteSpace': 'pre-line', 'overflow': 'hidden',
                                         'backgroundColor': "rgba(250,250,250,0.2)"},
                             style_header={'backgroundColor': "#fafafa", 'fontWeight': 'bold'},
                             style_data_conditional=[
                                 {
                                     "if": {"state": "selected"},  # 'active' | 'selected'
                                     # "backgroundColor": "rgba(0, 116, 217, 0.3)",
                                     "backgroundColor": "green",
                                     "border": "1px solid blue",
                                     "if": {"state": "active"},
                                     "font-color": "black"
                                 },
                             ]
                             )
    ], style={'margin': '1px'})


def update_tree(checked, state=False):
    global devs_id
    global cur_selected

    devs_id.clear()  # очистка словаря имен и id устройств дерева
    # device_list = s.devices_tree()
    # смена ветки API и структуры запроса/ответа в связи с обновлением
    try:
        device_list = s.get_data(s.host + '/sedmax/pq_journal_webapi/devices_tree', {})
    except:
        device_list = {'tree': [{'code': 'object-1', 'parentCode': '', 'name': 'Ошибка выгрузки', 'nodeType': 1},{'code': 'object-1005', 'name': 'ВРУ 2 этаж', 'nodeType': 1, 'parentCode': 'object-1'}]}
    device_list = pd.DataFrame(device_list['tree'])
    device_list = device_list.rename(columns={'parentCode': 'parent', 'code': 'id'})
    # device_list.to_csv('device_list.csv', index=False)

    devs = pq_devices(s, ['obj-1'], 106)
    devs = device_list
    devs = devs.rename(columns={'name': 'common-device'})
    # Сортируем фрейм по родителям
    devs = devs.sort_values('parent')

    # двухуровневая структура по дереву только до родителя
    nodes = []

    for i, row in devs.iterrows():
        # данные прибора
        node = []
        device_row = device_list[device_list['id'] == str(row['id'])]
        # device_row = device_list[device_list['id'].str.contains('device')]
        name = list(device_row['name'])  # имя устройства в дереве
        parent = list(device_row['parent'])  # имя родителя устройства в дереве
        ids = list((device_row['id']))  # id устройства в дереве
        devs_id = dict(zip(name, ids))
        # devs_id[name] = ids # словарь имен и id устройств в дереве (глобальная переменная)

        node.extend(name)

        # данные родителя прибора
        try:
            device_row = device_list[device_list['id'].isin(parent)]
            # parent_name = device_row['name'].item()
            parent_name = list(device_row['name'])
            node.extend(parent_name)
        except:
            pass
        nodes.append(node)

    # Формирование дерева устройств
    def get_children(device, parrent_id):
        cild_list = []
        df = device[device['parent'] == parrent_id]
        if not df.empty:
            for i in df.index:
                cilds = get_children(device, df.at[i, 'id'])
                dict_cild = {'title': df.at[i, 'name'], 'key': df.at[i, 'name']}
                if len(cilds) > 0:
                    dict_cild['children'] = cilds
                cild_list.append(dict_cild)
        return cild_list


    # print(devs_id)
    menu_list = get_children(device_list, '')
    keys_list = device_list['name'].unique().tolist()


    tree_menu = html.Div(dash_treeview_antd.TreeView(
        id='tree_input',
        multiple=True,
        checkable=True,
        # checked=keys_list,
        checked=checked,
        selected=[],
        expanded=keys_list,
        data={
            'title': 'Устройства ККЭ',
            'key': '0',
            'children': menu_list
        }
    ))
    if len(cur_selected) == 0:
        cur_selected = checked
    return tree_menu


# Переменная с кодом дерева
tree = update_tree([], state=False)
#
common_table = html.Div(dash_table.DataTable(
    id='common_table',
    columns=[{'id': 'index', 'name': 'Характеристка'},
             {'id': 'value', 'name': 'Значение'},
             {'id': 'index', 'name': 'Значение1'},
             {'id': 'index', 'name': 'Delta'}],
    style_cell={'font-size': 13, 'overflow': 'hidden', 'backgroundColor': "rgba(50,50,50,0.2)"},
), style={'padding': '5px'}
)
#
device_table = html.Div(dash_table.DataTable(
    id='device_table',
    columns=[{'id': 'Присоединение', 'name': 'Присоединение'},
             {'id': 'Uptime', 'name': 'Время без сбоев, ч.'},
             {'id': 'Uptime_percent', 'name': 'Время без сбоев, %'},
             {'id': 'outage_time', 'name': 'Время сбоев, ч'},
             {'id': 'outage_percent', 'name': 'Время сбоев, %'},
             {'id': 'events', 'name': 'Количество сбоев'},
             {'id': 'outage_min', 'name': 'Минимальое время сбоя, ч'},
             {'id': 'outage_max', 'name': 'Максимальное время сбоя, ч'},
             {'id': 'MTBF', 'name': 'Средняя наработка на отказ(MTBF)'},
             {'id': 'MTTR', 'name': 'Среднее время восстановления(MTTR)'},
             ],
    style_cell={'font-size': 13, 'overflow': 'hidden', 'backgroundColor': "rgba(50,50,50,0.2)"},
), style={'padding': '5px'})

# norma_style = {'background-color': '#326da8', 'margin-right': '3px', 'font-family': 'sans-serif', 'font-size': '14px'}
norma_style = {}
alarm_style = {}
# Кнопки на панели
update_button = dbc.Button("Обновить", id="update_tree", n_clicks=0,
                           className="ant-electro-btn-primary",
                           title='Обновить данные дашборда',
                           # style=norma_style
                           )
day_button = dbc.Button('День', title='Выбрать текущий день', id='day_button', className="ant-electro-btn-primary")
week_button = dbc.Button('Неделя', title='Выбрать текущую неделю', id='week_button', className="ant-electro-btn-primary")
month_button = dbc.Button('Месяц', title='Выбрать текущий месяц', id='month_button', className="ant-electro-btn-primary")


# Опции фильтрации журнала

# def_value = 'Провал напряжения'

def update_filter(filter_option, def_value):
    # values = load_kke_parameters()

    if len(filter_option) != 0:
        values = filter_option
    else:
        if not type(def_value) is list:
            values = [def_value]
        else:
            values = def_value

    # values=[['Провал напряжения'], ['Повышение напряжения'], ['Отклонение частоты'], ['Доза фликера'], ['Небаланс напряжения'], ['Гармонические искажения']]
    options = []
    for i in values:
        if type(i) is list:
            i = i[0]
        options.append({'label': i, 'value': i})
    # options = load_kke_parameters()
    filter_kke = dcc.Dropdown(
        id='filter_kke',
        options=options,
        value=def_value,
        placeholder='Не выбран ни один параметр...',
        multi=True,
        searchable=True,
        # multi=False,
        clearable=False)

    filter_content = html.Div([
        html.Div("Параметр ККЭ",
                 style={'width': '150px', 'height': '25px', 'font-size': 20, 'display': 'inline-table',
                        'margin-left': '40px', 'margin-top': '0px'}),
        html.Div(html.Div(filter_kke, style={'min-width': 'calc(100vw - 500px)'}),
                 title='Выберите контролируемый параметр качества электроэнергии',
                 style={'margin': '5px', 'font-size': 14, 'display': 'inline-table'})
    ], style={'box-shadow': '0 0 2px 2px 1px rgba(0,0,0,0.3)', 'border-radius': '2px'}
    )
    return filter_content


start_date = (datetime.datetime.now() - pd.Timedelta(days=30)).date()
end_date = datetime.datetime.now().date()

date_picker = html.Div([
    html.B('Анализ параметров ККЭ',
           style={'text-align': 'center', 'color': '#ffffff', 'font-size': 22, 'font-family': 'sans-serif',
                  'margin-left': '20px'}),
    html.Div([month_button, week_button, day_button, update_button,
              dcc.DatePickerRange(
                  id='date-picker-range',
                  # initial_visible_month=(datetime.datetime.now() - pd.Timedelta(days=30)).date(),
                  initial_visible_month=datetime.datetime.now().date(),
                  start_date=start_date,
                  end_date=end_date,
                  # min_date_allowed=(datetime.datetime.now() - pd.Timedelta(days=365)).date(),
                  min_date_allowed=(datetime.datetime.now() - pd.Timedelta(days=730)).date(),
                  max_date_allowed=datetime.datetime.now().date(),
                  # number_of_months_shown=2,
                  # month_format='MMMM YYYY',
                  # display_format='DD MMMM YYYY',
              )], title='Выберите период отчёта',
             style={'float': 'right', 'padding': '1px', 'margin': '0px 0px 0px 0px'}),

    # html.Div(
    #     [
    #         day_button
    #     ], style={'float': 'right', 'padding': '1px', 'margin': '0px 0px 0px 0px'}),
    # html.Div(
    #     [
    #         week_button
    #     ], style={'float': 'right', 'padding': '1px', 'margin': '0px 0px 0px 0px'}),
    # html.Div(
    #     [
    #         month_button
    #     ], style={'float': 'right', 'padding': '1px', 'margin': '0px 0px 0px 0px'}),

], style={'margin': '1px 0px 0px 0px', 'padding': '0px', 'backgroundColor': "grey",
          'box-shadow': '0 0 2px 2px rgba(0,0,0,0.3)'}
)

tables_content = dbc.Container(
    # dcc.Loading(type="circle",
    children=[
        dbc.Row([
            dbc.Col(html.Div(id="common_table"), width=3,
                    style={'padding': '5px', 'display': 'inline-table', 'backgroundColor': "transparent"
                           }),

            dbc.Col(html.Div(id="device_table"), width=9,
                    style={'padding': '5px', 'display': 'inline-table', 'backgroundColor': "transparent"
                           }),
        ], style={'padding': '5px', 'flex-flow': 'row no wrap'}),
        dbc.Row([
            dbc.Col(html.Div(
                dcc.Graph(id='out_table', animate=False,
                          config={'displayModeBar': False, 'locale': 'ru', 'staticPlot': True}),
                style={'height': '350px', 'overflow': 'auto'}),
                width=12),
        ], style={'padding': '5px', 'flex-flow': 'row nowrap', 'backgroundColor': "transparent"}),
    ]
    # )
    , fluid=True, style={'background-color': background_color})

graphs_content = dbc.Container(children=[
    dbc.Row(
        # dcc.Loading(type="circle",
        children=[
            dcc.Graph(id='out_time_scatter', animate=False,
                      config={'displaylogo': False, 'locale': 'ru'})
            # )
        ], style={'padding': '5px'})
], fluid=True, style={'background-color': background_color})

tabs = [html.Div(dbc.Tabs(
    [
        dbc.Tab(html.Div(tables_content,
                         style={'overflowY': 'auto', 'height': 'calc(100vh - 230px)'}
                         ), label="Таблицы", tab_id="tables", tab_style={"marginLeft": "auto"}),
        dbc.Tab(html.Div(graphs_content,
                         style={'overflowY': 'auto', 'height': 'calc(100vh - 230px)'}
                         ), label="Графики", tab_id="graphs")
    ],
    id="tabs",
    active_tab="tables",
    style={'margin': '5px 20px 5px 20px'}
),
    style={'height': 'calc(100vh - 200px)'}
),
    html.Div(id="content")]

filter_content = update_filter(filter_option, def_value)

# Create an app layout
app.layout = html.Div(children=[
    dcc.Store(id='memory-output'),
    dbc.Row([SedmaxHeader(title='', logo='sedmax')]),
    dbc.Row([date_picker], style={'background-color': background_color}),
    html.Div(children=[
        dbc.Row([
            dbc.Col(html.Div(html.Div(id='tree', children=[tree]),
                             style={'overflowY': 'auto', 'height': 'calc(100vh - 120px)'}),
                    style={'width': '250px', 'border-radius': '2px', 'box-shadow': '0 1px 4px 1px rgba(0,0,0,0.2)',
                           'margin': '2px 0px 2px 5px', 'padding': '5px'}),
            dbc.Col(dcc.Loading(type="circle", children=[html.Div([
                html.Div(id='filter_content', children=[filter_content],
                         style={'margin': '2px', 'padding': '5px', 'box-shadow': '0 1px 4px 1px rgba(0,0,0,0.2)',
                                'border-radius': '2px'}),

                html.Div(tabs,
                         style={'height': 'calc(100vh - 167px)', 'min-width': 'calc(100% - 250px)',
                                'padding': '5px', 'margin': '2px',
                                'box-shadow': '0 1px 4px 1px rgba(0,0,0,0.2)', 'border-radius': '2px'}),
            ], style={'min-width': '400px'})
            ]), style={'min-width': 'calc(100% - 250px)', 'margin-left': '0px'})
        ], style={'min-height': '200px', 'flex-flow': 'row nowrap'})
    ], style={'width': '100%', 'z-index': '0', 'hight': 'calc(100% - 100px)'})
], style={'width': '100%', 'z-index': '0'})


# Колбеки кнопок выбора дня/недели/месяца
@app.callback(
    [Output("date-picker-range", "start_date"),
     Output("date-picker-range", "end_date"),
     Output("update_tree", "n_clicks")],
    [Input("day_button", 'n_clicks'),
     Input("week_button", 'n_clicks'),
     Input("month_button", 'n_clicks')]

)
def on_button_click(n_day, n_week, n_month):    # Фильтрация по горячим кнопкам
    end_date = datetime.datetime.now().date()
    ctx = callback_context.triggered[0]['prop_id']
    if ctx == '.':
        delta = 30
        n = 1
    else:
        delta = 0
        if 'day_button' in ctx:
            delta = 1
            n = n_day
        elif 'week_button' in ctx:
            delta = 6
            n = n_week
        elif 'month_button' in ctx:
            delta = 30
            n = n_month
        # start_date = (datetime.datetime.now() - pd.Timedelta(days=delta)).date()
    start_date= (datetime.datetime.now() - pd.Timedelta(days=delta)).date()
    return start_date, end_date, n


@app.callback(Output(component_id='tree', component_property='children'),
              [Input("update_tree", "n_clicks"),
               # State(component_id='filter_kke', component_property='value'),
               State('tree_input', 'checked')], prevent_initial_call=True)
def update(n, checked):
    tree = update_tree(checked, state=True)
    return tree


@app.callback(Output(component_id='filter_content', component_property='children'),
              [State('date-picker-range', 'start_date'),
               State('date-picker-range', 'end_date'),
               State('tree_input', 'checked'),
               Input("update_tree", "n_clicks"),
               State(component_id='filter_kke', component_property='value')]
              )
def update_raw_data(start_date, end_date, selected, n, filtername):
    global raw_data, old_raw_data
    # b_click_count = n - 1
    # print('Callback #2' + ', n=' + str(n) + ', click_count=' + str(b_click_count))
    raw_data, def_value, filter_option, old_raw_data = load_raw_data(start_date, end_date, selected, filtername)
    filter_content = update_filter(filter_option, def_value)
    return filter_content


@app.callback(Output(component_id='memory-output', component_property='data'),
              [State('date-picker-range', 'start_date'),
               State('date-picker-range', 'end_date'),
               State('tree_input', 'checked'),
               Input("update_tree", "n_clicks"),
               Input(component_id='filter_kke', component_property='value')],
              prevent_initial_call=True
              )
def update_global_var(start_date, end_date, selected, n, filtername):
    df = load_data(raw_data, start_date, end_date, selected, filtername,old_raw_data)
    return df


@app.callback(Output(component_id='update_tree', component_property='className'),
              [Input('date-picker-range', 'start_date'),
               Input('date-picker-range', 'end_date'),
               Input('tree_input', 'checked'),
               Input("update_tree", "n_clicks"),
               ]
              )
def update_button_style(start_date, end_date, selected, n):
    global cur_start_time
    global cur_end_time
    global cur_selected

    if collections.Counter(cur_selected) != collections.Counter(
            selected) or cur_start_time != start_date or cur_end_time != end_date:
        if cur_selected == []:
            cur_selected = selected
        return "ant-electro-btn-primary_alarm"
    else:
        return "ant-electro-btn-primary"


@app.callback(
    [Output(component_id='common_table', component_property='children'),
     Output(component_id='device_table', component_property='children'),
     Output(component_id='out_table', component_property='figure'),
     ],
    [Input(component_id='memory-output', component_property='data')]
)
def show_report(data):
    if type(data) is list:
        # графики
        df = pd.read_json(data[0]).set_index('dt')
        df.index = pd.to_datetime(df.index, unit='ms')
        table = pd.read_json(data[3])

        heatmap = out_table(table)

        # таблицы
        columns = [{'id': 'Присоединение', 'name': 'Наименование устройства'},
                   {'id': 'Uptime', 'name': 'Время без сбоев'},
                   {'id': 'Uptime_percent', 'name': 'Время без сбоев, %'},
                   {'id': 'outage_time', 'name': 'Время сбоев'},
                   {'id': 'outage_percent', 'name': 'Время сбоев, %'},
                   {'id': 'events', 'name': 'Количество событий'},
                   {'id': 'outage_min', 'name': 'Минимальное время сбоя'},
                   {'id': 'outage_max', 'name': 'Максимальное время сбоя'},
                   {'id': 'MTBF', 'name': 'Средняя наработка на отказ (MTBF)'},
                   {'id': 'MTTR', 'name': 'Среднее время восстановления (MTTR)'},
                   ]

        device_report = update_table(pd.read_json(data[1]), columns, "Данные по устройствам")

        columns = [{'id': 'Характеристика', 'name': 'Характеристка'},
                   {'id': 'Значение', 'name': 'Значения текущие'},
                   {'id': 'Значение1', 'name': 'Значения за прошедший период'},
                   {'id': 'Delta', 'name': 'Сравнение результатов текущего и прошлого периодов'}]
        common_report = update_table(pd.read_json(data[2]), columns, "Общие данные")

        return [common_report, device_report, heatmap]
    else:
        return [html.Div(), html.Div(), empty_plot()]


@app.callback(
    [
        Output(component_id='out_time_scatter', component_property='figure'),
    ],
    [Input(component_id='memory-output', component_property='data')],
)
def show_report(data):
    if type(data) is list:
        # графики
        df = pd.read_json(data[0]).set_index('dt')
        df.index = pd.to_datetime(df.index, unit='ms')

        if df['pq-duration'].notnull().values.any():
            scatter = out_time_scatter(df)
        else:
            scatter = empty_plot()
    else:
        scatter = empty_plot()
    return [scatter]
