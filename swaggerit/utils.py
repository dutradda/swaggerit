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


from jsonschema import Draft4Validator, RefResolver
from types import MethodType
import os.path
import logging
import ujson
import sys


def build_validator(schema, path):
    handlers = {'': _URISchemaHandler(path)}
    resolver = RefResolver.from_schema(schema, handlers=handlers)
    return Draft4Validator(schema, resolver=resolver)


class _URISchemaHandler(object):

    def __init__(self, schemas_path):
        self._schemas_path = schemas_path

    def __call__(self, uri):
        schema_filename = os.path.join(self._schemas_path, uri.lstrip('/'))
        with open(schema_filename) as json_schema_file:
            return ujson.load(json_schema_file)


def get_dir_path(filename):
    return os.path.dirname(os.path.abspath(filename))


def get_swagger_json(current_filename, swagger_json_name=None):
    if swagger_json_name is None:
        swagger_json_name = 'swagger.json'

    return ujson.load(open(os.path.join(get_dir_path(current_filename), swagger_json_name)))


def get_module_path(cls):
    module_filename = sys.modules[cls.__module__].__file__
    return get_dir_path(module_filename)


def set_logger(obj, name_sufix=None):
    if isinstance(obj, type):
        module_name = obj.__module__
        name = obj.__name__
    else:
        module_name = type(obj).__module__
        name = type(obj).__name__

    name = '.'.join([part for part in (module_name, name, name_sufix) if part is not None])
    obj._logger = logging.getLogger(name)


from swaggerit.models._base import _all_models


def get_model(key):
    return _all_models[key]


def set_method(obj, method, method_name=None):
    if method_name is None:
        method_name = method.__name__

    if not hasattr(obj, method_name):
        setattr(obj, method_name, MethodType(method, obj))
