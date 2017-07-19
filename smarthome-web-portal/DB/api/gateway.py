# -*- coding: utf-8 -*-
"""
CRUD operation for gateway model
"""
from DB.api import database
from DB.models import Gateway
from DB.api import dbutils as utils

RESP_FIELDS = ['id', 'name', 'url', 'address', 'latitude', 'longitude', 'status', 'created_at']
SRC_EXISTED_FIELD = {
    'id': 'id',
    'name': 'name',
    'url': 'url',
    'address': 'address',
    'latitude': 'latitude',
    'longitude': 'longitude',
    'status': 'status',
    'created_at': 'created_at'
}


@database.run_in_session()
@utils.wrap_to_dict(['id'])
def add_gateway(session, src_dic, content={}):
    for k, v in SRC_EXISTED_FIELD.items():
        content[k] = src_dic.get(v, None)
    return utils.add_db_object(session, Gateway, **content)


@utils.supported_filters(optional_support_keys=['gateway_id', 'name', 'exception_when_missing'])
def _get_gateway(session, gateway_id, exception_when_missing=True):
    return utils.get_db_object(session, Gateway, exception_when_missing=exception_when_missing, id=gateway_id)


@database.run_in_session()
@utils.wrap_to_dict(['latitude', 'longitude', 'url', 'id'])
def get_gateway(session, gateway_id):
    return _get_gateway(session, gateway_id)


@database.run_in_session()
@utils.wrap_to_dict(['id', 'name', 'address', 'latitude', 'longitude', 'status'])
def list_gateways(session,  **kwargs):
    return utils.list_db_objects(session, Gateway, **kwargs)
