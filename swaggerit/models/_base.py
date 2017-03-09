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


_all_models = dict()


from swaggerit.exceptions import SwaggerItModelError
from swaggerit.utils import set_logger
from types import MethodType
import ujson
import re


class _ModelBaseMeta(type):
    __all_models__ = _all_models

    def __init__(cls, name, bases_classes, attributes):
        _init(cls, name)

    def get_key(cls, sufix=None):
        if not sufix or sufix == cls.__key__:
            return cls.__key__

        return '{}_{}'.format(cls.__key__, sufix)


def _init(obj, name):
    if hasattr(obj, '__model_base__'):
        name = name.replace('Model', '')
        key = obj.__key__ = getattr(obj, '__key__', _camel_case_convert(name))

        if key in _all_models:
            raise SwaggerItModelError("The model '{}' was already registered with name '{}'."
                .format(_all_models[key].__name__, key))

        _all_models[key] = obj

    set_logger(obj)
    obj.get_model = MethodType(_get_model, obj)
    obj._unpack_obj = MethodType(_unpack_obj, obj)
    obj._pack_obj = MethodType(_pack_obj, obj)

def _camel_case_convert(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def _get_model(obj, name):
    return _all_models.get(name)

def _unpack_obj(inst, obj):
    return ujson.loads(obj)

def _pack_obj(inst, obj):
    return ujson.dumps(obj, escape_forward_slashes=False)


class _ModelBase(object):
    __all_models__ = _all_models

    def __init__(self, key_sufix=None):
        name = type(self).__name__
        if key_sufix is not None:
            name += '_{}'.format(key_sufix)

        _init(self, name)
