from client import Client

client = Client()

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
# source.create_experiment()
# client.create_experiment(source) 

experiment = experiments[0]
print(experiment)
print(experiment.get('id'))

if experiment.get('status') == 'ready': # Validation을 여기서 할 건 아닌데, 일단 걸어놓음. 
    client.run(experiment)
else:
    print('실행 가능한 상태가 아님')
