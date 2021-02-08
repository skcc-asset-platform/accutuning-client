from accutuning_client.object import Experiment, Experiments
import json
from .util import GraphQL, REST


class Client:
    """
    accutuning-client의 가장 main 객체, 작업시 시작점
    """

    def __init__(self, server_ip, server_port):
        self._graphql = GraphQL(f'http://{server_ip}:{server_port}/api/graphql')
        self._rest = REST(f'http://{server_ip}:{server_port}/api')
        # self._graphql_endpoint = f'http://{server_ip}:{server_port}/api/graphql'
        # self._rest_api_url = f'http://{server_ip}:{server_port}/api'

    def login(self, id, password):
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

        exps = Experiments(graphql=self._graphql, rest=self._rest)
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

    def is_logged_in(self):
        """로그인 상태인지 구합니다."""
        result = self._server_env()
        login = False
        try:
            login = bool(result.get('userIsAuthenticated'))
        except Exception:
            login = False
        return login

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

    def create_experiment(self, source):  ## TODO 삭제예정
        """
        입력받은 source를 가지고 실험을 만든다. TODO 이거 Source 객체로 옮길 예정
        """
        self._rest.post(f'/sources/{source.get("id")}/experiment/', source)  # TODO 성공/실패 여부 리턴
