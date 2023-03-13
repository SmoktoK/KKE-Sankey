import pandas as pd
import numpy as np
import requests
import json
import csv

host = 'http://demo.sedmax.ru'


def login(username, password):
    r = requests.post(
        host + '/sedmax/auth/login',
        data=json.dumps({'Login': username, 'Password': password})
    )
    if r.status_code == 200:
        token = r.cookies.get_dict()["jwt"]
        username = username
        password = password
        print('Token get successful!')
        return token
    else:
        raise Exception(f'Status code: {r.status_code}. {r.json()["message"]}')


def get_data(token, url, request):
    r = requests.post(
        url,
        json=request,
        cookies={'jwt': token}
    )

    if r.status_code == 200:
        return r.json()
    elif r.status_code == 401 or r.status_code == 403:
        print(r.status_code)


def get_archive(token):
    url = host + '/sedmax/pq_journal_webapi/devices_tree'
    request = {}
    r = get_data(token, url, request)
    # np.savetxt('data_np.csv', r, delimiter=' ', fmt='%s')
    # with open('data.csv', 'a') as file:
    #     writer = csv.writer(file)
    #     writer.writerow(r)





token = login('demo', 'demo')

get_archive(token)
