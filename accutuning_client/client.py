from accutuning_client.object import Experiment, Experiments
import json
from .util import CallApi


class Client:
    """
    accutuning-client의 가장 main 객체, 작업시 시작점
    """

    def __init__(self, server_ip, server_port):
        self._api = CallApi(server_ip, server_port)

    def login(self, id, password):
        """아이디와 비밀번호를 가지고 로그인을 수행함"""
        return self._api.login(id, password)

    # def login_rest(self, id, password):  # TODO graphql 버전 검증 끝나면 삭제예정
    #     """아이디와 비밀번호를 가지고 REST 방식으로 로그인을 수행함"""
    #     res = self._rest.post('/token-auth/', {'username': id, 'password': password})
    #     self._rest.add_login_info(res.get('token'))
    #     self._graphql.add_login_info(res.get('token'))
    #     return True  # Error 안나고 오면 성공

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
        result = self._api.GRAPHQL(query)
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
        result = self._api.GRAPHQL(query)

        exps = Experiments()  # TODO 이런 방식으로 셋팅할 수밖에 없을까? -> list comprehension은 너무 길다.
        for exp_obj in result.get('runtimes'):
            exp = Experiment(api=self._api, dict_obj=exp_obj)
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
        source_str = self._api.FILEPOST('/sources/workspace_files/', filepath)
        source = json.loads(source_str)
        result = self._api.POST(f'/sources/{source.get("id")}/experiment/', source)
        exp = Experiment(api=self._api, dict_obj=result)
        return exp
