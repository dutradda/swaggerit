# MIT License

# Copyright (c) 2016 Diogo Dutra <dutradda@gmail.com>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from swaggerit.json_builder import JsonBuilder
from swaggerit.utils import build_validator, set_logger
from swaggerit.request import SwaggerRequest
from swaggerit.response import SwaggerResponse
from jsonschema import ValidationError
from copy import deepcopy
import ujson


class SwaggerMethod(object):

    def __init__(self, operation, schema, definitions, schema_dir, *, authorizer=None):
        set_logger(self)
        self._operation = operation
        self._body_validator = None
        self._path_validator = None
        self._query_validator = None
        self._headers_validator = None
        self._schema_dir = schema_dir
        self._body_required = False
        self._has_body_parameter = False
        self.auth_required = False
        self.authorizer = authorizer

        query_schema = self._build_default_schema()
        path_schema = self._build_default_schema()
        headers_schema = self._build_default_schema()

        for parameter in schema.get('parameters', []):
            if parameter['in'] == 'body':
                if definitions:
                    body_schema = deepcopy(parameter['schema'])
                    body_schema.update({'definitions': definitions})
                else:
                    body_schema = parameter['schema']

                self._body_validator = build_validator(body_schema, self._schema_dir)
                self._body_required = parameter.get('required', False)
                self._has_body_parameter = True

            elif parameter['in'] == 'path':
                self._set_parameter_on_schema(parameter, path_schema)

            elif parameter['in'] == 'query':
                self._set_parameter_on_schema(parameter, query_schema)

            elif parameter['in'] == 'header':
                if parameter['name'].lower() != 'authorization':
                    self._set_parameter_on_schema(parameter, headers_schema)

                elif self.authorizer == None:
                        raise ValidationError("'authorizer' is a required attribute when "
                                              "'Authorization' header is setted.")

                else:
                    self.auth_required = self._requires_auth(parameter)

        if path_schema['properties']:
            self._path_validator = build_validator(path_schema, self._schema_dir)

        if query_schema['properties']:
            self._query_validator = build_validator(query_schema, self._schema_dir)

        if headers_schema['properties']:
            self._headers_validator = build_validator(headers_schema, self._schema_dir)

    def _build_default_schema(self):
        return {'type': 'object', 'required': [], 'properties': {}}

    def _set_parameter_on_schema(self, parameter, schema):
        name = parameter['name'].lower()
        property_ = {'type': parameter['type']}

        if parameter['type'] == 'array':
            items = parameter.get('items', {})
            if items:
                property_['items'] = items

        if parameter['type'] == 'object':
            obj_schema = parameter.get('schema', {})
            if obj_schema:
                property_.update(obj_schema)

        if parameter.get('required'):
            schema['required'].append(name)

        schema['properties'][name] = property_

    def _requires_auth(self, param):
            return self.auth_required or param.get('required')

    async def __call__(self, req, session):
        denied = await self._authorize(req, session)
        if denied is not None:
            return denied

        response_headers = {'content-type': 'application/json'}

        try:
            body_params = await self._build_body_params(req)
            query_params = self._build_non_body_params(self._query_validator, req.query)
            path_params = self._build_non_body_params(self._path_validator,
                                                               req.path_params)
            headers_params = self._build_non_body_params(self._headers_validator, dict(req.headers))
        except ValidationError as error:
            return self._valdation_error_to_response(error, response_headers)

        req = SwaggerRequest(
            req.url,
            req.method,
            path_params=path_params,
            query=query_params,
            headers=headers_params,
            body=body_params,
            body_schema=self._body_validator.schema if self._body_validator else None,
            context=req.context
        )

        try:
            if session is None:
                resp = await self._operation(req)
            else:
                resp = await self._operation(req, session)

        except ValidationError as error:
            return self._valdation_error_to_response(error, response_headers)

        except Exception as error:
            body = ujson.dumps({'message': 'Something unexpected happened'})
            self._logger.exception('Unexpected')
            return SwaggerResponse(500, body=body, headers=response_headers)

        else:
            if resp.headers.get('content-type') is None:
                resp.headers.update(response_headers)
            return resp

    def _valdation_error_to_response(self, error, headers):
        if error.absolute_path or error.absolute_schema_path:
            message = '{}. Failed validating instance{} for schema{}'.format(
                error.message,
                self._format_error_path(error.absolute_path),
                self._format_error_path(error.absolute_schema_path)
            )
        else:
            message = error.message

        body = {
            'message': message
        }
        if isinstance(error.schema, dict) and len(error.schema):
            body['schema'] = error.schema
        if error.instance:
            body['instance'] = error.instance
        return SwaggerResponse(400, body=ujson.dumps(body), headers=headers)

    def _format_error_path(self, path):
        path = [str(p) for p in path]
        return ("['" + "']['".join(path) + "']") if path else ''

    async def _authorize(self, req, session):
        authorization = req.headers.get('authorization')

        if self.auth_required or (self.authorizer and authorization is not None):
            response = await self.authorizer(req, session)
            if response is not None:
                return response

    async def _build_body_params(self, req):
        content_type = req.headers.get('content-type')
        if content_type is None and req.body is not None:
            body, _ = await self._cast_body(req.body)
            raise ValidationError('Request content_type is missing', instance=body)

        elif self._body_required and req.body is None:
            raise ValidationError('Request body is missing', instance=req.body)

        elif content_type is not None and 'application/json' in content_type:
            if req.body is None:
                raise ValidationError(
                    "Request body must be setted when 'content-type' header is setted",
                    instance=req.body
                )

            body, error = await self._cast_body(req.body)

            if not self._has_body_parameter:
                raise ValidationError('Request body is not acceptable', instance=body)

            if error is not None:
                raise ValidationError(str(error), instance=body)

            if self._body_validator:
                self._body_validator.validate(body)

            return body

        else:
            return req.body

    async def _cast_body(self, body):
        body = (await body.read()).decode()
        try:
            return (ujson.loads(body), None)
        except Exception as error:
            return body, error

    def _build_non_body_params(self, validator, params):
        if validator:
            for param_name, prop in validator.schema['properties'].items():
                param = params.get(param_name)

                if param is not None:
                    params[param_name] = JsonBuilder.build(param, prop)

            validator.validate(params)

        return params
