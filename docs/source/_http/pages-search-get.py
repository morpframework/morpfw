import json
import requests


requests.get('http://localhost:5000/pages/+search', {
    'select': '$.[title, body]',
    'q': json.dumps({'operator': 'in',
                     'value': ['Hello'],
                     'field': 'body'})
})
