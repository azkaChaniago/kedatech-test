# -*- coding: utf-8 -*-
import json

from odoo import http
from odoo.http import request, Response


class Material(http.Controller):
    
    @http.route(['/api/v1/material', '/api/v1/material/<int:id>'],
                auth='public', type="http", methods=['GET'])
    def get_material(self, id=None, **kw):
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
        
    @http.route('/api/v1/material', auth='public',
                type="http", methods=['POST'], csrf=False)
    def post_material(self, **kw):
        payload = json.loads(request.httprequest.data.decode('utf-8'))
        material = request.env['material.material']
        try:
            new_material = material.create({
                'code': payload.get('code'),
                'type': payload.get('type'),
                'buy_price': payload.get('buy_price'),
                'supplier_id': payload.get('supplier_id'),
            })
        except Exception as err:
            # Return the custom response as JSON
            return Response(
                json.dumps({ 'message': str(err)}),
                headers=[('Content-Type', 'application/json')],
                content_type='application/json;charset=utf-8'
            )
        if new_material:
            return Response(
                json.dumps({ 'message': 'OK' }),
                headers=[('Content-Type', 'application/json')],
                content_type='application/json;charset=utf-8'
            )
            
        return { 'message': 'Failed' }
        
    @http.route('/api/v1/material/<int:id>', auth='public',
                type="json", methods=['PATCH', 'PUT'])
    def put_material(self, id=None, **kw):
        payload = request.jsonrequest
        material = request.env['material.material']
        material = material.search([('id', '=', id)])

        if material:
            material.write({
                'code': payload.get('code'),
                'type': payload.get('type'),
                'buy_price': payload.get('buy_price'),
                'supplier_id': payload.get('supplier_id'),
            })
            return { 'message': 'Success' }
        else:
            return { 'message': 'Not Found!'}


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
