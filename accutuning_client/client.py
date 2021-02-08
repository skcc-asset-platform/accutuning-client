from accutuning_client.category import Sklearn
from time import sleep
from .util import GraphQL, REST


class Client:
    '''
    accutuning-client의 가장 main 객체, 작업시 시작점
    '''

    def __init__(self, server_ip, server_port):
        self._graphql = GraphQL(f'http://{server_ip}:{server_port}/api/graphql')
        self._rest = REST(f'http://{server_ip}:{server_port}/api')
        # self._graphql_endpoint = f'http://{server_ip}:{server_port}/api/graphql'
        # self._rest_api_url = f'http://{server_ip}:{server_port}/api'

    def login(self, id, password):
        res = self._rest.post('/token-auth/', {'username': id, 'password': password})
        print(res)
        print(type(res))
        self._rest.add_login_info(res.get('token'))
        self._graphql.add_login_info(res.get('token'))
        return res

    def experiments(self):
        '''
        전체 experiments를 가져옴
        '''
        query = '''
            query {
                runtimes {
                    id
                    name
                    estimatorType
                    metric
                    modelsCnt
                    status
                    targetColumnName
                    dataset {
                        id
                        name
                        featureNames
                        processingStatus
                    }
                    deploymentsCnt
                }
            }
        '''
        result = self._graphql.execute(query)
        return result.get('runtimes')

    def sources(self):
        '''
        전체 sources를 가져옴
        '''
        return self._rest.get('/sources/')

    def create_source_from_sklearn(self, sklearn_dataset: Sklearn):
        self._rest.post('/sources/from_sklearn_dataset/', {'datasetName': sklearn_dataset.value})

    def create_source_from_file(self, filepath):
        self._rest.filepost('/sources/workspace_files/', filepath)

    def possible_container(self):   # TODO 컨테이너 갯수 정보가 있어야 할 꺼 같음, 이건 근데 매 호출시마다 먼저 구하는 것이 나을지도..
        pass

    def create_experiment(self, source):
        '''
        입력받은 source를 가지고 실험을 만든다. TODO 이거 Source 객체로 옮길 예정
        '''
        self._rest.post(f'/sources/{source.get("id")}/experiment/', source)  # TODO 성공/실패 여부 리턴
        # return True if res.status_code == 201 else False

    def preprocessor_config_recommend(self, experiment):
        '''
        데이터셋을 기반으로 Preprocessor 방법을 자동으로 추천받아 preprocessor config를 변경합니다.
        '''
        query = '''
            mutation patchRecmdConfig($id:ID!) {
                patchRecommendationConfig (id: $id) {
                        dataset {
                            id
                            processingStatus
                    }
                }
            }
        '''
        self._graphql.execute(query, {'id': experiment.get('dataset').get('id')})


    def preprocess(self, experiment):
        '''
        지정된 preprocessor config 설정대로 전처리를 실시합니다.
        '''
        query = '''
            mutation preprocess($id:ID!) {
                preprocess (id: $id) {
                    dataset {
                        id
                        processingStatus
                    }
                    error
                    errorMessage
                }
            }
        '''
        self._graphql.execute(query, {'id': experiment.get('dataset').get('id')})

    def set_runtime_settings(self, experiment, estimator_type, metric, target_column_name):
        '''
        '''

        query = '''
            mutation ($id: ID!, $input: PatchRuntimeInput!) {
                patchRuntime(id: $id, input: $input) {
                    runtime {
                        id
                        name
                        estimatorType
                        metric
                        targetColumnName
                    }
                }
            }
        '''
        self._graphql.execute(query, {'id': experiment.get('id'), 'input' : {'estimatorType': estimator_type, 'metric': metric, 'targetColumnName': target_column_name}})

    def run(self, experiment):
        '''
        입력받은 experiment를 가지고 run automl을 수행한다.
        TODO 이거 Experiment 객체로 옮길 예정
        TODO Validation 처리가 좀 되어야 한다. 특히 상태값 체크
        '''
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
        self._graphql.execute(query, {'id': experiment.get('id')})

    def leaderboard(self, experiment):
        '''
        입력받은 experiment의 leaderboard를 리턴한다.
        leaderboard = models로 할지, leaderboard에서 또 models를 구할지 고민 필요
        TODO Experiment 객체로 옮길 예정
        '''
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
        result = self._graphql.execute(query, {'id': experiment.get('id')})
        return result.get('runtime').get('leaderboard')

    def deploy(self, model):
        '''
        입력받은 model을 deploy한다.
        TODO Model 객체로 옮길 예정
        '''
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
        self._graphql.execute(query, {'modelId': model.get('id'), 'modelType': 'ensemble' if model.get('generator') == 'ensemble' else 'model'})

    def deployments(self, experiment):
        '''
        입력받은 experiment의 Deployments를 구한다.
        TODO Experiment 객체로 옮길 예정
        '''
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
        result = self._graphql.execute(query, {'id': experiment.get('id')})
        print(result)
        return result.get('deployments')

    def mostfrequent(self, experiment):
        '''
        입력받은 experiment에 대해서 각 컬럼의 최빈값을 구한다. 예측시 사용할 예정
        TODO 이 것은 어떻게 할 지 생각해봐야겠다.
        '''
        query = '''
            query mostfrequent($id: Int!) {
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
        result = self._graphql.execute(query, {'id': experiment.get('id')})
        columns = result.get('runtime').get('dataset').get('columns')
        target_column_name = result.get('runtime').get('targetColumnName')
        return [col for col in columns if col.get('name') != target_column_name]

    def predict(self, model, input, runtime_id):
        import json
        s = json.dumps(input)
        d = {}
        d['inputs'] = s
        d['target_deployment_id'] = model.get('id')

        res = self._rest.post(f'/runtimes/{runtime_id}/deployment/predict/', d)
        prediction_pk = res.get('predictionPk')

        sleep(5)

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
