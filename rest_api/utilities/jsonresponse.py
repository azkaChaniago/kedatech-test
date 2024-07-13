# -*- coding: utf-8 -*-
import json
from odoo.http import JsonRequest, Response

SUCCESS_CODE = 0
FAILED_CODE = -1

# DO NOT ASK WHY NAMED AS Respapi
class Respapi:
    def __init__(self, code=None, message=None, data=None):
        self.code = code
        self.message = message
        self.data = data

    def error(code=FAILED_CODE, message=None, data=None):
        return Respapi(code=code, message=message, data=data)

    def success(code=SUCCESS_CODE, message=None, data=None):
        return Respapi(code=code, message=message, data=data)


class JsonRequestPatch(JsonRequest):

    def _json_response(self, result=None, error=None):
        default_code = 200
        mime = 'application/json'
        response = {}
        
        if error is not None:
            response = error
        if result is not None:
            response = result

        body = json.dumps(response)

        return Response(
            body, status=error and error.pop(
                'http_status', default_code) or default_code,
            headers=[('Content-Type', mime), ('Content-Length', len(body))]
        )
