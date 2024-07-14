# -*- coding: utf-8 -*-

from odoo.tests.common import SavepointCase
from odoo.exceptions import ValidationError
from odoo.tests import tagged

# The CI will run these tests after all the modules are installed,
# not right after installing the one defining it.
@tagged('post_install', '-at_install')
class MaterialTestCase(SavepointCase):

    @classmethod
    def setUpClass(cls):
        # add env on cls and many other things
        super(MaterialTestCase, cls).setUpClass()

        # create the data for each tests. By doing it in the setUpClass instead
        # of in a setUp or in each test case, we reduce the testing time and
        # the duplication of code.
        cls.properties = cls.env['material.material'].create([
            {'code': 'A001', 'buy_price': 200, 'type': 'jeans'},
            {'code': 'A002', 'buy_price': 400, 'type': 'fabric'},
            {'code': 'A003', 'buy_price': 270, 'type': 'cotton'},
        ])


    def test_create(self):
        """Test that everything behaves like it should when creating a material."""
        self.assertRecordValues(self.properties, [
            {'code': 'A001', 'buy_price': 200, 'type': 'jeans'},
            {'code': 'A002', 'buy_price': 400, 'type': 'fabric'},
            {'code': 'A003', 'buy_price': 270, 'type': 'cotton'},
        ])

    def test_constrains_buy_price(self):
        with self.assertRaises(ValidationError):
            self.properties.create([
                {'code': 'A003', 'buy_price': 70, 'type': 'cotton'},
            ])