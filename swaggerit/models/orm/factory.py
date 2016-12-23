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


from swaggerit.models.orm.redis import ModelRedisMeta
from swaggerit.models.orm.sqlalchemy_redis import (
    ModelSQLAlchemyRedisBaseMeta, ModelSQLAlchemyRedisBaseSuper)
from sqlalchemy.ext.declarative import declarative_base
from types import MethodType


class FactoryOrmModels(object):

    @classmethod
    def make_redis(cls, class_name, id_names, key=None, base=object,
                   schema=None, key_separator=None, metaclass=ModelRedisMeta):

        attributes = {'__id_names__': sorted(tuple(id_names))}

        if key is not None:
            attributes['__key__'] = key

        if schema is not None:
            attributes['__schema__'] = schema

        if key_separator is not None:
            attributes['__key_separator__'] = key_separator

        class_ = metaclass(class_name, (base,), attributes)
        class_.update = MethodType(metaclass.update, class_)
        class_.get = MethodType(metaclass.get, class_)
        return class_

    @staticmethod
    def make_sqlalchemy_redis_base(
            name='ModelSQLAlchemyRedisBase',
            bind=None, metadata=None,
            mapper=None, key_separator=None,
            metaclass=ModelSQLAlchemyRedisBaseMeta,
            cls=ModelSQLAlchemyRedisBaseSuper,
            constructor=ModelSQLAlchemyRedisBaseSuper.__init__):
        base = declarative_base(
            name=name, metaclass=metaclass,
            cls=cls, bind=bind, metadata=metadata,
            mapper=mapper, constructor=constructor)

        if key_separator is not None:
           base.__key_separator__ = key_separator

        return base
