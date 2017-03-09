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


from swaggerit.models._base import _ModelBaseMeta, _ModelBase
from swaggerit.constants import SWAGGER_VALIDATOR
from swaggerit.exceptions import SwaggerItModelError
from swaggerit.utils import get_module_path, set_method
from swaggerit.response import SwaggerResponse
import re
import ujson


class _ModelSwaggerItMeta(_ModelBaseMeta):

    def __init__(cls, name, bases_classes, attributes):
        _ModelBaseMeta.__init__(cls, name, bases_classes, attributes)
        _init(cls)


def _init(obj):
    set_method(obj, _build_response)

    if hasattr(obj, '__model_base__') and hasattr(obj, '__swagger_json__'):
        if not 'paths' in obj.__swagger_json__:
            raise SwaggerItModelError("The 'paths' property of swagger json is mandatory.")

        SWAGGER_VALIDATOR.validate(obj.__swagger_json__['paths'])
        _validate_operation(obj)

        if isinstance(obj, type):
            model_name = obj.__name__
        else:
            model_name = type(obj).__name__

        _format_definitions_names(obj, model_name)
        _format_operations_names(obj, model_name)

        obj.__api__ = getattr(obj, '__api__', None)
        obj.__schema_dir__ = getattr(obj, '__schema_dir__', get_module_path(obj))
        _set_default_options(obj, model_name)

def _format_definitions_names(obj, model_name):
    definitions = obj.__swagger_json__.get('definitions', {})
    definitions_keys = list(definitions.keys())
    for def_name in definitions_keys:
        definitions['{}.{}'.format(model_name, def_name)] = definitions.pop(def_name)

    schema = ujson.dumps(obj.__swagger_json__, escape_forward_slashes=False)
    schema = re.sub(r'("\$ref":"#/definitions/)([^/"]+)', r'\1{}.\2'.format(model_name), schema)
    obj.__swagger_json__ = ujson.loads(schema)

def _format_operations_names(obj, model_name):
    for path_name, path in obj.__swagger_json__['paths'].items():
        for method_name, method in path.items():
            if method_name != 'parameters':
                op_id = method['operationId']
                method['operationId'] = '{}.{}'.format(model_name, op_id)

def _validate_operation(obj):
    for path, schema in obj.__swagger_json__['paths'].items():
        for key, method_schema in schema.items():
            if key != 'parameters' and key != 'definitions':
                operation_id = method_schema['operationId']
                if not hasattr(obj, operation_id):
                    raise SwaggerItModelError(
                        "'operationId' '{}' was not found".format(operation_id))

def _set_default_options(obj, model_name):
    for path, schema in obj.__swagger_json__['paths'].items():
        if not 'options' in schema:
            path_norm = path.strip('/').replace('/', '_')
            path_norm = re.sub(r'(\{|<)([a-zA-Z_0-9-]+)(\}|>)', r'\2', path_norm)
            options_operation_name = '{}_{}'.format('options', path_norm) \
                if path_norm else 'options'

            valid_methods = [k.upper() for k in schema.keys()]
            headers = {'Allow': ', '.join(valid_methods)}
            set_method(obj, _options_operation_decor(headers), options_operation_name)
            schema['options'] = _build_options_schema(options_operation_name, model_name)

def _build_response(obj, status_code, headers=None, body=None):
    return SwaggerResponse(status_code, headers, body)

def _options_operation_decor(headers):
    async def _options_operation(obj, req, sess):
        return obj._build_response(200, headers)

    return _options_operation

def _build_options_schema(options_operation_name, model_name):
    return {
        'operationId': '{}.{}'.format(model_name, options_operation_name),
        'responses': {
            '204': {
                'description': 'No Content',
                'headers': {'Allow': {'type': 'string'}}
            }
        }
    }
