from urllib.parse import urlencode
import json
import requests


qs = urlencode({
    'group': ("count:count(uuid), year:year(created), month:month(created),"
              "day:day(created), sum:sum(value), avg:avg(value)")
})
requests.get('/pages/+aggregate?%s' % qs)
