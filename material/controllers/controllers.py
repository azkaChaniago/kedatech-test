# -*- coding: utf-8 -*-
# from odoo import http


# class Material(http.Controller):
#     @http.route('/material/material/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/material/material/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('material.listing', {
#             'root': '/material/material',
#             'objects': http.request.env['material.material'].search([]),
#         })

#     @http.route('/material/material/objects/<model("material.material"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('material.object', {
#             'object': obj
#         })
