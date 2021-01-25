from accutuning_client.client import Client

client = Client()
# client.login(id, password)

# Experiment의 List를 불러온다.
experiments = client.experiments()
print(f'현재 Experiments는 총 {len(experiments)}개 있습니다.')
print(experiments)

# Source List를 불러온다. 
sources = client.sources()
print(f'현재 Sources는 총 {len(sources)}개 있습니다.')
print(sources)

# Source 선택
source = sources[0]
# client.create_experiment(source) 

# Experiment 선택
experiment = experiments[0]
print(experiment)
print(experiment.get('id'))

if experiment.get('status') == 'ready': # Validation을 여기서 할 건 아닌데, 일단 걸어놓음. 
    # Run AutoML 
    client.run(experiment)
else:
    print('Run 실행 가능한 상태가 아님')

if experiment.get('status') == 'finished': 
    # Leaderboard 정보 구해오기 
    leaderboard = client.leaderboard(experiment)
    print(f'leaderboad의 model 갯수는 {len(leaderboard)}')

    model = leaderboard[0]
    if model.get('deployedStatus') == None:
        # 모델 배포
        client.deploy(model)
    
else:
    print('Leaderboard 실행 가능한 상태가 아님')

if experiment.get('deploymentsCnt') > 0: 
    # Deployement 정보 구해오기 
    deployments = client.deployments(experiment)
    print(f'배포된 모델은 {len(deployments)}개 입니다.')
    deployed_model = deployments[0]
    print(deployed_model)
else:
    print('deploy된 모델이 없음')