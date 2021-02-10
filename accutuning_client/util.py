import requests
import json
from time import time
from accutuning_client.exception import HttpStatusError


class CallApi:
    """GraphQL 및 REST 방식으로 서버를 호출하는 Class"""

    _token = ''
    _token_exp_time = 0
    _headers = {}
    _schema_validation = False  # GraphQL의 Schema Validation으로, 서버에서 보안 때문에 막아놓을 경우 사용이 불가하다.
    _TOKEN_REFRESH_MINUTES = 28  # token의 만료시간이 15분 이내로 남으면 리프레시함

    def __init__(self, server_ip, server_port, graphql_schema_validation=False) -> None:
        self._graph_endpoint = f'http://{server_ip}:{server_port}/api/graphql'
        self._rest_api_url = f'http://{server_ip}:{server_port}/api'
        self._schema_validation = graphql_schema_validation

    def login(self, id, password):
        """입력받은 id, password를 가지고 로그인을 수행합니다."""
        token = self._get_token(id, password)
        token_exp_time = self._get_token_expire_time(token)
        self._write_token_info(token, token_exp_time)
        return True  # 에러가 없으면 성공

    def is_logged_in(self):
        """로그인 상태인지 구합니다."""
        return self._token and self._token_remain_time() > 0

    def GRAPHQL(self, query, params={}):  # GET Naming에 맞춰 대문자로 생성
        """GraphQL 방식으로 호출합니다."""
        # Token refresh Logic
        if self.is_logged_in() and self._token_remain_time() < 60 * CallApi._TOKEN_REFRESH_MINUTES:
            print(f'token expire timie이 {CallApi._TOKEN_REFRESH_MINUTES}분 이내라 내부적으로 token을 refresh함')  # TODO 메시지는 추후 삭제
            self._refresh_token()

        return self._GRAPHQL(query, params)

    def _GRAPHQL(self, query, params={}):
        """GraphQL 방식으로 호출합니다."""
        from gql import Client, gql
        from gql.transport.requests import RequestsHTTPTransport

        transport = RequestsHTTPTransport(
            url=self._graph_endpoint, verify=True, retries=3, headers=self._headers
        )

        client = Client(transport=transport, fetch_schema_from_transport=self._schema_validation)
        result = client.execute(gql(query), variable_values=params)
        return result

    def GET(self, url):  # dictionary에서 쓰는 get과 헷갈릴 수 있어 대문자로 생성함
        """REST API의 GET 방식으로 서버를 호출합니다."""
        res = requests.get(self._rest_api_url + url, headers=self._headers)
        if res.ok:
            obj = json.loads(res.text)
            return obj
        else:
            raise HttpStatusError(res.status_code, res.text)

    def POST(self, url, params):  # GET Naming에 맞춰 대문자로 생성
        """REST API의 POST 방식으로 서버를 호출합니다."""
        res = requests.post(self._rest_api_url + url, data=params, headers=self._headers)
        result = ''
        if res.ok:
            result = json.loads(res.text)  # TODO 여기 관련 에러처리
        else:
            raise HttpStatusError(res.status_code, res.text)

        return result

    def FILEPOST(self, url, filepath, params={}):  # GET Naming에 맞춰 대문자로 생성
        """REST API의 POST 방식으로 서버에 파일을 업로드합니다."""
        from pathlib import Path
        filename = Path(filepath).name

        result = ''
        with open(filepath, 'rb') as f:
            res = requests.post(self._rest_api_url + url, files={'fileData': (filename, f, 'text/csv')}, data=params, headers=self._headers)
            if res.ok:
                result = res.text
            else:
                raise HttpStatusError(res.status_code, res.text)

        return result

    def _get_token(self, id, password):
        """id와 password를 가지고 서버에서 토큰을 발급받습니다."""
        query = '''
            mutation tokenAuth($username: String!, $password: String!) {
                tokenAuth(username: $username, password: $password) {
                    token
                }
            }
        '''
        result = self._GRAPHQL(query, {'username': id, 'password': password})
        token = result.get('tokenAuth').get('token')
        return token

    def _get_token_expire_time(self, token):
        """입력받은 토큰의 만료시간을 구합니다."""
        query = '''
            mutation verifyToken($token: String!) {
                verifyToken(token: $token) {
                    payload
                }
            }
        '''
        result = self._GRAPHQL(query, {'token': token})
        exp = result.get('verifyToken').get('payload').get('exp')
        return int(exp)

    def _refresh_token(self):
        """서버에서 토큰을 재발급받습니다."""
        query = '''
            mutation refreshToken($token: String!) {
                refreshToken(token: $token) {
                    token
                    payload
                }
            }
        '''
        result = self._GRAPHQL(query, {'token': self._token})
        new_token = result.get('refreshToken').get('token')
        new_exp = int(result.get('refreshToken').get('payload').get('exp'))
        self._write_token_info(new_token, new_exp)

    def _token_remain_time(self):  # TODO 서버시간, 클라이언트 시간 보정계수 필요?
        """토큰 만료까지 남은 시간을 초 단위로 리턴합니다."""
        return self._token_exp_time - int(time())

    def _write_token_info(self, token, token_exp_time):
        """발급받은 토큰 관련 정보를 기록합니다."""
        self._token = token
        self._token_exp_time = token_exp_time
        self._headers = {'Authorization': f'JWT {token}'}


# class GraphQL:  # TODO GraphQL과 REST를 통합할 수도 있을까? (겹치는게 좀 있음)
#     """GraphQL 호출을 담당하는 클래스"""

#     _instance = None
#     _endpoint_url = ''
#     _header = {}
#     _token = ''
#     _token_exp_time = 0

#     def __init__(self, endpoint_url, schema_validation=False):
#         self._endpoint_url = endpoint_url
#         self._schema_validation = schema_validation  # GraphQL의 Schema Validation : 보안때문에 막아놓은 경우 False로 해야함
#         GraphQL._instance = self

#     def add_login_info(self, token, token_exp_time):  # TODO Graphql과 REST 공통으로 빼자
#         self._token = token
#         self._token_exp_time = token_exp_time
#         self._header['Authorization'] = f'JWT {token}'

#     async def execute_async(self, query, param={}):
#         from gql import Client, gql
#         from gql.transport.aiohttp import AIOHTTPTransport

#         transport = AIOHTTPTransport(url=self._endpoint_url, headers=self._header)

#         # Using `async with` on the client will start a connection on the transport
#         # and provide a `session` variable to execute queries on this connection
#         async with Client(
#             transport=transport, fetch_schema_from_transport=self._schema_validation,
#         ) as session:
#             result = await session.execute(gql(query), variable_values=param)
#             return result

#     def execute(self, query, param={}):
#         # return asyncio.run(self.execute_async(query, param))
#         from gql import Client, gql
#         from gql.transport.requests import RequestsHTTPTransport

#         transport = RequestsHTTPTransport(
#             url=self._endpoint_url, verify=True, retries=3, headers=self._header
#         )

#         client = Client(transport=transport, fetch_schema_from_transport=self._schema_validation)
#         result = client.execute(gql(query), variable_values=param)
#         return result


# # REST는 이렇게 씌울 필요가 있을까, 그냥 requests에서 바로 가져다 쓰는 것은...
# class REST:
#     """REST API를 호출하는 역할을 진행하는 클래스"""

#     _instance = None
#     _header = {}
#     _token = ''
#     _token_exp_time = 0

#     def __init__(self, api_url):
#         self._api_url = api_url
#         REST._instance = self

#     def add_login_info(self, token, token_exp_time):
#         self._token = token
#         self._token_exp_time = token_exp_time
#         self._header['Authorization'] = f'JWT {token}'

#     def get(self, url):
#         res = requests.get(self._api_url + url, headers=self._header)
#         if res.ok:
#             obj = json.loads(res.text)
#             return obj
#         else:
#             raise HttpStatusError(res.status_code, res.text)

#     def post(self, url, param):
#         res = requests.post(self._api_url + url, data=param, headers=self._header)
#         result = ''
#         if res.ok:
#             result = json.loads(res.text)  # TODO 여기 관련 에러처리
#         else:
#             raise HttpStatusError(res.status_code, res.text)

#         return result

#     def filepost(self, url, filepath, param={}):
#         from pathlib import Path
#         filename = Path(filepath).name

#         result = ''
#         with open(filepath, 'rb') as f:
#             res = requests.post(self._api_url + url, files={'fileData': (filename, f, 'text/csv')}, data=param, headers=self._header)
#             if res.ok:
#                 result = res.text
#             else:
#                 raise HttpStatusError(res.status_code, res.text)

#         return result
