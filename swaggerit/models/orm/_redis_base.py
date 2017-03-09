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


from swaggerit.models.orm._swaggerit_meta import _ModelSwaggerItOrmMeta
from swaggerit.models._base import _ModelBaseMeta
from swaggerit.exceptions import SwaggerItModelError


class _ModelRedisBaseMeta(_ModelSwaggerItOrmMeta):

    def __init__(cls, name, bases_classes, attributes):
        if hasattr(cls, '__model_base__') and not getattr(cls, '__id_names__', None):
                raise SwaggerItModelError("Class attribute '__id_names__' must be setted "
                                          "and must contains at least one name.")

        _ModelSwaggerItOrmMeta.__init__(cls, name, bases_classes, attributes)
        cls.__key_separator__ = getattr(cls, '__key_separator__', b'|')

    def _to_list(cls, objs):
        return objs if isinstance(objs, list) else [objs]

    def get_instance_key(cls, instance, id_names=None):
        ids_ = [str(v) for v in cls.get_instance_ids_values(instance, id_names)]
        return cls.__key_separator__.decode().join(ids_).encode()

    def get_instance_ids_values(cls, instance, keys=None):
        if keys is None:
            keys = cls.__id_names__

        if isinstance(instance, dict):
            return tuple([instance[key] for key in sorted(keys)])
        else:
            return tuple([getattr(instance, key) for key in sorted(keys)])

    def set_instance_ids(cls, instance, key, keys=None):
        if keys is None:
            keys = sorted(cls.__id_names__)

        values = key.split(cls.__key_separator__)
        for key, value in zip(keys, values):
            instance[key] = value.decode()

    def get_instance_ids_map(cls, instance, keys=None):
        if keys is None:
            keys = cls.__id_names__

        if isinstance(instance, dict):
            return {key: instance[key] for key in keys}
        else:
            return {key: getattr(instance, key) for key in keys}

    def _unpack_objs(cls, objs):
        if isinstance(objs, dict):
            objs = objs.values()
        return [cls._unpack_obj(obj) for obj in objs if obj is not None]
