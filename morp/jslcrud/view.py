from .app import App
from .model import CRUDModel, CRUDCollection
from .validator import validate_schema, get_data
from .errors import ValidationError, NotFoundError, StateUpdateProhibitedError
from .errors import AlreadyExistsError
from . import permission
import json
from webob.exc import HTTPNotFound, HTTPForbidden, HTTPInternalServerError
from morepath.request import Request
from transitions import MachineError
from jsonpath_ng import parse as jsonpath_parse
from urllib.parse import urlencode
import traceback
import os
import sys
import logging
logger = logging.getLogger('jslcrud')


@get_data.register(model=CRUDCollection, request=Request)
def get_collection_data(model, request):
    return request.json


@App.json(model=CRUDCollection, permission=permission.View)
def schema(context, request):
    return context.json()


@App.json(model=CRUDCollection, name='search', permission=permission.Search)
def search(context, request):
    if not context.search_view_enabled:
        raise HTTPForbidden()
    query = json.loads(request.GET.get('q', '{}'))
    if not query:
        query = None
    limit = int(request.GET.get('limit', 20))
    offset = int(request.GET.get('offset', 0))
    order_by = request.GET.get('order_by', None)
    select = request.GET.get('select', None)
    if order_by:
        order_by = order_by.split(':')
        if len(order_by) == 1:
            order_by = order_by + ['asc']
    if limit > 100:
        limit = 100
    objs = context.search(query, offset=offset, limit=limit, order_by=order_by)
    objs = [obj.json() for obj in objs]
    if select:
        expr = jsonpath_parse(select)
        results = []
        for obj in objs:
            results.append([match.value for match in expr.find(obj['data'])])
    else:
        results = objs
    params = {}
    if select:
        params['select'] = select
    if limit:
        params['limit'] = limit
    params['offset'] = offset + limit
    qs = urlencode(params)
    res = {'results': results, 'q': query}
    if len(results):
        res.setdefault('links', [])
        res['links'].append({
            'rel': 'next',
            'href': request.link(context, '+search?%s' % qs)
        })
    if offset > 0:
        prev_offset = offset - limit
        if prev_offset < 0:
            prev_offset = 0
        params['offset'] = prev_offset
        qs = urlencode(params)
        res.setdefault('links', [])
        res['links'].append({
            'rel': 'previous',
            'href': request.link(context, '+search?%s' % qs)
        })
    return res


@App.json(model=CRUDCollection, request_method='POST',
          load=validate_schema(), permission=permission.Create)
def create(context, request, json):
    if not context.create_view_enabled:
        raise HTTPForbidden()
    obj = context.create(request.json)
    obj.save()
    return obj.json()


@get_data.register(model=CRUDModel, request=Request)
def get_obj_data(model, request):
    data = model.json()['data']
    data.update(request.json)
    return data


@App.json(model=CRUDModel, permission=permission.View)
def read(context, request):
    select = request.GET.get('select', None)
    obj = context.json()
    if select:
        expr = jsonpath_parse(select)
        results = []
        obj = [match.value for match in expr.find(obj['data'])]
    return obj


@App.json(model=CRUDModel, request_method='PATCH', load=validate_schema(),
          permission=permission.Edit)
def update(context, request, json):
    if not context.update_view_enabled:
        raise HTTPForbidden()

    context.update(request.json)
    return {'status': 'success'}


@App.json(model=CRUDModel, name='statemachine', request_method='POST',
          permission=permission.Edit)
def statemachine(context, request):
    if not context.statemachine_view_enabled:
        raise HTTPForbidden()

    sm = context.state_machine()
    transition = request.json['transition']
    attr = getattr(sm, transition, None)
    if attr is None:
        @request.after
        def adjust_status(response):
            response.status = 422

        return {
            'status': 'error',
            'message': 'Unknown transition %s' % transition
        }
    attr()
    context.save()
    return context.json()


@App.json(model=CRUDModel, request_method='DELETE',
          permission=permission.Delete)
def delete(context, request):
    if not context.delete_view_enabled:
        raise HTTPForbidden()

    context.delete()
    return {'status': 'success'}


@App.json(model=NotFoundError)
def notfound_error(context, request):
    @request.after
    def adjust_status(response):
        response.status = 404
    return {'status': 'error',
            'message': 'Object Not Found : %s on %s' % (context.message,
                                                        request.path)}


@App.json(model=AlreadyExistsError)
def alreadyexists_error(context, request):
    @request.after
    def adjust_status(response):
        response.status = 422

    return {'status': 'error',
            'message': 'Object Already Exists : %s' % context.message}


@App.json(model=HTTPForbidden)
def forbidden_error(context, request):
    @request.after
    def adjust_status(response):
        response.status = 403
    return {'status': 'error',
            'message': 'Access Denied : %s' % request.path}


@App.json(model=HTTPNotFound)
def httpnotfound_error(context, request):
    @request.after
    def adjust_status(response):
        response.status = 404
    return {'status': 'error',
            'message': 'Object Not Found : %s' % request.path}


@App.json(model=ValidationError)
def validation_error(context, request):
    @request.after
    def adjust_status(response):
        response.status = 422

    field_errors = []
    form_errors = []
    for e in context.field_errors:
        path = [str(p) for p in e.path]
        field_errors.append({
            'field': '.'.join(path),
            'message': e.message
        })

    for e in context.form_errors:
        form_errors.append(e.message)

    return {
        'status': 'error',
        'field_errors': field_errors,
        'form_errors': form_errors
    }


@App.json(model=MachineError)
def statemachine_error(context, request):
    @request.after
    def adjust_status(response):
        response.status = 422

    return {
        'status': 'error',
        'message': context.value
    }


@App.json(model=StateUpdateProhibitedError)
def stateupdateprohibited_error(context, request):
    @request.after
    def adjust_status(response):
        response.status = 422

    return {
        'status': 'error',
        'message': "Please use 'statemachine' view to update state"
    }


@App.json(model=Exception)
def internalserver_error(context, request):
    @request.after
    def adjust_status(response):
        response.status = 500

    logger.error(traceback.format_exc())

    return {
        'status': 'error',
        'message': "Internal server error"
    }
