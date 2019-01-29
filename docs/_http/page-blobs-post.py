import json
import requests

requests.post('http://localhost:5000/pages/ea31ebb4eb814572b2cbfc2d30fac7f2/+blobs?field=attachment',
              files={'upload': open('/path/to/file.jpg')})
