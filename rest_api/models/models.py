# -*- coding: utf-8 -*-

import hashlib
import jwt
import logging

from datetime import datetime, timedelta
from jwt.exceptions import ExpiredSignatureError

from odoo import api, fields, models, _
from odoo.exceptions import MissingError, UserError
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
        if not self.login or not self.partner_id:
            raise UserError("Login and Partner field should not be empty!")
        
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
        now = payload.pop('now') if payload.get('now') else datetime.now()
        oauth = self.env['oauth.access_token'].sudo().search([
            ('user_id', '=', user_id),
            ('grant_type', '=', payload.get('grant_type'))
        ], order='id DESC', limit=1)
        if not oauth:
            oauth = self.env['oauth.access_token'].sudo().create({
                'user_id': user_id,
                'grant_type': payload.get('grant_type'),
                'token': hashlib.sha256().hexdigest(),
                'expires': now,
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

        expires = now + timedelta(seconds=1200)
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
        refresh = False
        now = datetime.now()
        salt = hashlib.sha512(self.user_id.login.encode('utf-8')).hexdigest()
        try:
            refresh = jwt.decode(self.token, salt, algorithm=['HS256'])

        except ExpiredSignatureError as err:
            _logger.warning(err.args[0])
            refresh = self._generate_jwt(self.user_id.id, {
                'grant_type': self.grant_type,
                'client_id': self.user_id.client_id,
                'client_secret': self.user_id.client_secret,
                'now': now
            })

        client_id = self.user_id.client_id
        client_secret = self.user_id.client_secret
        client_id = refresh.get('client_id')
        client_secret = refresh.get('client_secret')

        if client_id == client_id and client_secret == client_secret:
            refresh = self.sudo().write({
                'expires': now.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            })

        return refresh
