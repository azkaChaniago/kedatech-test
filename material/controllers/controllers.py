# -*- coding: utf-8 -*-
import json

from odoo import http
from odoo.http import request, Response


class Material(http.Controller):
    
    @http.route(['/api/v1/material', '/api/v1/material/<int:id>'], auth='public', type="http", methods=['GET'])
    def material(self, id=None, **kw):
        material = request.env['material.material']
        domain = [('id', '=', id)] if id else []
        result = material.search(domain)
        if result:
            payload = []
            for res in result:
                payload.append({
                    'name': res.name,
                    'code': res.code,
                    'type': res.type,
                    'buy_price': res.buy_price,
                    'supplier_id': res.supplier_id.name
                })
            return Response(response=json.dumps(payload), status=200)
        else:
            return Response('Not Found', status=404)


    # @http.route('/api/v1/material/objects/', auth='public')
    # def list(self, **kw):
    #     return http.request.render('material.listing', {
    #         'root': '/api/v1/material',
    #         'objects': http.request.env['material.material'].search([]),
    #     })

    # @http.route('/api/v1/material/objects/<model("material.material"):obj>/', auth='public')
    # def object(self, obj, **kw):
    #     return http.request.render('material.object', {
    #         'object': obj
    #     })
