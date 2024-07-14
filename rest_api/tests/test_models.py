# -*- coding: utf-8 -*-
import hashlib
import jwt

from datetime import datetime, timedelta

from odoo.exceptions import UserError, MissingError
from odoo.tests.common import TransactionCase, tagged


# The CI will run these tests after all the modules are installed,
# not right after installing the one defining it.
@tagged('post_install', '-at_install')
class TestResUsers(TransactionCase):
    
    def test_action_generate_credentials(self):
        """ Check name_search on user. """
        User = self.env['res.users']
        test_user = User.create({ 'name': 'Flad the Impaler', 'login': 'Flad' })
        test_user.write({'partner_id': False})
        
        with self.assertRaises(UserError):
            test_user.action_generate_credentials()

@tagged('post_install', '-at_install')
class TestOauth(TransactionCase):

    def create_test_user(self):
        User = self.env['res.users']
        return User.create({
            'name': 'Flad the Impaler',
            'login': 'Flad',
        })
    
    def create_test_oauth(self, test_user):
        Oauth = self.env['oauth.access_token']
        return Oauth.create({
            'user_id': test_user.id,
            'grant_type': 'bearer',
            'token': hashlib.sha256().hexdigest(),
            'expires': datetime.now(),
        })
    
    def test_generate_jwt_client_id_missing(self):
        test_user = self.create_test_user()
        secret = f'{test_user.partner_id}{datetime.now().isoformat()}'
        test_user.client_secret = hashlib.sha256(secret.encode('utf-8')).hexdigest()
        
        test_oauth = self.create_test_oauth(test_user)
        
        with self.assertRaises(MissingError):
            test_oauth._generate_jwt(test_user.id, {'grant_type': 'bearer'})
    
    def test_generate_jwt_client_secret_missing(self):
        test_user = self.create_test_user()
        client = f'{test_user.login}{datetime.now().isoformat()}'
        test_user.client_id = hashlib.sha256(client.encode('utf-8')).hexdigest()

        test_oauth = self.create_test_oauth(test_user)
        
        with self.assertRaises(MissingError):
            test_oauth._generate_jwt(test_user.id, {'grant_type': 'bearer'})

    def test_generate_jwt_is_success(self):
        now = datetime.now()

        test_user = self.create_test_user()
        client = f'{test_user.login}{now.isoformat()}'
        secret = f'{test_user.partner_id}{now.isoformat()}'
        test_user.client_id = hashlib.sha256(client.encode('utf-8')).hexdigest()
        test_user.client_secret = hashlib.sha256(secret.encode('utf-8')).hexdigest()

        test_oauth = self.create_test_oauth(test_user)

        payload = {
            'exp': timedelta(seconds=1200).seconds,
            'username': test_user.login,
            'client_id': test_user.client_id,
            'client_secret': test_user.client_secret,
        }

        expires = now + timedelta(seconds=1200)
        salt = hashlib.sha512(f'{test_user.login}{expires.isoformat()}'.encode('utf-8')).hexdigest()
        vals = {
            'token': jwt.encode(payload, salt, algorithm='HS256'),
            'expires': expires,
            'scope': 'read write'
        }
        test_oauth.sudo().write(vals)
        vals.update({'expires': timedelta(seconds=1200).seconds})
        payload['now'] = now

        self.assertEqual(test_oauth._generate_jwt(test_user.id, payload), vals)
