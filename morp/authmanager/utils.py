

def rellink(context, request, name=None, method='GET', link_name=None):
    link_name = link_name or name
    if name:
        name = '+%s' % name
    if name is None:
        link_name = 'self'
    return {
        'rel': link_name,
        'type': method,
        'href': request.link(context, name)
    }
