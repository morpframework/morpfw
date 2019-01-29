import json
import requests


requests.get('http://localhost:5000/pages/+search', {
    'q': json.dumps({'operator': 'in',
                     'value': ['Hello'],
                     'field': 'body'})
})
