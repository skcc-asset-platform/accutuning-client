from accutuning_client.util import GraphQL, REST
from accutuning_client.category import Estimator
from accutuning_client.exception import StatusError
from time import time, sleep
import json


class Experiment(dict):
    """Accu.Tuning의 실험(Experiment)을 담당하는 클래스"""

    _display_prop = ['id', 'name', 'dataset.name', 'dataset.colCount', 'status', 'estimatorType', 'metric', 'bestScore', 'modelsCnt', 'deploymentsCnt']
    _RELOAD_SECOND = 10  # TODO Global 설정으로 바꿀까?

    def __init__(self, *args, graphql=GraphQL._instance, rest=REST._instance, dict_obj=None, **kwargs):  # TODO graphql, rest 대신 Client로 변경
        super().__init__(*args, **kwargs)
        self._graphql = graphql
        self._rest = rest
        if dict_obj:
            self.update(dict_obj)
        self._update_timestamp()

    def _update_timestamp(self):
        """객체의 timestamp정보를 업데이트함"""
        self._timestamp = time()

    def __repr__(self):  # TODO 화면 표현 검토
        self._reload_if_needs()
        return 'Experiment(' + ', '.join([f'{k}={self.get(k)}' for k in self._display_prop if self.get(k)]) + ')'

    def get(self, k, *args):
        """여러 Depth의 get을 한꺼번에 실행함(key안에 "."으로 구분)"""
        if isinstance(k, str) and '.' in k:
            obj = super()
            try:
                for sub_key in k.split('.'):
                    obj = obj.get(sub_key, *args)
            except Exception:
                obj = None
            return obj
        else:
            return super().get(k, *args)

    def __getitem__(self, k):
        """여러 Depth의 get을 한꺼번에 실행함(key안에 "."으로 구분)"""
        if isinstance(k, str) and '.' in k:
            obj = super()
            try:
                for sub_key in k.split('.'):
                    obj = obj.__getitem__(sub_key)
            except Exception:
                raise KeyError(k)
            return obj
        else:
            return super().__getitem__(k)

    def _reload_if_needs(self):
        cur_timestamp = time()
        if (cur_timestamp - self._timestamp) > Experiment._RELOAD_SECOND:
            self.reload()

    def reload(self):
        """
        Experiment 객체를 서버에서 다시 로드함
        """

        query = '''
            query getRuntime($id: Int!) {
                runtime(id: $id) {
                    id
                    name
                    estimatorType
                    metric
                    targetColumnName
                    status
                    modelsCnt
                    dataset {
                        id
                        name
                        columns {
                            id
                            name
                            datatype
                            mostFrequent
                            min
                            max
                        }
                        colCount
                    }
                    deploymentsCnt
                }
            }
        '''
        result = self._graphql.execute(query, {'id': self.get('id')})
        self.update(result.get('runtime'))
        self._update_timestamp()

    def run(self):
        """Run AutoML

        TODO Validation 처리
        """

        self._reload_if_needs()
        if (status := self.get('status')) != 'ready':
            raise StatusError(f'run을 하려면 ready 상태여야 합니다. 현재 {status} 상태입니다.')

        query = '''
            mutation startRuntime($id: ID!) {
                startRuntime(id: $id) {
                    __typename
                    runtime {
                        __typename
                        id
                        status
                        startedAt
                    }
                }
            }
        '''
        result = self._graphql.execute(query, {'id': self.get('id')})
        self.update(result.get('startRuntime').get('runtime'))
        self._update_timestamp()
        return self.get('status') == 'learning'

    def leaderboard(self):
        """leaderboard를 리턴한다."""
        query = '''
            query getLeaderboard($id: Int!) {
                runtime(id: $id) {
                    leaderboard {
                        id
                        score
                        trainScore
                        validScore
                        testScore
                        estimatorName
                        generator
                        file {
                            size
                            sizeHumanized
                        }
                        deployedStatus
                    }
                }
            }
        '''
        result = self._graphql.execute(query, {'id': self.get('id')})

        leaderboard = Leaderboard()
        for model_dict in result.get('runtime').get('leaderboard'):
            leaderboard.append(Model(experiment=self, graphql=self._graphql, rest=self._rest, dict_obj=model_dict))

        return leaderboard

    def deployments(self):  # TODO Graphql에서 first와 skip은 무엇인가? 용도를 알아보고 지우자.
        """Deployments를 구한다."""
        query = '''
            query runtimeDeployments($id: Int! $first: Int $skip: Int) {
                deployments(runtimeId: $id, first: $first, skip: $skip) {
                    id
                    name
                    description
                    status
                    modelType
                    modelPk
                    allMetricsJson
                    createdAt
                    testScore
                    model {
                        id
                        trainScore
                        validScore
                    }
                    file:pipelineFp {
                        url
                        size
                        sizeHumanized
                        name
                    }
                }
            }
        '''
        result = self._graphql.execute(query, {'id': self.get('id')})

        deployments = Deployments()
        for deployment_dic in result.get('deployments'):
            deployment = Deployment(self, dict_obj=deployment_dic)
            deployments.append(deployment)

        return deployments

    def column_info(self):
        """각 컬럼의 정보를 구한다."""
        query = '''
            query columnSummary($id: Int!) {
                runtime(id: $id) {
                    id
                    targetColumnName
                    dataset {
                        id
                        columns {
                            id
                            name
                            datatype
                            mostFrequent
                            min
                            max
                        }
                    }
                }
            }
        '''
        result = self._graphql.execute(query, {'id': self.get('id')})
        columns = result.get('runtime').get('dataset').get('columns')
        target_name = result.get('runtime').get('targetColumnName')
        return Columns([dict(col, isTarget=(col.get('name') == target_name)) for col in columns])


class Experiments(list):
    """
    실험(Experiment)을 모아놓은 컬렉션
    """
    def __init__(self, *args, graphql=GraphQL._instance, rest=REST._instance):  # TODO 여기는 graphql, rest 필요없을 듯
        super().__init__(*args)
        self._graphql = graphql
        self._rest = rest
        self._update_timestamp()

    def _update_timestamp(self):
        """객체의 timestamp정보를 업데이트함"""
        self._timestamp = time()

    def __repr__(self):  # TODO pandas 처럼 table 형태로 출력되게 변경
        return f'{len(self)} Experiments' + '\n=======================\n' + '\n'.join([exp.__repr__() for exp in self])

    # 일단 circular import 문제로 막아놓자.
    # @classmethod
    # def all(cls, client: Client):
    #     """
    #     client에서 전체 Experiments를 가져온다.
    #     """
    #     return client.experiments()

    def first(self):
        """
        실험목록 중 가장 최근 실험을 구합니다.
        """

        return self[0] if len(self) > 0 else None

    def find(self, estimatorType: Estimator, name: str):
        """
        estimatorType과 실험 이름으로 검색합니다.
        """

        result = self
        if estimatorType is not None:
            result = [exp for exp in self if exp.estimatorType == estimatorType]
        if name is not None:
            result = [exp for exp in self if exp.name == name]

        return Experiments(result)

    def get(self, id):
        """
        실험 ID에 해당하는 실험을 구합니다.
        """

        for exp in self:
            if exp.get('id') == str(id):
                return exp

        return None


class Leaderboard(list):
    """Accu.Tuning의 리더보드, 모델로 구성된 리스트"""

    def __init__(self, *args):
        super().__init__(*args)

    def best_model(self):
        """best model을 리턴합니다."""
        return self[0]


class Model(dict):  # TODO reload 필요, 특정 상태만
    def __init__(self, experiment, *args, graphql=GraphQL._instance, rest=REST._instance, dict_obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._experiment = experiment
        self._graphql = graphql
        self._rest = rest
        if dict_obj:
            self.update(dict_obj)
        self._update_timestamp()

    def _update_timestamp(self):
        """객체의 timestamp정보를 업데이트함"""
        self._timestamp = time()

    def deploy(self):
        """model을 deploy한다."""
        query = '''
            mutation mutateDeployment($modelId: ID!, $modelType: String!) {
                deployModel(modelId: $modelId, modelType: $modelType) {
                    deployment {
                        id
                        model {
                            id
                            __typename
                            deployedStatus
                        }
                    }
                }
            }
        '''
        result = self._graphql.execute(query, {'modelId': self.get('id'), 'modelType': 'ensemble' if self.get('generator') == 'ensemble' else 'model'})
        print(result)


class Deployments(list):
    """Deploy된 모델의 리스트"""
    def __init__(self, *args):
        super().__init__(*args)


class Deployment(dict):
    """Deploy된 모델"""
    def __init__(self, experiment, *args, dict_obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._experiment = experiment
        self._graphql = experiment._graphql
        self._rest = experiment._rest
        if dict_obj:
            self.update(dict_obj)

    def predict(self, col_input):
        """인풋값을 가지고 예측을 수행합니다."""
        param = dict(inputs=json.dumps(col_input), target_deployment_id=self.get('id'))

        res = self._rest.post(f'/runtimes/{self._experiment.get("id")}/deployment/predict/', param)
        prediction_pk = res.get('predictionPk')

        sleep(5)  # 예측 자체는 얼마 걸리지 않아 기다림 TODO 추후 비동기로 어떻게 할 수 있을까...

        query = '''
            query queryPrediction($id: Int!) {
                prediction(id: $id) {
                    output
                    done
                    error
                    errorMessage
                }
            }
        '''
        result = self._graphql.execute(query, {'id': prediction_pk})

        if not result.get('prediction').get('done'):
            for _ in range(3):
                sleep(5)
                result = self._graphql.execute(query, {'id': prediction_pk})
                if result.get('prediction').get('done'):
                    break

        return result.get('prediction').get('output')


class Columns(list):
    """Dataset을 이루는 컬럼 정보로 dict의 리스트로 이루어져 있음"""
    def __init__(self, *args):
        super().__init__(*args)
        self._except_target = [col for col in self if col.get('isTarget') is False]
        self._target_name = next(col.get('name') for col in self if col.get('isTarget'))

    def _column_values(self, val_type, include_target):
        col_list = self if include_target else self._except_target
        return {col.get('name'): col.get(val_type) for col in col_list}

    def most_frequent_values(self, include_target=False):
        """각 컬럼의 최빈값의 정보를 구합니다."""
        return self._column_values('mostFrequent', include_target)

    def max_values(self, include_target=False):
        """각 컬럼의 최대값의 정보를 구합니다."""
        return self._column_values('max', include_target)

    def min_values(self, include_target=False):
        """각 컬럼의 최소값의 정보를 구합니다."""
        return self._column_values('min', include_target)