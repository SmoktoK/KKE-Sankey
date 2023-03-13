import json
import requests
import pandas as pd
import datetime


def request_energy(channels, period, begin, end):
    if type(period) is not str:
        raise Exception(f'Period expected to be a "str" type, got {type(period)} instead')

    request = {
        "nodes": channels,
        "period": period,
        "begin": begin,
        "end": end,
    }
    return request


class EnergyArchive:

    def __init__(self, sedmax_object):
        self.host = sedmax_object.get_url()
        self.sedmax = sedmax_object

    def get_data(self, channels, period, begin, end):
        if type(channels) is not list:
            raise Exception(f'Channels expected to be a "list" type, got {type(channels)} instead')

        channels = sorted(channels)

        url = self.host + '/sedmax/energy_archive/energy/archive'
        request = request_energy(channels, period, begin, end)

        data = self.sedmax.get_data(url, request)

        df = pd.DataFrame(data['rows'])
        df.set_index('dt', inplace=True)
        df.index = pd.to_datetime(df.index)

        for i, channel in enumerate(channels):
            df[channel] = df.cells.map(lambda x: x[i]['value'])
            df[channel] = pd.to_numeric(df[channel], errors='coerce')
        df.drop('cells', axis=1, inplace=True)
        return df

    def devices_tree(self):
        url = self.host + '/sedmax/web/archive/devices_tree'
        request = {'category': 'energy'}

        data = self.sedmax.get_data(url, request)

        df = pd.DataFrame(data['treeObject'])
        return df

    def integrity(self, devices, days=1):
        if type(devices) is not list:
            raise Exception(f'Devices expected to be a "list" type, got {type(devices)} instead')

        now = datetime.datetime.now()
        past = now - datetime.timedelta(days=days)

        request = {
            "begin": past.strftime("%Y-%m-%d %H:%M:%S"),
            "end": now.strftime("%Y-%m-%d %H:%M:%S"),
            "category": "energy",
            "sort": "id",
            "period": "1h",
            "sources": devices
        }

        url = self.host + '/sedmax/web/archive/integrity'
        data = self.sedmax.get_data(url, request)

        return data


#e.get_data(["chn-3_100001_1"], 'undefined', '2021-11-29','2021-11-30')