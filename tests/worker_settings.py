imports = ('test_signals',)
#broker_url = 'amqp://celery:celery@localhost/'
broker_url = 'redis://'
result_backend = 'redis://'

