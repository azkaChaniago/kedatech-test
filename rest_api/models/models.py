# -*- coding: utf-8 -*-

import hashlib
import jwt
import logging

from datetime import datetime, timedelta
from jwt.exceptions import ExpiredSignatureError

from odoo import api, fields, models, _
from odoo.exceptions import MissingError, AccessDenied
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

try:
    from oauthlib import common as oauthlib_common
except ImportError:
    _logger.warning(
        'OAuth library not found. If you plan to use it, '
        'please install the oauth library from '
        'https://pypi.python.org/pypi/oauthlib')



class IrModel(models.Model):
    _inherit = 'ir.model'

    rest_api = fields.Boolean('REST API', default=True,
                              help="Enable REST API for this object/model")
    

class Users(models.Model):
    _inherit = 'res.users'

    client_id = fields.Char()
    client_secret = fields.Char()
    token_ids = fields.One2many('oauth.access_token', 'user_id',
                                string="Access Tokens")
    
    def action_generate_credentials(self):
        now = datetime.now().isoformat()
        client = f'{self.login}{now}'
        secret = f'{self.partner_id}{now}'
        self.client_id = hashlib.sha256(client.encode('utf-8')).hexdigest()
        self.client_secret = hashlib.sha256(secret.encode('utf-8')).hexdigest()



class OauthAccessToken(models.Model):
    _name = 'oauth.access_token'

    token = fields.Char('Access Token', required=True)
    user_id = fields.Many2one('res.users', string='User', required=True)
    expires = fields.Datetime('Expires', required=True)
    scope = fields.Char('Scope')
    grant_type = fields.Selection([
        ('basic_auth', 'Basic Auth'),
        ('bearer', 'Bearer'),
        ('password', 'Password')
    ], default='bearer')

    @api.model
    def _get_access_token(self, user_id=None, create=False):
        if not user_id:
            user_id = self.env.user.id

        access_token = self.env['oauth.access_token'].sudo().search(
            [('user_id', '=', user_id)], order='id DESC', limit=1)
        if access_token:
            access_token = access_token[0]
            if access_token.is_expired():
                if create == True:
                    access_token = None
        if not access_token and create:
            expire_val = self.env.ref(
                'rest_api.oauth2_access_token_expires_in').sudo().value
            expires = datetime.now() + timedelta(seconds=int(expire_val))
            vals = {
                'user_id': user_id,
                'scope': 'userinfo',
                'expires': expires.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'token': oauthlib_common.generate_token(),
            }
            access_token = self.env['oauth.access_token'].sudo().create(vals)
            # we have to commit now, because /oauth2/tokeninfo could
            # be called before we finish current transaction.
            self._cr.commit()
        if not access_token:
            return None
        return access_token.token

    @api.model
    def _get_access_token_google(self, user_id=None, create=False):
        access_token = self.env['oauth.access_token'].sudo().search(
            [('user_id', '=', user_id)], order='id DESC', limit=1)
        if access_token:
            access_token = access_token[0]
            # if access_token.is_expired():
            #     access_token = None
        if not access_token and create:
            expire_val = self.env.ref(
                'rest_api.oauth2_access_token_expires_in').sudo().value
            expires = datetime.now() + timedelta(seconds=int(expire_val))
            vals = {
                'user_id': user_id,
                'scope': 'userinfo',
                'expires': expires.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'token': oauthlib_common.generate_token(),
            }
            access_token = self.env['oauth.access_token'].sudo().create(vals)
            # we have to commit now, because /oauth2/tokeninfo could
            # be called before we finish current transaction.
            self._cr.commit()
        if not access_token:
            return None
        return access_token.token

    @api.model
    def is_valid(self, scopes=None):
        """
        Checks if the access token is valid.

        :param scopes: An iterable containing the scopes to check or None
        """
        self.ensure_one()
        return not self.is_expired() and self._allow_scopes(scopes)

    @api.model
    def is_expired(self):
        self.ensure_one()
        return datetime.now() > fields.Datetime.from_string(self.expires)

    @api.model
    def _allow_scopes(self, scopes):
        self.ensure_one()
        if not scopes:
            return True

        provided_scopes = set(self.scope.split())
        resource_scopes = set(scopes)

        return resource_scopes.issubset(provided_scopes)

    @api.model
    def _generate_jwt(self, user_id, payload):
        
        oauth = self.env['oauth.access_token'].sudo().search([
            ('user_id', '=', user_id),
            ('grant_type', '=', payload.get('grant_type'))
        ], order='id DESC', limit=1)
        if not oauth:
            oauth = self.env['oauth.access_token'].sudo().create({
                'user_id': user_id,
                'grant_type': payload.get('grant_type'),
                'token': hashlib.sha256().hexdigest(),
                'expires': datetime.now(),
            })
        
        user = oauth.user_id
        if user.client_id != payload.get('client_id'):
            raise MissingError('client_id is not recognized!')
        
        if user.client_secret != payload.get('client_secret'):
            raise MissingError('client_secret is not recognized!')

        payload.update({
            'exp': timedelta(seconds=1200).seconds,
            'username': user.login,
            'client_id': user.client_id,
            'client_secret': user.client_secret
        })

        expires = datetime.now() + timedelta(seconds=1200)
        salt = hashlib.sha512(f'{user.login}{expires.isoformat()}'.encode('utf-8')).hexdigest()
        vals = {
            'token': jwt.encode(payload, salt, algorithm='HS256'),
            'expires': expires,
            'scope': 'read write'
        }
        oauth.sudo().write(vals)
        vals.update({'expires': timedelta(seconds=1200).seconds})

        return vals

    @api.model
    def _refresh_jwt(self):
        # TODO: should implement refresh token, therefore client could
        # TODO: retrieve token if the current request is less than refresh expired time

        refresh = False
        salt = hashlib.sha512(self.user_id.login.encode('utf-8')).hexdigest()
        try:
            refresh = jwt.decode(self.token, salt, algorithm=['HS256'])

        except ExpiredSignatureError as err:
            _logger.warning(err.args[0])
            refresh = self._generate_jwt(self.user_id.id, {
                'grant_type': self.grant_type,
                'client_id': self.user_id.client_id,
                'client_secret': self.user_id.client_secret
            })

        client_id = self.user_id.client_id
        client_secret = self.user_id.client_secret
        client_id = refresh.get('client_id')
        client_secret = refresh.get('client_secret')

        if client_id == client_id and client_secret == client_secret:
            expires = datetime.now()
            refresh = self.sudo().write({
                'expires': expires.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            })

        return refresh
