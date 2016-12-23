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
from swaggerit.utils import get_module_path
from swaggerit.response import SwaggerResponse
from types import MethodType
import re


def _init(obj):
    SWAGGER_VALIDATOR.validate(obj.__schema__)
    _validate_operation(obj)
    obj.__api__ = getattr(obj, '__api__', None)
    obj.__schema_dir__ = getattr(obj, '__schema_dir__', get_module_path(obj))
    _set_default_options(obj)
    obj._build_response = MethodType(_build_response, obj)


def _validate_operation(obj):
    for path in obj.__schema__:
        if path != 'definitions':
            for key, method_schema in obj.__schema__[path].items():
                if key != 'parameters' and key != 'definitions':
                    operation_id = method_schema['operationId']
                    if not hasattr(obj, operation_id):
                        raise SwaggerItModelError(
                            "'operationId' '{}' was not found".format(operation_id))


def _set_default_options(obj):
    for path, schema in obj.__schema__.items():
        if not 'options' in schema and path != 'definitions':
            valid_methods = [k.upper() for k in schema.keys()]
            headers = {'Allow': ', '.join(valid_methods)}
            path_norm = path.strip('/').replace('/', '_')
            path_norm = re.sub(r'(\{|<)([a-zA-Z_0-9-]+)(\}|>)', r'\2', path_norm)
            options_operation_name = '{}_{}'.format('options', path_norm) \
                if path_norm else 'options'

            options_method = MethodType(_options_operation, obj)
            setattr(obj, options_operation_name, options_method)
            schema['options'] = _build_options_schema(options_operation_name)


def _build_response(obj, status_code, body=None, headers={}):
    return SwaggerResponse(status_code, {}, body)


async def _options_operation(obj, req, sess):
    return SwaggerResponse(200, headers, None, None)


def _build_options_schema(options_operation_name):
    return {
        'operationId': options_operation_name,
        'responses': {
            '204': {
                'description': 'No Content',
                'headers': {'Allow': {'type': 'string'}}
            }
        }
    }


class _ModelSwaggerItMeta(_ModelBaseMeta):

    def __init__(cls, name, bases_classes, attributes):
        _ModelBaseMeta.__init__(cls, name, bases_classes, attributes)
        _init(cls)
