from accutuning_client.object import Experiment, Experiments
import json
from time import time
from .util import GraphQL, REST


class Client:
    """
    accutuning-client의 가장 main 객체, 작업시 시작점
    """

    def __init__(self, server_ip, server_port):
        self._graphql = GraphQL(f'http://{server_ip}:{server_port}/api/graphql')
        self._rest = REST(f'http://{server_ip}:{server_port}/api')

    def _get_token(self, id, password):
        """서버에서 토큰을 발급받음"""
        query = '''
            mutation tokenAuth($username: String!, $password: String!) {
                tokenAuth(username: $username, password: $password) {
                    token
                }
            }
        '''
        result = self._graphql.execute(query, {'username': id, 'password': password})
        token = result.get('tokenAuth').get('token')
        return token

    def _get_token_expire_time(self, token):
        """발급받은 토큰의 만료시간을 구함"""
        query = '''
            mutation verifyToken($token: String!) {
                verifyToken(token: $token) {
                    payload
                }
            }
        '''
        result = self._graphql.execute(query, {'token': token})
        exp = result.get('verifyToken').get('payload').get('exp')
        return int(exp)

    def _token_remain_time(self):  # TODO 서버시간, 클라이언트 시간 보정계수 필요?
        """토큰 만료까지 남은 시간을 초 단위로 리턴함"""
        return self._token_exp_time - int(time())

    def is_logged_in(self):
        """로그인 상태인지 구합니다."""
        return self._token and self._token_remain_time() > 0

    def _refresh_token(self):
        """토큰을 재발급받음"""
        query = '''
            mutation refreshToken($token: String!) {
                refreshToken(token: $token) {
                    token
                    payload
                }
            }
        '''
        result = self._graphql.execute(query, {'token': self._token})
        new_token = result.get('refreshToken').get('token')
        new_exp = int(result.get('refreshToken').get('payload').get('exp'))
        self._write_token_info(new_token, new_exp)

    def _refresh_token_if_needs(self):
        """지정 시간 이내로 남을 경우 토큰 재발급 처리"""
        _TOKEN_REFRESH_MINUTES = 28  # token의 만료시간이 15분 이내로 남으면 리프레시함
        time_diff = self._token_remain_time()
        if time_diff < 60 * _TOKEN_REFRESH_MINUTES:
            print(f'token expire timie이 {_TOKEN_REFRESH_MINUTES}분 이내라 내부적으로 token을 refresh함')  # TODO 메시지는 추후 삭제
            self._refresh_token()

    def _write_token_info(self, token, token_exp_time):
        """발급받은 토큰 관련 정보를 기록함"""
        self._token = token
        self._token_exp_time = token_exp_time
        self._rest.add_login_info(token, token_exp_time)
        self._graphql.add_login_info(token, token_exp_time)

    def login(self, id, password):
        """아이디와 비밀번호를 가지고 로그인을 수행함"""
        token = self._get_token(id, password)
        token_exp_time = self._get_token_expire_time(token)
        self._write_token_info(token, token_exp_time)
        return True

    def login_rest(self, id, password):  # TODO graphql 버전 검증 끝나면 삭제예정
        """아이디와 비밀번호를 가지고 REST 방식으로 로그인을 수행함"""
        res = self._rest.post('/token-auth/', {'username': id, 'password': password})
        self._rest.add_login_info(res.get('token'))
        self._graphql.add_login_info(res.get('token'))
        return True  # Error 안나고 오면 성공

    def _server_env(self):
        """서버 환경설정을 가져옵니다."""
        query = '''
            query {
                env {
                    totalContainerCount
                    activeContainerCount
                    userIsAuthenticated
                    loginUser {
                        id
                    }
                }
            }
        '''
        result = self._graphql.execute(query)
        return result.get('env')

    def experiments(self):
        """
        전체 experiments를 가져옴
        """
        query = '''
            query getAllRuntimes {
                runtimes {
                    id
                    name
                    metric
                    estimatorType
                    modelsCnt
                    status
                    targetColumnName
                    dataset {
                        id
                        name
                        featureNames
                        processingStatus
                        colCount
                    }
                    deploymentsCnt
                }
            }
        '''
        result = self._graphql.execute(query)

        exps = Experiments(graphql=self._graphql, rest=self._rest)  # TODO 이런 방식으로 셋팅할 수밖에 없을까?
        for exp_obj in result.get('runtimes'):
            exp = Experiment(graphql=self._graphql, rest=self._rest, dict_obj=exp_obj)
            exps.append(exp)

        return exps

    def possible_container(self):
        """사용가능한 컨테이너 갯수를 구합니다."""
        result = self._server_env()
        no_of_container = 0
        try:
            no_of_container = int(result.get('activeContainerCount'))
        except Exception:
            no_of_container = 0
        return no_of_container

    def create_experiment_from_file(self, filepath):
        source_str = self._rest.filepost('/sources/workspace_files/', filepath)
        source = json.loads(source_str)
        result = self._rest.post(f'/sources/{source.get("id")}/experiment/', source)
        exp = Experiment(graphql=self._graphql, rest=self._rest, dict_obj=result)
        return exp

    def sources(self):  # TODO 삭제예정
        """
        전체 sources를 가져옴
        """
        return self._rest.get('/sources/')

    def create_source_from_file(self, filepath):  # TODO 삭제예정
        return self._rest.filepost('/sources/workspace_files/', filepath)

    def create_experiment(self, source):  # TODO 삭제예정
        """
        입력받은 source를 가지고 실험을 만든다. TODO 이거 Source 객체로 옮길 예정
        """
        self._rest.post(f'/sources/{source.get("id")}/experiment/', source)  # TODO 성공/실패 여부 리턴
