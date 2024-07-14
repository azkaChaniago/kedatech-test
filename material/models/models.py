# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class Material(models.Model):
    _name = 'material.material'
    _description = 'Material'

    name = fields.Char(default=lambda self: self.env['ir.sequence'].next_by_code('material.material'), required=1)
    code = fields.Char(required=1)
    type = fields.Selection([('fabric', 'Fabric'),
                             ('jeans', 'Jeans'),
                             ('cotton', 'Cotton')], default='fabric', required=1)
    buy_price = fields.Integer(required=1)
    supplier_id = fields.Many2one('res.partner', required=1)

    @api.constrains('buy_price')
    def _validate_buy_price(self):
        for record in self:
            if record.buy_price < 100:
                raise ValidationError("Buy Price value should not less than 100!")
            
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                raise UserError("Field code is empty!")
            
        return super().create(vals_list)
