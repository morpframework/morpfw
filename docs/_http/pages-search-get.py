from urllib.parse import urlencode
import json
import requests

qs = urlencode({
    'q': 'body in ["Hello"]'
})
requests.get('http://localhost:5000/pages/+search?%s' % qs)
