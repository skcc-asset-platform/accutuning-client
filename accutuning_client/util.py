from json.decoder import JSONDecodeError
import requests
import json


class GraphQL:
    """GraphQL 호출을 담당하는 클래스"""

    _instance = None
    _endpoint_url = ''
    _header = {'Content-Type': 'application/json', 'refresh-token': ''}

    def __init__(self, endpoint_url, schema_validation=False):
        self._endpoint_url = endpoint_url
        self._schema_validation = schema_validation  # GraphQL의 Schema Validation : 보안때문에 막아놓은 경우 False로 해야함
        GraphQL._instance = self

    def add_login_info(self, token):
        self._header['Authorization'] = f'JWT {token}'

    async def execute_async(self, query, param={}):
        from gql import Client, gql
        from gql.transport.aiohttp import AIOHTTPTransport

        transport = AIOHTTPTransport(url=self._endpoint_url, headers=self._header)

        # Using `async with` on the client will start a connection on the transport
        # and provide a `session` variable to execute queries on this connection
        async with Client(
            transport=transport, fetch_schema_from_transport=self._schema_validation,
        ) as session:
            result = await session.execute(gql(query), variable_values=param)
            return result

    def execute(self, query, param={}):
        # return asyncio.run(self.execute_async(query, param))
        from gql import Client, gql
        from gql.transport.requests import RequestsHTTPTransport

        transport = RequestsHTTPTransport(
            url=self._endpoint_url, verify=True, retries=3, headers=self._header
        )

        client = Client(transport=transport, fetch_schema_from_transport=self._schema_validation)
        result = client.execute(gql(query), variable_values=param)
        return result


# REST는 이렇게 씌울 필요가 있을까, 그냥 requests에서 바로 가져다 쓰는 것은...
class REST:
    """REST API를 호출하는 역할을 진행하는 클래스"""

    _instance = None
    _header = {}

    def __init__(self, api_url):
        self._api_url = api_url
        REST._instance = self

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
        res = requests.post(self._api_url + url, data=param, headers=self._header)
        result = ''
        if res.ok:
            try:
                result = json.loads(res.text)
            except JSONDecodeError:
                result = ''
        else:
            result = f'{res.status_code}|{res.text}'
            print(result)

        return result

    def filepost(self, url, filepath, param={}):
        from pathlib import Path
        filename = Path(filepath).name

        result = ''
        with open(filepath, 'rb') as f:
            res = requests.post(self._api_url + url, files={'fileData': (filename, f, 'text/csv')}, data=param, headers=self._header)
            if res.ok:
                result = res.text
            else:
                print(res.status_code)
                print(res.text)
                result = f'{res.status_code}|{res.text}'

        return result
