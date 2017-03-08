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
from swaggerit.constants import SWAGGER_JSON_TEMPLATE, SWAGGER_SCHEMA, HTTP_METHODS
from swaggerit.utils import set_logger
from collections import namedtuple, defaultdict
from jsonschema import Draft4Validator, ValidationError
from abc import ABCMeta, abstractmethod
from copy import deepcopy
import ujson
import re
import asyncio


class SwaggerAPI(metaclass=ABCMeta):

    def __init__(self, models, sqlalchemy_bind=None, redis_bind=None,
                   elsearch_bind=None, swagger_json_template=None, title=None,
                   version='1.0.0', authorizer=None, get_swagger_req_auth=True,
                   swagger_doc_url='doc', redis_bind_sync=None):
        self._validate_metadata(swagger_json_template, title, version)

        set_logger(self)
        self.authorizer = authorizer
        self._sqlalchemy_bind = sqlalchemy_bind
        self._redis_bind = redis_bind
        self._elsearch_bind = elsearch_bind
        self._get_swagger_req_auth = get_swagger_req_auth
        self._redis_bind_sync = redis_bind_sync
        self._set_swagger_json_template(swagger_json_template, title, version)
        self._validate_swagger_json(models)
        self._set_models(models)
        self._set_swagger_doc(swagger_doc_url)

    def _validate_swagger_json(self, models):
        swagger_json = deepcopy(self._swagger_json_template)
        final_definitions = swagger_json.get('definitions', {})
        final_paths = dict()

        for model in models:
            model_swagger_schema = model.__swagger_json__
            model_definitions = model_swagger_schema.get('definitions', {})
            model_paths = model_swagger_schema['paths']
            self._raise_duplicated_key_error('paths', final_paths, model_paths)
            self._raise_duplicated_key_error('definitions', final_definitions, model_definitions)
            final_paths.update(model_paths)
            final_definitions.update(model_definitions)

        swagger_json['paths'] = final_paths
        if final_definitions:
            swagger_json['definitions'] = final_definitions

        Draft4Validator(SWAGGER_SCHEMA).validate(swagger_json)

    def _validate_metadata(self, swagger_json_template, title, version):
        if bool(title is None) == bool(swagger_json_template is None):
            raise SwaggerItAPIError("One of 'title' or 'swagger_json_template' "
                                  "arguments must be setted.")

        if version != '1.0.0' and swagger_json_template is not None:
            raise SwaggerItAPIError("'version' argument can't be setted when "
                                  "'swagger_json_template' was setted.")

    def _set_swagger_json_template(self, swagger_json_template, title, version):
        if swagger_json_template is None:
            swagger_json_template = deepcopy(SWAGGER_JSON_TEMPLATE)
            swagger_json_template['info']['title'] = title
            swagger_json_template['info']['version'] = version

        if swagger_json_template.get('paths'):
            raise SwaggerItAPIError("The Swagger Json 'paths' property will be populated "
                "by the 'models' contents. This property must be empty.")

        self._swagger_json_template = swagger_json_template

    def _raise_duplicated_key_error(self, name, set_, subset):
        subset = set(subset.keys())
        set_ = set(set_.keys())
        if set_.intersection(subset):
            raise SwaggerItAPIError(
                "The Swagger Json {} '{}' are duplicated!".format(name, ', '.join(subset))
            )

    def _set_models(self, models):
        self._models = set()
        for model in models:
            self.add_model(model)

    def add_model(self, model):
        if model.__api__ is not None:
            raise SwaggerItAPIError(
                "Model '{}' was already registered for '{}' API".format(
                    model.__name__, model.__api__.__class__.__name__
                ))

        self._models.add(model)
        self._set_model_routes(model)
        model.__api__ = self

    def _set_model_routes(self, model):
        for path, method, handler in self.get_model_methods(model):
            handler = self._set_handler_decorator(handler)
            self._set_route(path, method, handler)

    def get_model_methods(self, model):
        model_swagger_schema = model.__swagger_json__

        for path, path_schema in model_swagger_schema['paths'].items():
            all_methods_parameters = path_schema.get('parameters', [])
            path = self._format_path(path)

            for method in HTTP_METHODS:
                method_schema = path_schema.get(method)

                if method_schema is not None:
                    method_schema = deepcopy(method_schema)
                    definitions = model_swagger_schema.get('definitions')
                    parameters = method_schema.get('parameters', [])
                    parameters.extend(all_methods_parameters)

                    method_schema['parameters'] = parameters
                    operation = getattr(model, method_schema['operationId'].split('.')[-1])
                    handler = SwaggerMethod(operation, method_schema,
                                           definitions, model.__schema_dir__,
                                           authorizer=self.authorizer)
                    yield path, method, handler

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
                       elsearch_bind=self._elsearch_bind,
                       redis_bind_sync=self._redis_bind_sync,
                       loop=self.loop)

    def _destroy_session(self, session):
        if hasattr(session, 'close'):
            session.close()

    @abstractmethod
    def _set_swagger_doc(self, swagger_doc_url):
        pass

    async def _authorize(self, req, session):
        if self.authorizer and self._get_swagger_req_auth:
            response = await self.authorizer(req, session)
            if response is not None:
                return response

    @property
    def swagger_json(self):
        swagger_json = deepcopy(self._swagger_json_template)
        final_definitions = swagger_json.get('definitions', {})
        final_paths = dict()

        for model in self._models:
            model_swagger_schema = model.__swagger_json__
            model_definitions = model_swagger_schema.get('definitions', {})
            model_paths = model_swagger_schema['paths']
            final_paths.update(model_paths)
            final_definitions.update(model_definitions)

        swagger_json['paths'] = final_paths
        if final_definitions:
            swagger_json['definitions'] = final_definitions

        return swagger_json
