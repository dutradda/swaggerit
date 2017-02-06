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


from swaggerit.method import SwaggerMethod
from swaggerit.response import SwaggerResponse
from swaggerit.models.orm.session import Session
from swaggerit.exceptions import SwaggerItAPIError
from swaggerit.constants import SWAGGER_TEMPLATE, SWAGGER_SCHEMA, HTTP_METHODS
from swaggerit.utils import set_logger
from collections import namedtuple, defaultdict
from jsonschema import Draft4Validator, ValidationError
from abc import ABCMeta, abstractmethod
from copy import deepcopy
import ujson
import re


class SwaggerAPI(metaclass=ABCMeta):

    def __init__(self, models, sqlalchemy_bind=None, redis_bind=None,
                 swagger_json_template=None, title=None, version='1.0.0',
                 authorizer=None, get_swagger_req_auth=True, swagger_doc_url='doc'):
        set_logger(self)
        self.authorizer = authorizer
        self._sqlalchemy_bind = sqlalchemy_bind
        self._redis_bind = redis_bind
        self._get_swagger_req_auth = get_swagger_req_auth

        self._set_swagger_json(swagger_json_template, title, version)
        self._set_models(models)
        self._set_swagger_doc(swagger_doc_url)

    def _set_swagger_json(self, swagger_json_template, title, version):
        self._validate_metadata(swagger_json_template, title, version)
        if swagger_json_template is None:
            swagger_json_template = deepcopy(SWAGGER_TEMPLATE)
            swagger_json_template['info']['title'] = title
            swagger_json_template['info']['version'] = version

        if swagger_json_template['paths']:
            raise SwaggerItAPIError("The Swagger Json 'paths' property will be populated "
                "by the 'models' contents. This property must be empty.")

        Draft4Validator(SWAGGER_SCHEMA).validate(swagger_json_template)

        self.swagger_json = defaultdict(dict)
        self.swagger_json.update(deepcopy(swagger_json_template))
        definitions = self.swagger_json.get('definitions', {})
        self.swagger_json['definitions'] = definitions

    def _validate_metadata(self, swagger_json_template, title, version):
        if bool(title is None) == bool(swagger_json_template is None):
            raise SwaggerItAPIError("One of 'title' or 'swagger_json_template' "
                                  "arguments must be setted.")

        if version != '1.0.0' and swagger_json_template is not None:
            raise SwaggerItAPIError("'version' argument can't be setted when "
                                  "'swagger_json_template' was setted.")

    def _set_models(self, models):
        self._models = set()
        for model in models:
            self.add_model(model)

        if not self.swagger_json['definitions']:
            self.swagger_json.pop('definitions')

    def add_model(self, model):
        if model.__api__ is not None:
            raise SwaggerItAPIError(
                "Model '{}' was already registered for '{}' API".format(
                    model.__name__, model.__api__.__class__.__name__
                ))

        self._models.add(model)
        self._set_model_routes(model)
        model.__api__ = self
        model_paths = deepcopy(model.__schema__)
        model_paths.pop('definitions', None)
        model_definitions = deepcopy(model.__schema__.get('definitions', {}))

        self._validate_model('paths', model_paths, model.__name__)
        self._validate_model('definitions', model_definitions, model.__name__)
        self.swagger_json['paths'].update(model_paths)
        self.swagger_json['definitions'].update(model_definitions)

    def _set_model_routes(self, model):
        for path, method, handler in self.get_model_methods(model):
            handler = self._set_handler_decorator(handler)
            self._set_route(path, method, handler)

    def get_model_methods(self, model):
        for path, path_schema in model.__schema__.items():
            if path != 'definitions':
                all_methods_parameters = path_schema.get('parameters', [])
                path = self._format_path(path)

                for method in HTTP_METHODS:
                    method_schema = path_schema.get(method)

                    if method_schema is not None:
                        method_schema = deepcopy(method_schema)
                        definitions = model.__schema__.get('definitions')
                        parameters = method_schema.get('parameters', [])
                        parameters.extend(all_methods_parameters)

                        method_schema['parameters'] = parameters
                        operation = getattr(model, method_schema['operationId'].split('.')[-1])
                        handler = SwaggerMethod(operation, method_schema,
                                               definitions, model.__schema_dir__,
                                               authorizer=self.authorizer)
                        yield path, method, handler

    def _validate_model(self, key_name, keys, model_name):
        for key in keys:
            if key in self.swagger_json[key_name]:
                raise SwaggerItAPIError("Duplicated {} '{}' for model '{}'"\
                                        .format(key_name, key, model_name))

    @abstractmethod
    def _set_handler_decorator(self, handler):
        pass

    def _method_decorator(self, method):
        async def _method_wrapper(req):
            response_headers = {'content-type': 'application/json'}
            session = self._build_session()

            try:
                response = await method(req, session)

            except ValidationError as error:
                body = {
                    'message': error.message
                }
                if isinstance(error.schema, dict) and len(error.schema):
                    body['schema'] = error.schema
                if error.instance:
                    body['instance'] = error.instance
                response = SwaggerResponse(400, body=ujson.dumps(body), headers=response_headers)

            except Exception as error:
                body = ujson.dumps({'message': 'Something unexpected happened'})
                self._logger.exception('ERROR Unexpected')
                response = SwaggerResponse(500, body=body, headers=response_headers)

            self._destroy_session(session)
            return response
        _method_wrapper.func = method
        return _method_wrapper

    @abstractmethod
    def _set_route(self, path, method, handler):
        pass

    def _format_path(self, path):
        return self._get_base_path() + path.rstrip('/')

    def _get_base_path(self):
        if getattr(self, '_base_path', None) == None:
            self._base_path = self.swagger_json.get('basePath', '').rstrip('/')

        return self._base_path

    def _build_session(self):
        return Session(bind=self._sqlalchemy_bind,
                       redis_bind=self._redis_bind,
                       loop=self.loop)

    def _destroy_session(self, session):
        if hasattr(session, 'close'):
            session.close()

    async def _authorize(self, req, session):
        if self.authorizer and self._get_swagger_req_auth:
            response = await self.authorizer(req, session)
            if response is not None:
                return response

    @abstractmethod
    def _set_swagger_doc(self, swagger_doc_url):
        pass
