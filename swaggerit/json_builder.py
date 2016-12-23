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


from swaggerit.exceptions import SwaggerItJsonError
from copy import deepcopy
import ujson


class JsonBuilderMeta(type):

    def _type_builder(cls, type_):
        return getattr(cls, '_build_' + type_)

    def _build_string(cls, value):
        return str(value)

    def _build_number(cls, value):
        return float(value)

    def _build_boolean(cls, value):
        value = ujson.loads(value)
        if not isinstance(value, bool):
            raise ValueError(value)
        return value

    def _build_integer(cls, value):
        return int(value)

    def _build_array(cls, values, schema, nested_types, input_):
        if 'array' in nested_types:
            raise SwaggerItJsonError('nested array was not allowed', instance=input_)

        if isinstance(values, list):
            new_values = []
            [new_values.extend(value.split(',')) for value in values]
            values = new_values
        else:
            values = values.split(',')

        items_schema = schema.get('items')
        if items_schema:
            nested_types.add('array')

            if isinstance(items_schema, dict):
                values = [cls._build_value(
                    value, items_schema, nested_types, input_) for value in values]

            elif isinstance(items_schema, list):
                if len(items_schema) != len(values):
                    raise SwaggerItJsonError(
                        "size mismatch for items array '{}'".format(', '.join(values)),
                        instance=input_, schema=items_schema)
                values = [cls._build_value(value, schema, nested_types, input_) \
                            for value, schema in zip(values, items_schema)]

        return values

    def _build_value(cls, value, schema, nested_types, input_):
        type_ = schema['type']
        exception = SwaggerItJsonError("invalid value '{}' for type '{}'".format(value, type_),
                                    instance=input_, schema=schema)
        if type_ == 'array' or type_ == 'object':
            try:
                return cls._type_builder(type_)(value, schema, nested_types, input_)
            except ValueError:
                raise exception

        try:
            return cls._type_builder(type_)(value)
        except ValueError:
            raise exception

    def _build_object(cls, value, schema, nested_types, input_):
        if 'object' in nested_types:
            raise SwaggerItJsonError('nested object was not allowed', instance=input_)

        properties = value.split('|')
        dict_obj = dict()
        nested_types.add('object')
        for prop in properties:
            key, value = prop.split(':')
            prop_schema = schema['properties'].get(key)
            if prop_schema is None:
                raise SwaggerItJsonError("Invalid property '{}'".format(key),
                    instance=input_, schema=schema)

            dict_obj[key] = \
                cls._build_value(value, prop_schema, nested_types, input_)

        nested_types.discard('object')
        return dict_obj


class JsonBuilder(metaclass=JsonBuilderMeta):

    @classmethod
    def build(cls, json_value, schema):
        nested_types = set()
        input_ = deepcopy(json_value)
        return cls._build_value(json_value, schema, nested_types, input_)
