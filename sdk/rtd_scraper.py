import json
import requests
import pandas as pd
import datetime


def request_rtd(channels, limit, begin, end, tree_type, offset):
    if type(channels) is not list:
        raise Exception(f'Channels expected to be a "list" type, got {type(channels)} instead')
    if type(limit) is not int:
        raise Exception(f'Limit expected to be a "int" type, got {type(limit)} instead')

    request = {
        "nodes": channels,
        "limit": limit,
        "begin": begin,
        "end": end,
        "treeType": tree_type,
        "offset": offset
    }
    return request


class RTDArchive:

    def __init__(self, sedmax_object):
        self.host = sedmax_object.get_url()
        self.sedmax = sedmax_object

    def get_data(self, channels, period, begin, end, tree_type=1, offset=0):
        if type(channels) is not list:
            raise Exception(f'Channels expected to be a "list" type, got {type(channels)} instead')

        channels = sorted(channels)

        url = self.host + '/sedmax/web/rtd_analysis/archive/select'
        request = request_rtd(channels, period, begin, end, tree_type, offset)

        data = self.sedmax.get_data(url, request)

        df = pd.DataFrame(data['archive'])
        df['ts'] = pd.to_datetime(df.ts, unit='ms') + pd.Timedelta(3, unit='h')
        df = df.rename(columns={'ts': 'dt'})
        df.set_index('dt', inplace=True)

        return df


#r.get_data(["par-1001"], 720, '2021-12-03 13:00:00','2021-12-03 16:00:00')