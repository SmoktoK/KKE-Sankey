import json
import requests
import pandas as pd
import datetime


def request_event(ID, begin, end, limit, filters):
    if type(ID) is not int:
        raise Exception(f'Channels expected to be a "int" type, got {type(ID)} instead')

    sessionFilters = True if filters != {} else False

    # request = {
    #     "filters": filters,
    #     "sessionFilters": sessionFilters,
    #     "limit": limit,
    #     "configurationId": ID,
    #     "begin": begin,
    #     "end": end,
    # }

    request = {
        "begin": begin,
        "configurationId": ID,
        "end": end,
        "filters": {},
        "limit": limit,
        "sessionFilters": sessionFilters,
        "sort": []
    }
    return request


class EventJournal:

    def __init__(self, sedmax_object):
        self.host = sedmax_object.get_url()
        self.sedmax = sedmax_object

    def get_data(self, ID, begin, end, limit=1000, filters={}):
        url = self.host + '/sedmax/common_event_journal/archive/select'
        # url = self.host + '/sedmax/archive_webapi/energy/data/'
        request = request_event(ID, begin, end, limit, filters)

        data = self.sedmax.get_data(url, request)
        df = pd.DataFrame(data['events'])
        # if response data is empty
        if len(data['events']) == 0:
            return df

        df['dt'] = pd.to_datetime(df['common-tm'])
        df = df.set_index('dt').drop('common-tm', axis=1)

        return df

#j.get_data(88, '2021-11-05 00:00:00','2021-12-05 23:00:00', filters = {'common-message': ['провал']} )
#df['MTBF'] = df.groupby('common-device')['common-tm'].diff()