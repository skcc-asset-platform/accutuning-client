import asyncio
from json.decoder import JSONDecodeError
import requests
import json


class GraphQL:
    _endpoint_url = ''
    _header = {'refresh-token': ''}

    def __init__(self, endpoint_url):
        self._endpoint_url = endpoint_url

    def add_login_info(self, token):
        self._header['Authorization'] = f'Bearer {token}'
        print(f'Header:{self._header}')

    async def execute_async(self, query, param={}):
        from gql import Client, gql
        from gql.transport.aiohttp import AIOHTTPTransport

        transport = AIOHTTPTransport(url=self._endpoint_url, headers=self._header)

        # Using `async with` on the client will start a connection on the transport
        # and provide a `session` variable to execute queries on this connection
        async with Client(
            transport=transport, fetch_schema_from_transport=True,
        ) as session:
            result = await session.execute(gql(query), variable_values=param)
            return result

    def execute(self, query, param={}):
        return asyncio.run(self.execute_async(query, param))


# REST는 이렇게 씌울 필요가 있을까, 그냥 requests에서 바로 가져다 쓰는 것은...
class REST:
    _header = {'Accept': 'application/json', 'Content-Type': 'application/json;charset=UTF-8'}

    def __init__(self, api_url):
        self._api_url = api_url

    def add_login_info(self, token):
        self._header['Authorization'] = f'JWT {token}'

    def get(self, url):
        res = requests.get(self._api_url + url, headers=self._header)
        if res.status_code == 200:
            obj = json.loads(res.text)
            return obj
        else:
            return ''  # TODO 에러 발생시켜야 함

    def post(self, url, param):
        res = requests.post(self._api_url + url, data=param)
        if res.status_code == 200:
            obj = ''
            try:
                obj = json.loads(res.text)
            except JSONDecodeError:
                obj = ''
            return obj
        else:
            print(res.text)
            return res.status_code

    def filepost(self, url, filepath, param={}):
        from pathlib import Path
        filename = Path(filepath).name

        result = ''
        with open(filepath, 'rb') as f:
            res = requests.post(self._api_url + url, files={'fileData': (filename, f, 'text/csv')}, data=param)
            if res.ok:
                result = res.text
            else:
                print(res.status_code)
                print(res.text)
                result = res.status_code + '|' + res.text

        return result
