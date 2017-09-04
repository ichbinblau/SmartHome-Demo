# -*- coding: utf-8 -*-
"""
CRUD operation for activity model
"""
from DB.models import Activity
from DB.api import dbutils as utils
from DB.api import database

RESP_FIELDS = ['id', 'resource_id', 'total', 'created_at']
SRC_EXISTED_FIELD = {
    'resource_id': 'resource_id',
    'total': 'total',
    'created_at': 'created_at'
}


@database.run_in_session()
@utils.wrap_to_dict(RESP_FIELDS)
def new(session, src_dic, content={}):
    for k, v in SRC_EXISTED_FIELD.items():
        content[k] = src_dic.get(v, None)
    return utils.add_db_object(session, Activity, **content)


@utils.supported_filters(optional_support_keys=['id', 'resource_id', 'total'])
@database.run_in_session()
@utils.wrap_to_dict(RESP_FIELDS)
def get_activity(session=None, exception_when_missing=True,  **kwargs):
    """
    :param session:
    :param exception_when_missing: raise exception when missing
    :return:get field of the resource
    """
    return utils.get_db_object(
        session, Activity, exception_when_missing, **kwargs)


@utils.supported_filters(optional_support_keys=['id', 'resource_id'])
@database.run_in_session()
@utils.wrap_to_dict(RESP_FIELDS)
def list_activity(session=None, **filters):
    """
    :param session:
    :param filters:
    :return: list blocks
    """
    return utils.list_db_objects(session, Activity, **filters)


@utils.wrap_to_dict(RESP_FIELDS)
def _update_activity(session, resource_id, **kwargs):
    res = utils.get_db_object(session, Activity, resource_id=resource_id)
    return utils.update_db_object(session, res, **kwargs)


@utils.supported_filters(optional_support_keys=['id', 'resource_id', 'total'])
@database.run_in_session()
def update_activity(session, resource_id, **kwargs):
    return _update_activity(
        session, resource_id, **kwargs
    )
