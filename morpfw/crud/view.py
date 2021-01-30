import json
import logging
import os
import sys
import traceback
from urllib.parse import urlencode

from jsonpath_ng import parse as jsonpath_parse
from morepath.request import Request
from transitions import MachineError
from webob.exc import HTTPForbidden, HTTPInternalServerError, HTTPNotFound

from . import permission
from .app import App
from .errors import (
    AlreadyExistsError,
    FieldValidationError,
    StateUpdateProhibitedError,
    UnprocessableError,
    ValidationError,
)
from .model import Collection, Model
from .validator import get_data, validate_schema

logger = logging.getLogger("morp")


@get_data.register(model=Collection, request=Request)
def get_collection_data(model, request):
    return request.json


@App.json(model=Collection, permission=permission.View)
def schema(context, request):
    return context.json()


@App.json(model=Collection, name="aggregate", permission=permission.Aggregate)
def aggregate(context, request):
    if not context.aggregate_view_enabled:
        raise HTTPNotFound()

    qs = request.GET.get("q", "").strip()

    query = None

    aggregateprovider = context.aggregateprovider()

    if qs:
        query = aggregateprovider.parse_query(qs)

    order_by = request.GET.get("order_by", None)
    limit = request.GET.get("limit", None)

    gs = request.GET.get("group", "").strip()
    group = None
    if gs:
        group = aggregateprovider.parse_group(gs)

    if order_by:
        order_by = order_by.split(":")
        if len(order_by) == 1:
            order_by = order_by + ["asc"]
    objs = context.aggregate(query, group=group, order_by=order_by, limit=limit)
    return objs


@App.json(model=Collection, name="search", permission=permission.Search)
def search(context, request):
    if not context.search_view_enabled:
        raise HTTPNotFound()

    qs = request.GET.get("q", "").strip()

    query = None
    if qs:
        searchprovider = context.searchprovider()
        query = searchprovider.parse_query(qs)

    default_limit = request.app.get_config("morpfw.crud.search.default_limit", 20)
    max_limit = request.app.get_config("morpfw.crud.search.max_limit", 100)
    limit = int(request.GET.get("limit", 0)) or default_limit
    if limit > max_limit:
        limit = max_limit
    offset = int(request.GET.get("offset", 0))
    order_by = request.GET.get("order_by", None)
    select = request.GET.get("select", None)
    if order_by:
        order_by = order_by.split(":")
        if len(order_by) == 1:
            order_by = order_by + ["asc"]
    # HACK: +1 to ensure next page links is triggered
    searchlimit = limit
    if limit:
        searchlimit = limit + 1
    objs = context.search(
        query, offset=offset, limit=searchlimit, order_by=order_by, secure=True
    )
    # and limit back to actual limit
    objs = [obj.json() for obj in objs]
    has_next = False
    if limit:
        if len(objs) > limit:
            has_next = True
        objs = objs[:limit]
    if select:
        expr = jsonpath_parse(select)
        results = []
        for obj in objs:
            results.append([match.value for match in expr.find(obj["data"])])
    else:
        results = objs
    params = {}
    if select:
        params["select"] = select
    if limit:
        params["limit"] = limit
    if order_by:
        params["order_by"] = request.GET.get("order_by", "")
    params["offset"] = offset + (limit or 0)
    qs = urlencode(params)
    res = {
        "results": results,
        "q": query,
        "limit": limit,
        "order_by": order_by,
        "offset": offset,
        "result_count": len(results),
    }
    if has_next:
        res.setdefault("links", [])
        res["links"].append(
            {"rel": "next", "href": request.link(context, "+search?%s" % qs)}
        )
    if offset > 0:
        prev_offset = offset - (limit or 0)
        if prev_offset < 0:
            prev_offset = 0
        params["offset"] = prev_offset
        qs = urlencode(params)
        res.setdefault("links", [])
        res["links"].append(
            {"rel": "previous", "href": request.link(context, "+search?%s" % qs)}
        )
    return res


@App.json(model=Collection, request_method="POST", permission=permission.Create)
def create(context, request):
    if not context.create_view_enabled:
        raise HTTPNotFound()
    obj = context.create(request.json, secure=True)
    return obj.json()


@get_data.register(model=Model, request=Request)
def get_obj_data(model, request):
    data = model.json()["data"]
    data.update(request.json)
    return data


@App.json(model=Model, permission=permission.View)
def read(context, request):
    select = request.GET.get("select", None)
    obj = context.json()
    if select:
        expr = jsonpath_parse(select)
        obj = [match.value for match in expr.find(obj["data"])]
    return obj


@App.json(model=Model, request_method="PATCH", permission=permission.Edit)
def update(context, request):
    if not context.update_view_enabled:
        raise HTTPNotFound()

    context.update(request.json, secure=True)
    return {"status": "success"}


@App.json(
    model=Model,
    name="statemachine",
    request_method="POST",
    permission=permission.StateUpdate,
)
def statemachine(context, request):
    if not context.statemachine_view_enabled:
        raise HTTPNotFound()

    sm = context.statemachine()
    transition = request.json["transition"]
    transition_callable = getattr(sm, transition, None)
    if transition_callable and (transition not in sm.get_triggers()):

        @request.after
        def adjust_status(response):
            response.status = 422

        return {
            "status": "error",
            "message": "Transition %s is not allowed" % transition,
        }

    if not transition_callable:

        @request.after
        def adjust_status(response):
            response.status = 422

        return {"status": "error", "message": "Unknown transition %s" % transition}
    transition_callable()
    context.save()
    return {"status": "success"}


@App.json(model=Model, request_method="DELETE", permission=permission.Delete)
def delete(context, request):
    if not context.delete_view_enabled:
        raise HTTPNotFound()

    context.delete()
    return {"status": "success"}


@App.view(model=Model, name="blobs", permission=permission.View)
def get_blob(context, request):
    field = request.GET.get("field", None)
    if field is None or context.storage.blobstorage is None:
        raise HTTPNotFound()

    if field not in context.blob_fields:
        raise HTTPNotFound()

    blob = context.get_blob(field)

    if blob is None:
        raise HTTPNotFound()

    return request.get_response(blob)


@App.json(model=Model, name="blobs", request_method="POST", permission=permission.Edit)
def put_blob(context, request):
    field = request.GET.get("field", None)
    if field is None or context.storage.blobstorage is None:
        raise HTTPNotFound()

    if field not in context.blob_fields:
        raise HTTPNotFound()

    upload = request.POST.get("upload")

    if upload is None:
        raise UnprocessableError()

    context.put_blob(
        field,
        filename=os.path.basename(upload.filename),
        mimetype=upload.type,
        fileobj=upload.file,
    )
    return {"status": "success"}


@App.json(
    model=Model, name="blobs", request_method="DELETE", permission=permission.Edit
)
def delete_blob(context, request):
    field = request.GET.get("field", None)
    if field is None or context.storage.blobstorage is None:
        raise HTTPNotFound()

    if field not in context.blob_fields:
        raise HTTPNotFound()

    context.delete_blob(field)

    return {"status": "success"}


@App.json(model=Model, name="xattr-schema", permission=permission.View)
def get_xattr_schema(context, request):
    if not context.xattr_view_enabled:
        raise HTTPNotFound()

    provider = context.xattrprovider()
    return provider.jsonschema()


@App.json(model=Model, name="xattr", permission=permission.View)
def get_xattr(context, request):
    if not context.xattr_view_enabled:
        raise HTTPNotFound()

    provider = context.xattrprovider()
    return provider.as_json()


@App.json(model=Model, name="xattr", permission=permission.View, request_method="PATCH")
def set_xattr(context, request):
    if not context.xattr_view_enabled:
        raise HTTPNotFound()

    provider = context.xattrprovider()
    provider.process_update(request.json)
    return {"status": "success"}


@App.json(model=AlreadyExistsError)
def alreadyexists_error(context, request):
    @request.after
    def adjust_status(response):
        response.status = 422

    #   FIXME: should log this when a config for DEBUG_SECURITY is enabled
    #    logger.error(traceback.format_exc())
    #    print(traceback.format_exc())

    return {
        "status": "error",
        "message": "Object Already Exists : %s" % context.message,
    }


@App.json(model=HTTPForbidden)
def forbidden_error(context, request):
    @request.after
    def adjust_status(response):
        response.status = 403

    #   FIXME: should log this when a config for DEBUG_SECURITY is enabled
    #    logger.error(traceback.format_exc())
    return {"status": "error", "message": "Access Denied : %s" % request.path}


@App.json(model=HTTPNotFound)
def httpnotfound_error(context, request):
    @request.after
    def adjust_status(response):
        response.status = 404

    return {"status": "error", "message": "Object Not Found : %s" % request.path}


@App.json(model=ValidationError)
def validation_error(context, request):
    @request.after
    def adjust_status(response):
        response.status = 422

    field_errors = []
    form_errors = []
    for e in context.field_errors:
        field_errors.append({"field": e.path, "message": e.message})

    for e in context.form_errors:
        form_errors.append(e.message)

    #   FIXME: should log this when a config for DEBUG_SECURITY is enabled
    # logger.error(traceback.format_exc())

    return {"status": "error", "field_errors": field_errors, "form_errors": form_errors}


@App.json(model=FieldValidationError)
def field_validation_error(context, request):
    @request.after
    def adjust_status(response):
        response.status = 422

    form_errors = [context.args[0]]

    return {"status": "error", "field_errors": [], "form_errors": form_errors}


@App.json(model=MachineError)
def statemachine_error(context, request):
    @request.after
    def adjust_status(response):
        response.status = 422

    return {"status": "error", "message": context.value}


@App.json(model=StateUpdateProhibitedError)
def stateupdateprohibited_error(context, request):
    @request.after
    def adjust_status(response):
        response.status = 422

    return {
        "status": "error",
        "message": "Please use 'statemachine' view to update state",
    }


@App.json(model=Exception)
def internalserver_error(context, request):
    @request.after
    def adjust_status(response):
        response.status = 500

    tb = traceback.format_exc()
    logger.error(tb)

    return {
        "status": "error",
        "message": "Internal server error",
        "traceback": tb.split("\n"),
    }


@App.json(model=UnprocessableError)
def unprocessable_error(context, request):
    @request.after
    def adjust_status(response):
        response.status = 422

    return {"status": "error", "message": "%s" % (context.message)}
