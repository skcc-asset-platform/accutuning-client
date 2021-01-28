# accutuning-client

## 개요 
* Accu.Tuning이 원격에 설치되어 있는 경우, 개인 노트북에서 원격 서버 자원을 이용해서 automl 수행 

## 구현 
* Graphql Client : gql 사용 (https://github.com/graphql-python/gql) 
* REST API Client : requests 패키지 사용 

## 사용방법
```python
# import
from accutuning_client.category import Sklearn
from accutuning_client.client import Client

# Client 객체 생성 
client = Client('localhost', 8000)

# Experiment List 불러오기
experiments = client.experiments()

# Source List 불러오기 
sources = client.sources()

# Local File을 업로드해서 Source 생성 
client.create_source_from_file('/Users/ahaljh/Downloads/diabetes2.csv')

# Sklearn dataset에서 Source 생성 
client.create_source_from_sklearn(Sklearn.BOSTON)

# Source에서 Experiment 생성 
client.create_experiment(sources[0])

# Run Automl
experiment = experiments[0]
client.run(experiment)

# Leaderboard 정보 구해오기 
leaderboard = client.leaderboard(experiment)

# 모델 배포 
client.deploy(leaderboard[0])

# Deployment 정보 구해오기 
deployments = client.deployments(experiment)

# 각 컬럼의 최빈값, min, max를 구함 
most_frequent = client.mostfrequent(experiment)

# 예측 
input_val = {col.get('name'): col.get('mostFrequent') for col in most_frequent}
predict_val = client.predict(deployed_model, input_val, experiment.get('id'))
```