# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
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
