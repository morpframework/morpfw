import json
import requests

requests.get('/pages/+aggregate', data={'group': json.dumps({
    'count': {
        'function': 'count',
        'field': 'uuid'
    },
    'year': {
        'function': 'year',
        'field': 'created'
    },
    'month': {
        'function': 'month',
        'field': 'created'
    },
    'day': {
        'function': 'day',
        'field': 'created'
    },
    'sum': {
        'function': 'sum',
        'field': 'value'
    },
    'avg': {
        'function': 'avg',
        'field': 'value'
    }
})})
