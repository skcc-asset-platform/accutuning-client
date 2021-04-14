# accutuning-client

## 개요 
* Accu.Tuning이 원격에 설치되어 있는 경우, 개인 노트북에서 원격 서버 자원을 이용해서 automl 수행 

## 구현 
* Graphql Client : gql 사용 (https://github.com/graphql-python/gql) 
* REST API Client : requests 패키지 사용 

## 사용방법
```python
# import
from accutuning_client.client import Client

# Client 객체 생성 
client = Client('localhost', 8000)

# 로그인
client.login('autoinsight', 'autoinsight')

# Experiment List 불러오기
experiments = client.experiments()

# 로컬 파일에서 Experiment 생성 
experiment_new = client.create_experiment_from_file('/Users/ahaljh/Downloads/iris1.csv')

# 전처리를 추천받아 preprocessor config를 변경 
experiment_new.recommend()

# Run Automl
experiment_new.run()

# Leaderboard 정보 구해오기 
leaderboard = experiment.leaderboard()

# Best Model 구하기 
model = leaderboard.best_model()

# 모델 배포 
model.deploy()

# Deployment 정보 구해오기 
deployments = experiment_new.deployments()

# 첫번째 Deployment 모델 가져오기
deployed_model = deployments[0]

# 모델 예측을 위해 Default값인 최빈값을 구함
columns = experiment.column_info()
most_frequent = columns.most_frequent_values()

# 예측을 위한 input 값 생성
input_val = most_frequent

# 예측 
predict_val = deployed_model.predict(input_val)
```