# -*- coding: utf-8 -*-

import json
import logging

from odoo.http import request
import werkzeug.wrappers

from jsonresponse import JsonRequestPatch


_logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (bytes, bytearray)):
            return obj.decode("utf-8")
        return json.JSONEncoder.default(self, obj)

def valid_response(status, data):
    return werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        response=json.dumps(data, cls=JSONEncoder),
    )

def invalid_response(status, error, info):
    _logger.error(info)
    response = {
        'error': error,
        'error_descrip': info,
    }

    return werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        response=json.dumps(response)
    )

def valid_response_api(status, data, message='Success'):
    response = {
        'status': 1,
        'message': message,
        'code': status,
        'data': data
    }
    if request.httprequest.content_type == 'application/json':
        request._json_response = JsonRequestPatch._json_response.__get__(request)
        return response

    return werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        response=json.dumps(response, cls=JSONEncoder),
    )


def invalid_response_api(status, error, info,message=None):
    _logger.error('%s - %s - %s' % (status, error, info))
    _logger.error(info)
    message = message
    if not message:
        message = 'Failed'
    if 'opt' in str(info) or 'syntax' in str(info):
        info = 'Error !, Please contact administrator if you think this is a mistake.'
    response = {
        'status': 0,
        'message': message,
        'code': status,
        'data': {
            'error': error,
            'error_descrip': info,
        }
    }
    if request.httprequest.content_type == 'application/json':
        request._json_response = JsonRequestPatch._json_response.__get__(
            request)
        return response

    return werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        response=json.dumps(response)
    )


def invalid_object_id():
    _logger.error("Invalid object 'id'!")
    return invalid_response(400, 'invalid_object_id', "Invalid object 'id'!")


def invalid_token():
    _logger.error("Token is expired or invalid!")
    return invalid_response(401, 'invalid_token', "Token is expired or invalid!")

def modal_not_found(modal_name):
    _logger.error("Not found object(s) in flectra!")
    return invalid_response(404, 'object_not_found_in_flectra',
                            "Modal " + modal_name + " Not Found!")

def rest_api_unavailable(modal_name):
    _logger.error("Not found object(s) in flectra!")
    return invalid_response(404, 'object_not_found_in_flectra',
                            "Enable Rest API For " + modal_name + "!")

def object_not_found_all(modal_name):
    _logger.error("Not found object(s) in flectra!")
    return invalid_response(404, 'object_not_found_in_flectra',
                            "No Record found in " + modal_name + "!")

def object_not_found(record_id, modal_name):
    _logger.error("Not found object(s) in flectra!")
    return invalid_response(404, 'object_not_found_in_flectra',
                            "Record " + str(record_id) + " Not found in " + modal_name + "!")


def unable_delete():
    _logger.error("Access Denied!")
    return invalid_response(403, "you don't have access to delete records for "
                               "this model", "Access Denied!")


def no_object_created(flectra_error):
    _logger.error("Not created object in flectra! ERROR: %s" % flectra_error)
    return invalid_response(500, 'not_created_object_in_flectra',
                          "Not created object in flectra! ERROR: %s" %
                          flectra_error)


def no_object_updated(flectra_error):
    _logger.error("Not updated object in flectra! ERROR: %s" % flectra_error)
    return invalid_response(500, 'not_updated_object_in_flectra',
                          "Object Not Updated! ERROR: %s" %
                          flectra_error)


def no_object_deleted(flectra_error):
    _logger.error("Not deleted object in flectra! ERROR: %s" % flectra_error)
    return invalid_response(500, 'not_deleted_object_in_flectra',
                          "Not deleted object in flectra! ERROR: %s" %
                          flectra_error)
