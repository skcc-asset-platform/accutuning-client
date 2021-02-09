import requests
import json
from accutuning_client.exception import HttpStatusError


class GraphQL:  # TODO GraphQL과 REST를 통합할 수도 있을까? (겹치는게 좀 있음)
    """GraphQL 호출을 담당하는 클래스"""

    _instance = None
    _endpoint_url = ''
    _header = {}
    _token = ''
    _token_exp_time = 0

    def __init__(self, endpoint_url, schema_validation=False):
        self._endpoint_url = endpoint_url
        self._schema_validation = schema_validation  # GraphQL의 Schema Validation : 보안때문에 막아놓은 경우 False로 해야함
        GraphQL._instance = self

    def add_login_info(self, token, token_exp_time):  # TODO Graphql과 REST 공통으로 빼자
        self._token = token
        self._token_exp_time = token_exp_time
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
    _token = ''
    _token_exp_time = 0

    def __init__(self, api_url):
        self._api_url = api_url
        REST._instance = self

    def add_login_info(self, token, token_exp_time):
        self._token = token
        self._token_exp_time = token_exp_time
        self._header['Authorization'] = f'JWT {token}'

    def get(self, url):
        res = requests.get(self._api_url + url, headers=self._header)
        if res.ok:
            obj = json.loads(res.text)
            return obj
        else:
            raise HttpStatusError(res.status_code, res.text)

    def post(self, url, param):
        res = requests.post(self._api_url + url, data=param, headers=self._header)
        result = ''
        if res.ok:
            result = json.loads(res.text)  # TODO 여기 관련 에러처리
        else:
            raise HttpStatusError(res.status_code, res.text)

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
                raise HttpStatusError(res.status_code, res.text)

        return result
