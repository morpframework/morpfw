imports = ('test_signals',)
#broker_url = 'amqp://celery:celery@localhost/'
broker_url = 'amqp://guest:guest@localhost:34567/'
result_backend = 'db+postgresql://postgres@localhost:45678/morp_tests'
