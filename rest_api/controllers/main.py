# -*- coding: utf-8 -*-
import functools
import logging

import odoo
from odoo import http
from odoo.exceptions import MissingError, AccessDenied
from odoo.http import request
from ..rest_exception import invalid_response, valid_response, invalid_token

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

DBNAME = odoo.tools.config.get('db_name')
if not DBNAME:
    _logger.warning("Warning: To proper setup OAuth - it's necessary to "
                    "set the parameter 'DBNAME' in flectra config file!")

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
        request.branch_ids = access_token_data.user_id.branch_ids
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
            _logger.error(err.args)
            return invalid_response(401, 'MissingError', err.args[1])
        
        except AccessDenied as err:
            _logger.error(err.args)
            return invalid_response(400, err.args[0], 'User authentication is invalid!')

        return valid_response(200, {
            'access_token': oauth.get('token'),
            'expired_in': oauth.get('expires')
        })
