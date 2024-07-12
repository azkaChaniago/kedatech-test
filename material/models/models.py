# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Material(models.Model):
    _name = 'material.material'
    _description = 'Material'

    name = fields.Char()
    code = fields.Char()
    type = fields.Selection([('fabric', 'Fabric'),
                             ('jeans', 'Jeans'),
                             ('cotton', 'Cotton')], default='fabric')
    buy_price = fields.Integer()
    supplier_id = fields.Many2one('res.partner')

    @api.constrains('buy_price')
    def _validate_buy_price(self):
        for record in self:
            if record.buy_price < 100:
                raise ValidationError("Buy Price value should not less than 100!")
