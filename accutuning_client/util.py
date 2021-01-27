import asyncio
from json.decoder import JSONDecodeError
import requests
import json


class GraphQL:
    _header = {'refresh-token': ''}

    @classmethod
    def add_login_info(cls, token):
        cls._header['authorization'] = f'Bearer {token}'
        print(f'Header:{cls._header}')

    @classmethod
    async def execute_async(cls, endpoint_url, query, param={}):
        from gql import Client, gql
        from gql.transport.aiohttp import AIOHTTPTransport

        transport = AIOHTTPTransport(url=endpoint_url, headers=cls._header)

        # Using `async with` on the client will start a connection on the transport
        # and provide a `session` variable to execute queries on this connection
        async with Client(
            transport=transport, fetch_schema_from_transport=True,
        ) as session:

            result = await session.execute(gql(query), variable_values=param)
            print(result)
            return result

    @classmethod
    def execute(cls, endpoint_url, query, param={}):
        return asyncio.run(cls.execute_async(endpoint_url, query, param))


# REST는 이렇게 씌울 필요가 있을까, 그냥 requests에서 바로 가져다 쓰는 것은...
class REST:
    _header = {'Accept': 'application/json', 'Content-Type': 'application/json;charset=UTF-8'}

    @classmethod
    def add_login_info(cls, token):
        cls._header['Authorization'] = f'JWT {token}'

    @classmethod
    def get(cls, url):
        res = requests.get(url, headers=cls._header)
        print(res.status_code)
        if res.status_code == 200:
            obj = json.loads(res.text)
            print(obj)
            return obj
        else:
            return ''  # TODO 에러 발생시켜야 함

    @classmethod
    def post(cls, url, param):
        res = requests.post(url, data=param)
        print(res)
        if res.status_code == 200:
            obj = ''
            try:
                obj = json.loads(res.text)
            except JSONDecodeError:
                obj = ''
            print(obj)
            return obj
        else:
            print(res.text)
            return res.status_code
