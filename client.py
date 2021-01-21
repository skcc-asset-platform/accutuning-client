from util import GraphQL, REST

class Client:
    '''
    accutuning-client의 가장 main 객체, 작업시 시작점 
    '''

    def __init__(self):
        pass    # TODO Singleton

    def server(self, ip, port):
        pass # graphql endpoint, rest endpoint setting

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
        res = REST.post(f'/sources/{source.get("id")}/experiment/', source) # TODO 성공/실패 여부 리턴
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
        result = GraphQL.execute(query, {'id': experiment.get('id')})