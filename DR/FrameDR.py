import pandas as pd
import os
import numpy as np
import datetime
from DR.DataDR import power_chart_rtd, power_bar
import dash
from dash import dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from sdk import SedmaxHeader, Sedmax, EnergyArchive, ElectricalArchive, RTDArchive # для коретного импорта sdk
# вызов app  находиться в sedmax-sdk\mainDR.py в одном катологе с sdk
# from graphs import electro_chart, electro_bar, heat_chart, heat_bar
### Подготовка данных для графиков
#Создание датафрема со значением ДГ для вывода на графике
#структура датафрейма:
#Day_Power_Set(
#                  ["power_set"]  столбец с часовыми значениями мощности - суточная завка предприятия на потребление мощности
#                  ["time"] столбец с временной меткой часовых заявок, мощность указана на конец часа, формат datetime
#                  ["hour"] столбец с указанием часа для вывода в дропбокс
#                  ['установленная мощность'] - установленная мощьнность с учетом условия команды по снижению мощности (DR)
#                  ['power'] - мощность потребления предприятия на конец часа
#
Day_Power_Set = pd.DataFrame({"power_set": np.random.randint(30, 100, 24)}) # заполнение рандомными значениями от 30 до 100, всего 24 значения
#Добавление в ДФ столбца с типом данных timestamp (временная метка каждого часа потребляемой мощности на графике), изменение значения timstapm происходит с помощью функции
# date_range - генерирует список элементов с типам данных timestamp/ аргумент start начало генерации, periods - количество элементов списка, freq='H' - строковый указатель на велечину интервала
# функция combine - позволяет сгенерировать значение типа timestamp из пары значений типа date и time/
# в качестве первого аргумента используеться текущее значение timestamp, вторым - значение типа time
Day_Power_Set["time"]= pd.date_range(start=datetime.datetime.combine(datetime.datetime.today(), datetime.time(hour =1, minute= 0)), periods=len(Day_Power_Set), freq='H')

# !! пока в ДФ добавлю сталбец time, возможно дале имеет смысл настроить коректное отображение  timestamp
Day_Power_Set["hour"]=datetime.time(hour =0, minute= 0)
# в пользовательском интерфейсе избыточно указание полного формата  timestamp
# добавление в ДФ Day_Power_Set столбца со значением типа time
# ! имеет смысл описать функцией или найти  Стандартный генерации списка значений  типа time  с произвольным диапазоном
for i in range(1,len(Day_Power_Set)): # Генератор списка часовых значений для мощности из ДФ Day_Power_Set
    # FOR работает в питоне только с итерационными объектами. т.е i в каждом последующем цикле примет следующее значение из списка, сгенерированного range
    # ! в место len(Day_Power_Set) следует както применить список индексов Day_Power_Set
    # в каждую строку, с позиционным индексом i(i-го значения списка range),  столбца  "hour" ДФа будет присвоено значение часа. равного i-му значению списка range
  Day_Power_Set["hour"].iloc[i-1] = datetime.time(hour =i, minute= 0).strftime(('%H : %M'))
Day_Power_Set["hour"].iloc[23] = datetime.time(hour =0, minute= 0).strftime(('%H : %M'))

#Генерация списка диспетчерских команд для вывода на экран
DC= pd.DataFrame({'Время начала': [datetime.datetime.combine(datetime.datetime.today(), datetime.time(hour =12, minute= 0)),'','',''], # список диспетчерских команд
                 'Время окончания':  [datetime.datetime.combine(datetime.datetime.today(), datetime.time(hour =16, minute= 0)),'','',''],
                 'Снижение': [20,'','','']}, index =[1,2,3,4])
DC.index.name='№'
DC['Время начала'].iloc[1:]=''
DC['Время окончания'].iloc[1:]=''
#
# Генерация списка исполнения диспетчерской команды
X = pd.DataFrame()# переменная буфер для формаирования выходного списка
DR = pd.DataFrame() # переменная для вывода в таблицу 'Исполнение за текущие сутки'
for i in DC.index:
    try:
        X['time'] = pd.date_range(start=DC['Время начала'][i], end=DC['Время окончания'][i], freq='H')
        # создаётся перечень из часовых значений, соотвесвующих периоду выполнения сброса мощности DR
        # 'time' используеться для генерации занчений активной мощности
        X['установленная мощность']=DC['Снижение'][i] # заполняю в часовые периоды целевое значение мощности
    #  print( i )
    except:
    #    print(i)
        continue
    else:
        DR = pd.concat([DR, X], axis=0)
#
DR=DR.astype({'установленная мощность': np.float64})

# Генерация графика с учетом  команды DR
Day_Power_Set['установленная мощность']=Day_Power_Set['power_set']
mask=Day_Power_Set['time'].isin(DR['time'])
Day_Power_Set.loc[mask,'установленная мощность']=[i for i in DR['установленная мощность']]
#
# генерация значений мощности для вывода на график
Day_Power_Set['power']=Day_Power_Set['установленная мощность']-np.random.randint(-5, 5, 24)
# генерация отклонения графика мощбности от ДГ
Day_Power_Set['err']=Day_Power_Set['установленная мощность']-Day_Power_Set['power']
# генерация отклонения для вывода в таблицу 'Исполнение за текущие сутки'
DR['отклонение']=[i for i in Day_Power_Set.loc[mask,'err']]
DR=DR.drop(0)# удаление нулевой строки,

avalibel_hour = Day_Power_Set["hour"]
def now (list_hour):
  return list_hour[datetime.datetime.now().hour]

dataSet= Day_Power_Set # переменная используеться для передачи данных  графиков
# добавляю атрибуты Min, Max для маштабирования шкалы у графиков
dataSet.Min= 0
dataSet.Max= 200

#авторизация
s = Sedmax('https://sdk.sedmax.ru')

username = os.environ['SEDMAX_USERNAME']
password = os.environ['SEDMAX_PASSWORD']
s.login(username, password)
# классы для доступа к данным сервера Sedmax

el = ElectricalArchive(s)
r = RTDArchive(s)
time_now = datetime.datetime.now()
#Time используеться как указатель на время при запросе данных

Time_of_ReadRTD = datetime.datetime.combine(time_now.date(), datetime.time(00, 00, 00))
#Time используеться как указатель на время при запросе архивных данных

Time_of_ReadHist = datetime.datetime.combine(time_now.date(), datetime.time(00, 00, 00))

#   функция для записи данных ртд в датафрейм из sedmax
def Read_RTD (begin, end):

    df = r.get_data(['par-2001'], 10, begin.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S"))
    df = df.rename(columns= {'par-2001-value': 'power'})
    df = df.filter(['power']) #удаляем лишнее в ответе
    df = df.groupby(df.index.ceil(freq='S')).mean() # групируем временной ряд с точностью до секунд
    df['hour'] = df.index.ceil(freq='h')
    df = df.iloc[0 : -1] # фильтруеться посследняя строка, при дальнейшей склейки во времееной ряд исключаються поторяющиеся индексы
    return df

# rtd_power используеться как переменная с графиком активной мощности
power_rtd = pd.DataFrame()

# инициализация переменной rtd_power не нулевыми значениями
begin = Time_of_ReadRTD
power_rtd = Read_RTD(begin, time_now)
# сдвиг указателя на время выведенное на график ртд
Time_of_ReadRTD = time_now

# power_set используеться как переменная с графиками плановой мощности
power_set = pd.DataFrame()
# инициализация переменной power_set не нулевыми значениями

# power_hist используеться как переменная для таблици с исполнением
power_hist = pd.DataFrame()

#забрать архивные данные каналов заявки и DR
def Load_Archive():
    today = Time_of_ReadRTD.strftime("%Y-%m-%d")
    data = el.get_data(["dev-5_pa_imp", "dev-6_pa_imp"], ['30min'], today, today)
    data = data.rename(columns={"dev-5_pa_imp": 'Заявка', "dev-6_pa_imp": 'DR'})
    data = data.reset_index().groupby(data.index.ceil(freq='h')).mean()
    data.loc[data['Заявка'] != data['DR'], 'command'] = 1
    data = data.fillna(0)
    return data.to_json()



# сейчас в Load_Data выгружаеться архим и ртд, но поскольку временные интервалы разные необходимо разделить запросы в разные функции
def Load_Data_rtd (n):
    # использую функцию как процедуру обновляя указатель Time, и временной ряд power_rtd
    # в power_rtd должен быть сформированн весь временной ряд мощности за сутки
    # запрос в sedmax формируеться в первый вызов с начала суток до времени вызова (при инициализации), в последующиие с временем предидущего
    # до текущего .
    # !! возможно иммет смылс добавить глобальный буфер для дельты временного ряда последующих запросов и реализовать отдельный класс
    global Time_of_ReadRTD
    global power_rtd
    time_now = datetime.datetime.now()

    if time_now.date()>Time_of_ReadRTD.date():
        begin = datetime.datetime.combine(time_now.date(), datetime.time(00, 00, 00))
        power_rtd = Read_RTD(begin, time_now)
    else:
        df2 = Read_RTD(Time_of_ReadRTD, time_now)
        power_rtd = pd.concat([power_rtd, df2], axis=0)

    #begin = Time
    # запрос из седмакс в df1 работает но нет данных ручного ввода
    #end = datetime.datetime.combine(time_now.date(), datetime.time(23, 59, 59))
    #df1 = el.get_data(['bg-1'], ['30min'], begin.strftime("%Y-%m-%d"),
    #                  end.strftime("%Y-%m-%d"), multiplier=1)
    #df1 = df1.rename(columns={'bg-1': 'power'},)

    # некоректно, но работает, нужен сдвиг на время последних данных полученного ответа, при правельном ответе
    Time_of_ReadRTD = time_now  # сдвиг указателя на время последних запрошенных данных
    #df2 = df2.drop(['par-2001-max', 'par-2001-min', 'par-2001-status', 'par-2001-isBound'])
    #df3 = df2.groupby(df2.index.ceil(freq='S')).mean()

    #if n<1 :
       #print(df2.power)
    return #[power_rtd.to_json()] # не используеться, заменил вывод на график через глобальную переменную,
# необходимо исправить вывод, процедуру заменить на функцию, объедение полученного среза с временным рядом вынести из функции.

def Load_Data_hist (listofData, ListofTimer, end_time):
    # использую функцию как процедуру обновляя указатель Time, и временной ряд power_set
    # в power_set должен быть сформированн весь временной ряд мощности за сутки
    # запрос в sedmax формируеться в первый вызов с начала суток до времени вызова (при инициализации), в последующиие с временем предидущего
    # до текущего .
    # !! возможно иммет смылс добавить глобальный буфер для дельты временного ряда последующих запросов и реализовать отдельный класс
    global Time_of_ReadHist
    global power_set
    time_now = datetime.datetime.now()
    #begin = Time
    # запрос из седмакс в df1 работает но нет данных ручного ввода
    end = datetime.datetime.combine(time_now.date(), datetime.time(23, 59, 59))
    #df1 = el.get_data(['bg-1'], ['30min'], begin.strftime("%Y-%m-%d"),
    #                  end.strftime("%Y-%m-%d"), multiplier=1)
    #df1 = df1.rename(columns={'bg-1': 'power'},)

    df2 = Read_Hist(Time_of_ReadHist, end )
    # сдвиг указателя на время последних запрошенных данных
    #Time_of_ReadRTD = time_now
    #df2 = df2.drop(['par-2001-max', 'par-2001-min', 'par-2001-status', 'par-2001-isBound'])
    #df3 = df2.groupby(df2.index.ceil(freq='S')).mean()
    power_rtd = pd.concat([power_rtd, df2], axis=0)
    #if n<1 :
       #print(df2.power)
    return #[power_rtd.to_json()] # не используеться, заменил вывод на график через глобальную переменную power_rtd
# Create a dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])


#modal со всплывающей таблицей
modal = html.Div(
    [
        dbc.Button("Исполнение за текущие сутки", id="open-centered", style={'backgroundColor': "rgba(50,50,50,0.2)"}),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Исполнение за текущие сутки"), close_button=True),
                dbc.ModalBody(
                html.Div(id="modal_table", style={'padding': '5px', 'backgroundColor': '#5f8dab'})
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        "Закрыть",
                        id="close-centered",
                        className="ms-auto",
                        n_clicks=0,
                    )
                ),
            ],
            id="modal-centered",
            centered=True,
            is_open=False,
        ),
    ]
)

# Create an app layout
body = dbc.Container([
    dcc.Store(id='memory-output'),

    dcc.Interval(
        id='interval-component',
        interval=5*1000, # 5 seconds in milliseconds
        n_intervals=0),

    html.Br(), #дополнительный отступ
    dbc.Row([ #2-я строка страницы содержащая:
        dbc.Col(dcc.Graph(id='chart', animate=True, config= {'displaylogo': False}), width=9), # 1-ю колонку с графиком мощности
        dbc.Col([
            #dbc.Label('Целевое значение мощности на текущий час', style={'textAlign': 'center', 'color': 'rgba(241,241,241,0.8)', 'font-size': 20, }),
            dcc.Graph(id='target_electro', animate=True, config= {'displayModeBar': False})], width=3),# 2-ю колонку с графиком текущих значений
        # width задаёт соотношение размеров ширины графиков расположенных в строке (1,2-й график)
        ], style = {'display':'flex', 'flex-flow': 'row nowrap'}
    ),
    html.Br(),#дополнительный отступ
    dbc.Row([#3-я строка страницы содержащая:
        dbc.Col([ #1-ю колонку с таблицей 'Диспетчерские команды'
            dbc.Label('Диспетчерские команды', style={'textAlign': 'center', 'color': 'rgba(241,241,241,0.8)', 'font-size': 20, }),
            html.Div(id="commands", style={'padding': '5px'}),
        ]),
        dbc.Col([ #2-ю колонку с таблицей 'Исполнение за текущие сутки'
            #dbc.Label('Исполнение за текущие сутки',style={'textAlign': 'center', 'color': 'rgba(241,241,241,0.8)','font-size': 20, }),
            modal,
            html.Div(id="day_performance", style={'padding': '5px'}),
        ]),
        dbc.Col([ #3-ю колонку с таблицей 'Получено от реализации услуги, тыс. руб'
            dbc.Label('Получено от реализации услуги, тыс. руб',
                      style={'textAlign': 'center', 'color': 'rgba(241,241,241,0.8)',
                             'font-size': 20, }),
            html.Div(id="profit", style={'padding': '5px'}),
        ]),
    ], style = {'display':'flex', 'flex-flow': 'row nowrap', 'padding': '5px', 'backgroundColor': "rgba(50,50,50,0.2)"}),

    #     dbc.Row([
    #         dbc.Col(dcc.Graph(id='heat_chart'), width=10),
    #         dbc.Col(dcc.Graph(id='target_heat'), width=2),
    #     ], style={'display': 'flex', 'flex-flow': 'row nowrap'}),

    html.Br(),

    ], fluid=True, style = {'background-color': '#5f8dab'})



app.layout = html.Div(children=[
    SedmaxHeader(title='Панель управления Demand Response предприятия'),# SedmaxHeader имеет ссылку на лого :
    #assets/{logo}.png каталог assets/ должен находиться в папке с FrameDR
    body
])

def update_table(df):
    df = df.reset_index()
    data = df.to_dict('records')
    columns = [{"name": i, "id": i, } for i in (df.columns)]
    return dash_table.DataTable(data=data, columns=columns,
                style_cell={'font-size': 13, 'overflow': 'hidden', 'backgroundColor': "rgba(50,50,50,0.2)"},
                style_data_conditional=[
                                    {
                                        "if": {"state": "selected"},  # 'active' | 'selected'
                                        "backgroundColor": "rgba(0, 116, 217, 0.3)",
                                        "border": "1px solid blue",
                                    },
                                ]
                                )


@app.callback(Output(component_id='memory-output', component_property='data'),
              Input(component_id='interval-component', component_property='n_intervals'),
              )
def RealTimeData (n):
    Load_Data_rtd(n)
    return Load_Archive()

@app.callback(
    Output(component_id='chart', component_property='figure'),
    [Input(component_id='memory-output', component_property='data'),
     Input(component_id='interval-component', component_property='n_intervals')]
 )
def chart_rtd(data, n):
    #power_rtd= pd.read_json(data[1])

    data = pd.read_json(data)
    error = power_rtd.merge(data, left_on='hour', right_index=True)[['power', 'DR']]
    error = np.round(100*(error['power'] - error['DR'])/error['DR'], 2)

    fig = power_chart_rtd(data, power_rtd, error)

    return fig

#@app.callback(
#    Output(component_id='chart', component_property='figure'),
#    Input(component_id='dropdown', component_property='value')
# )
#def chart(time):
#    fig = power_chart(dataSet, time)
#    return fig

@app.callback(
    [Output(component_id='target_electro', component_property='figure'),
    Output(component_id='commands', component_property='children'),
     Output(component_id='day_performance', component_property='children'),
     Output(component_id='profit', component_property='children'),
     Output(component_id='modal_table', component_property='children')],
    [Input(component_id='memory-output', component_property='data'),
     Input(component_id='interval-component', component_property='n_intervals')]
 )
def bar(data, n):
    data = pd.read_json(data)
    fig = power_bar(data, power_rtd.tail(1))

    #таблицы команды, исполнение, реализация

    #исполнение
    hour_power = power_rtd.groupby('hour').mean()
    hour_power = hour_power.reset_index().merge(data, left_on='hour', right_index=True).set_index('hour').sort_index(ascending=False)
    hour_power.index = hour_power.index.strftime("%Y-%m-%d %H:%M:%S")
    hour_power['Отклонение, %'] = np.round(100*(hour_power['power'] - hour_power['DR'])/hour_power['DR'], 2)
    hour_power = np.round(hour_power[['power', 'DR', 'Отклонение, %']], 2)
    perform_table = update_table(hour_power.head(4))

    # команды
    start = data[data.command==1].reset_index().groupby('DR')['index'].min()
    end = data[data.command == 1].reset_index().groupby('DR')['index'].max() + pd.to_timedelta(1, unit='h')

    starts = []
    ends = []
    power_commands=[]
    plan = []
    for i in range(len(start)):
        starts.append(start.iloc[i].strftime("%Y-%m-%d %H:%M:%S"))
        ends.append(end.iloc[i].strftime("%Y-%m-%d %H:%M:%S"))
        record = data[data.index == start.iloc[i]]
        power_commands.append(record['DR'] - record['Заявка'])
        plan.append(record['Заявка'])

    commands = pd.DataFrame({'Время начала': starts,
                             'Время окончания': ends, 'Заявка': plan,'Снижение': power_commands})

    for i in range(4-len(commands)):
        commands = commands.append(pd.Series(dtype='object'), ignore_index=True)

    commands_table = update_table(commands.fillna(' ').set_index('Время начала'))

    #таблица с прибылью
    profit = commands.merge(hour_power, left_on='Время начала', right_index=True)
    profit = profit[profit['Отклонение, %'] > 0]
    profit['coef'] = (pd.to_datetime(profit['Время окончания']) - pd.to_datetime(profit['Время начала'])) / pd.to_timedelta(4, unit='h')
    profit['Выручка'] = (550 * (1/30) * profit['coef'] * (abs(profit['Снижение']))).astype('float').round(3)
    profit['Выполнение, %'] = (100*(profit['Заявка'] - profit['power']) / -profit['Снижение']).astype('float').round(2)
    profit = profit[profit['Время окончания'] < datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]

    for i in range(4-len(profit)):
        profit = profit.append(pd.Series(dtype='object'), ignore_index=True)

    profit = update_table(profit[['Время начала', 'Время окончания', 'Выполнение, %', 'Выручка']].set_index('Время начала'))

    # таблица в Modal
    modal_table = update_table(hour_power)

    return [fig, commands_table, perform_table, profit,modal_table]

#открытие-закрытие modal
@app.callback(
    Output("modal-centered", "is_open"),
    [Input("open-centered", "n_clicks"), Input("close-centered", "n_clicks")],
    [State("modal-centered", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


#@app.callback(
#    Output(component_id='heat_chart', component_property='figure'),
#    Input(component_id='dropdown', component_property='value')
# )
#def chart(time):
#    fig = heat_chart(data, time)
#    return fig

#@app.callback(
#    Output(component_id='target_heat', component_property='figure'),
#    Input(component_id='dropdown', component_property='value')
# )
#def bar(time):
#    fig = heat_bar(data, time)
#    return fig