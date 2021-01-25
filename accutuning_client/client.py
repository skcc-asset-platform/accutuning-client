from .util import GraphQL, REST


class Client:
    '''
    accutuning-client의 가장 main 객체, 작업시 시작점
    '''

    def __init__(self):
        pass    # TODO Singleton

    def server(self, ip, port):
        pass    # graphql endpoint, rest endpoint setting

    def experiments(self):
        '''
        전체 experiments를 가져옴
        '''
        query = '''
            query {
                runtimes {
                    id
                    name
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
        result = GraphQL.execute(query)
        return result.get('runtimes')

    def sources(self):
        '''
        전체 sources를 가져옴
        '''
        return REST.get('/sources/')

    def possible_container(self):   # TODO 컨테이너 갯수 정보가 있어야 할 꺼 같음, 이건 근데 매 호출시마다 먼저 구하는 것이 나을지도..
        pass

    def create_experiment(self, source):
        '''
        입력받은 source를 가지고 실험을 만든다. TODO 이거 Source 객체로 옮길 예정
        '''
        REST.post(f'/sources/{source.get("id")}/experiment/', source)  # TODO 성공/실패 여부 리턴
        # return True if res.status_code == 201 else False

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
        GraphQL.execute(query, {'id': experiment.get('id')})

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
        result = GraphQL.execute(query, {'id': experiment.get('id')})
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
        GraphQL.execute(query, {'modelId': model.get('id'), 'modelType': 'ensemble' if model.get('generator') == 'ensemble' else 'model'})

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
        result = GraphQL.execute(query, {'id': experiment.get('id')})
        print(result)
        return result.get('deployments')
