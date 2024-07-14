# -*- coding: utf-8 -*-
import ast
import functools
import logging

import odoo
from odoo import http
from odoo.exceptions import MissingError, AccessDenied
from odoo.http import request
from odoo.addons.rest_api.utilities.exceptions import (
    invalid_response,
    valid_response,
    invalid_token,
    rest_api_unavailable,
    modal_not_found,
    invalid_object_id,
    object_not_found,
    object_not_found_all,
    no_object_created,
    no_object_updated,
    no_object_deleted,
)

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

DBNAME = odoo.tools.config.get('db_name')
if not DBNAME:
    _logger.warning("Warning: To proper setup OAuth - it's necessary to "
                    "set the parameter 'DBNAME' in odoo config file!")
    
def object_read_one(model_name, rec_id, params, status_code):
    fields = []
    if 'field' in params:
        fields += ast.literal_eval(params['field'])
    try:
        rec_id = int(rec_id)
    except Exception as e:
        rec_id = False

    if not rec_id:
        return invalid_object_id()
    data = request.env[model_name].search_read(domain=[('id', '=', rec_id)], fields=fields)
    if data:
        return valid_response(status=status_code, data=data)
    else:
        return object_not_found(rec_id, model_name)
    
def object_read(model_name, params, status_code):
    domain = []
    fields = []
    offset = 0
    limit = None
    order = None
    if 'filters' in params:
        domain += ast.literal_eval(params['filters'])
    if 'field' in params:
        fields += ast.literal_eval(params['field'])
    if 'offset' in params:
        offset = int(params['offset'])
    if 'limit' in params:
        limit = int(params['limit'])
    if 'order' in params:
        order = params['order']

    data = request.env[model_name].search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
    if data:
        return valid_response(status=status_code, data={
            'count': len(data),
            'results': data
        })
    else:
        return object_not_found_all(model_name)

def object_create_one(model_name, data, status_code):
    try:
        res = request.env[model_name].create(data)
    except Exception as e:
        return no_object_created(e)
    if res:
        return valid_response(status_code, {'id': res.id})


def object_update_one(model_name, rec_id, data, status_code):
    try:
        rec_id = int(rec_id)
    except Exception as e:
        rec_id = None

    if not rec_id:
        return invalid_object_id()

    try:
        res = request.env[model_name].search([('id', '=', rec_id)])
        if res:
            res.write(data)
        else:
            return object_not_found(rec_id, model_name)
    except Exception as e:
        return no_object_updated(e)
    if res:
        return valid_response(status_code, {'desc': 'Record Updated successfully!', 'update': True})


def object_delete_one(model_name, rec_id, status_code):
    try:
        rec_id = int(rec_id)
    except Exception as e:
        rec_id = None

    if not rec_id:
        return invalid_object_id()

    try:
        res = request.env[model_name].search([('id', '=', rec_id)])
        if res:
            res.unlink()
        else:
            return object_not_found(rec_id, model_name)
    except Exception as e:
        return no_object_deleted(e)
    if res:
        return valid_response(status_code, {'desc': 'Record Successfully Deleted!', 'delete': True})

def verify_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        authorization = request.httprequest.headers.get('Authorization')
        grant_type = authorization.split(' ')[0]
        
        if not grant_type:
            return invalid_response(401,
                'grant_type_not_found',
                'Missing Grant Type in request header!')

        access_token = authorization.split(' ')[-1]
        if not access_token:
            return invalid_token()

        access_token_data = request.env['oauth.access_token'].sudo().search([
            ('token', '=', access_token),
            ('grant_type', '=', grant_type.lower())])
        
        if not access_token_data or access_token_data.is_expired():
            return invalid_token()

        request.session.uid = access_token_data.user_id.id
        request.uid = access_token_data.user_id.id
        return func(self, *args, **kwargs)

    return wrap

class JWTControllerREST(http.Controller):

    @http.route('/api/oauth2/get_tokens', methods=['POST'], type='http',
                auth='public', csrf=False, json_rpc=False)
    def get_jwt_token(self, **kwargs):
        # verify client authentication
        try:
            request.session.authenticate(
                DBNAME,
                kwargs.get('username'),
                kwargs.get('password')
            )
            uid = request.session.uid
            
        except Exception as err:
            _logger.error(err.args)
            return invalid_response(400, 'Internal Server Error', err.args[0])

        if not uid:
            info = 'Username or Password is invalid!'
            _logger.error(info)
            return invalid_response(401, 'AccessDenied', info)

        # verify body and user oauth credentials sends by client
        # generate tpken if body and user is verified
        try:
            oauth = request.env['oauth.access_token']._generate_jwt(uid, kwargs)
        
        except MissingError as err:
            _logger.error(err.name)
            return invalid_response(401, 'MissingError', err.name)
        
        except AccessDenied as err:
            _logger.error(err.args)
            return invalid_response(400, err.args, 'User authentication is invalid!')

        return valid_response(200, {
            'access_token': oauth.get('token'),
            'expired_in': oauth.get('expires')
        })
    
    @http.route([
        '/api/v1/<string:model_name>',
        '/api/v1/<string:model_name>/<int:id>'
    ], type='http', auth="none", methods=['POST', 'GET', 'PUT', 'DELETE'],
        csrf=False)
    @verify_token
    def restapi_access_token(self, model_name=False, id=False, **post):
        Model = request.env['ir.model']
        Model_id = Model.sudo().search([('model', '=', model_name)], limit=1)

        if Model_id:
            if Model_id.rest_api:
                return getattr(self, '%s_data' % (
                    request.httprequest.method).lower())(
                    model_name=model_name, id=id, **post)
            else:
                return rest_api_unavailable(model_name)
        return modal_not_found(model_name)

    def get_data(self, model_name=False, id=False, **get):
        if id:
            return object_read_one(model_name, id, get, status_code=200)
        return object_read(model_name, get, status_code=200)

    def put_data(self, model_name=False, id=False, **put):
        return object_update_one(model_name, id, put, status_code=200)

    def post_data(self, model_name=False, **post):
        return object_create_one(model_name, post, status_code=200)

    def delete_data(self, model_name=False, id=False):
        return object_delete_one(model_name, id, status_code=200)
