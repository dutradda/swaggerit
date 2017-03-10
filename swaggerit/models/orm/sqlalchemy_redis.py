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


from swaggerit.models.orm._redis_base import _ModelRedisBaseMeta
from swaggerit.exceptions import SwaggerItModelError
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.ext.declarative.clsregistry import _class_resolver
from sqlalchemy.orm.properties import RelationshipProperty, ColumnProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy import or_, and_
from collections import OrderedDict
from copy import deepcopy
import ujson
import asyncio


class _ModelSQLAlchemyRedisBaseInitMetaMixin(DeclarativeMeta, _ModelRedisBaseMeta):

    def __init__(cls, name, bases_classes, attributes):
        DeclarativeMeta.__init__(cls, name, bases_classes, attributes)

        if hasattr(cls, '__model_base__'):
            cls._set_primaries_keys()
            cls.__id_names__ = getattr(cls, '__id_names__', sorted(cls.__primaries_keys__.keys()))
            cls.__key__ = str(cls.__table__.name)

            _ModelRedisBaseMeta.__init__(cls, name, bases_classes, attributes)
            cls._validate_base_class(bases_classes)

            cls.__backrefs__ = set()
            cls.__relationships__ = dict()
            cls.__columns__ = set(cls.__table__.c)
            cls.__use_redis__ = getattr(cls, '__use_redis__', True)
            cls.__todict_schema__ = {}
            all_models = [m for m in cls.__all_models__.values()
                          if issubclass(m, cls.__model_base__)]
            cls._set_backrefs_for_all_models(all_models)

        else:
            _ModelRedisBaseMeta.__init__(cls, name, bases_classes, attributes)
            cls.__model_base__ = cls

    def _set_primaries_keys(cls):
        primaries_keys = {}

        for attr_name in cls.__dict__:
            primary_key = cls._get_primary_key(attr_name)
            if primary_key:
                primaries_keys[attr_name] = primary_key

        cls.__primaries_keys__ = OrderedDict(sorted(primaries_keys.items()))

    def _get_primary_key(cls, attr_name):
        attr = getattr(cls, attr_name)
        if isinstance(attr, InstrumentedAttribute) \
                and isinstance(attr.prop, ColumnProperty) \
                and [col for col in attr.prop.columns if col.primary_key]:
            return attr

    def _validate_base_class(cls, bases_classes):
        for base in bases_classes:
            if base.__name__ == cls.__model_base__.__name__:
                return base
        else:
            raise SwaggerItModelError("'{}' class must inherit from '{}'".format(
                                 name, cls.__model_base__.__name__))

    def _set_backrefs_for_all_models(cls, all_models):
        all_relationships = set()

        for model in all_models:
            model._set_relationships()
            all_relationships.update(model.__relationships__.values())

        for model in all_models:
            for relationship in all_relationships:
                if model != cls.get_model_from_rel(relationship, all_models, parent=True) and \
                        model == cls.get_model_from_rel(relationship, all_models):
                    model.__backrefs__.add(relationship)

    def _set_relationships(cls):
        if cls.__relationships__:
            return

        for attr_name in cls.__dict__:
            relationship = cls._get_relationship(attr_name)
            if relationship:
                cls.__relationships__[attr_name] = relationship

    def _get_relationship(cls, attr_name):
        attr = getattr(cls, attr_name)
        if isinstance(attr, InstrumentedAttribute):
            if isinstance(attr.prop, RelationshipProperty):
                return attr


class _ModelSQLAlchemyRedisBaseInsertMetaMixin(type):

    async def insert(cls, session, objs, commit=True, todict=True, **kwargs):
        input_ = deepcopy(objs)
        objs = cls._to_list(objs)
        new_insts = set()

        for obj in objs:
            instance = await cls.new(session, input_, **obj)
            new_insts.add(instance)

        session.add_all(new_insts)

        if commit:
            await session.commit()

        return cls._build_todict_list(new_insts) if todict else list(new_insts)


class _ModelSQLAlchemyRedisBaseUpdateMetaMixin(type):

    async def update(cls, session, objs, commit=True, todict=True, ids=None, **kwargs):
        input_ = deepcopy(objs)
        objs = cls._to_list(objs)
        ids = [cls.get_ids_from_values(
            obj) for obj in objs] if not ids else cls._to_list(ids)

        insts = await cls.get(session, ids, todict=False)

        for inst in insts:
            inst.old_redis_key = cls.get_instance_key(inst)

        id_insts_zip = [(cls.get_instance_ids_map(inst, ids[0].keys()), inst) for inst in insts]

        for id_, inst in id_insts_zip:
            await inst.init(session, input_, **objs[ids.index(id_)])

        if commit:
            await session.commit()

        return cls._build_todict_list(insts) if todict else insts


class _ModelSQLAlchemyRedisBaseDeleteMetaMixin(type):

    async def delete(cls, session, ids, commit=True, **kwargs):
        ids = cls._to_list(ids)
        filters = cls.build_filters_by_ids(ids)
        instances = cls._build_query(session).filter(filters).all()
        [session.delete(inst) for inst in instances]

        if commit:
            await session.commit()


class _ModelSQLAlchemyRedisBaseGetMetaMixin(type):

    async def get(cls, session, ids=None, limit=None, offset=None, todict=True, **kwargs):
        if ids is None:
            query = cls._build_query(session, kwargs)

            if limit is not None:
                query = query.limit(limit)

            if offset is not None:
                query = query.offset(offset)

            return cls._build_todict_list(query.all()) if todict else query.all()

        if limit is not None and offset is not None:
            limit += offset

        ids = cls._to_list(ids)
        return await cls._get_many(session, ids[offset:limit], todict, kwargs)

    def _build_query(cls, session, kwargs=None):
        query = session.query(cls)

        if kwargs:
            for prop_name, value in kwargs.items():
                if isinstance(value, dict):
                    query, filters = \
                        cls._get_query_and_filters_by_relationship(prop_name, value, kwargs, query)

                elif isinstance(value, list):
                    if value and isinstance(value[0], dict):
                        query, filters = cls._get_query_and_filters_by_relationship(
                            prop_name, value, kwargs, query)
                    else:
                        filters = cls.build_filters_by_ids([{prop_name: v} for v in value])

                else:
                    filters = cls.build_filters_by_ids([{prop_name: value}])

                query = query.filter(filters)

        return query

    def _get_query_and_filters_by_relationship(cls, prop_name, value, kwargs, query):
        relationship = cls.__relationships__.get(prop_name)
        if not relationship:
            raise SwaggerItModelError("invalid model '{}'".format(prop_name), kwargs)

        secondary = relationship.prop.secondary
        model  = cls.get_model_from_rel(relationship)
        join = secondary if secondary is not None else model

        ids = cls._to_list(value)
        filters = model.build_filters_by_ids(ids)
        query = query.join(join)

        return query, filters

    async def _get_many(cls, session, ids, todict, kwargs):
        if not todict or session.redis_bind is None:
            filters = cls.build_filters_by_ids(ids)
            insts = cls._build_query(session, kwargs).filter(filters).all()

            if todict:
                return [inst.todict() for inst in insts]
            else:
                return insts

        model_redis_key = type(cls).get_key(cls, '_'.join(kwargs.keys()))
        ids_redis_keys = [cls.get_instance_key(id_, id_.keys()) for id_ in ids]
        objs = await session.redis_bind.hmget(model_redis_key, *ids_redis_keys)
        ids_not_cached = [id_ for i, (id_, obj) in enumerate(zip(ids, objs)) if obj is None]
        objs = [ujson.loads(obj) for obj in objs if obj is not None]

        if ids_not_cached:
            await session.redis_bind.sadd(cls.get_filters_names_key(), model_redis_key)
            filters = cls.build_filters_by_ids(ids_not_cached)
            instances = cls._build_query(session).filter(filters).all()
            if instances:
                items_to_set = {
                    cls.get_instance_key(inst): ujson.dumps(inst.todict()) for inst in instances}
                await session.redis_bind.hmset_dict(model_redis_key, items_to_set)

                for inst in instances:
                    inst_ids = cls.get_instance_ids_map(inst, ids[0].keys())
                    index = ids_not_cached.index(inst_ids)
                    objs.insert(index, inst.todict())

        return objs

    def get_filters_names_key(cls):
        return cls.get_key('_filters_names')


class ModelSQLAlchemyRedisBaseMeta(
        _ModelSQLAlchemyRedisBaseInitMetaMixin,
        _ModelSQLAlchemyRedisBaseInsertMetaMixin,
        _ModelSQLAlchemyRedisBaseUpdateMetaMixin,
        _ModelSQLAlchemyRedisBaseDeleteMetaMixin,
        _ModelSQLAlchemyRedisBaseGetMetaMixin):

    def get_model_from_rel(cls, relationship, all_models=None, parent=False):
        if parent:
            return relationship.prop.parent.class_

        if isinstance(relationship.prop.argument, _class_resolver):
            if all_models is None:
                return relationship.prop.argument()

            for model in all_models:
                if model.__name__ == relationship.prop.argument.arg:
                    return model

            return

        return relationship.prop.argument

    def _build_todict_list(cls, insts):
        return [inst.todict() for inst in insts]

    def get_ids_from_values(cls, values):
        cast = lambda id_name, value: getattr(cls, id_name).type.python_type(value) \
            if value is not None else None
        return {id_name: cast(id_name, values.get(id_name)) for id_name in cls.__id_names__}

    def build_filters_by_ids(cls, ids):
        if len(ids) == 1:
            return cls._get_obj_i_comparison(ids[0])

        or_clause_args = []
        for i in range(0, len(ids)):
            comparison = cls._get_obj_i_comparison(ids[i])
            or_clause_args.append(comparison)

        return or_(*or_clause_args)

    def _get_obj_i_comparison(cls, attributes):
        if len(attributes) == 1:
            attr_name = [i for i in attributes.keys()][0]
            return cls._build_attribute_comparison(attr_name, attributes)

        and_clause_args = []
        for attr_name in attributes:
            comparison = cls._build_attribute_comparison(
                attr_name, attributes)
            and_clause_args.append(comparison)

        return and_(*and_clause_args)

    def _build_attribute_comparison(cls, attr_name, attributes):
        return getattr(cls, attr_name) == attributes[attr_name]


class ModelSQLAlchemyRedisBaseSuper(object):

    @classmethod
    async def new(cls, session, input_=None, **kwargs):
        inst = cls()
        await inst.init(session, input_=input_, **kwargs)
        return inst

    async def init(self, session, input_=None, **kwargs):
        if input_ is None:
            input_ = deepcopy(kwargs)

        for key, value in kwargs.items():
            await self._setattr(key, value, session, input_)

        self._validate()

    async def _setattr(self, attr_name, value, session, input_):
        cls = type(self)
        if not hasattr(cls, attr_name):
            raise TypeError("{} is an invalid keyword argument for {}".format(attr_name, cls.__name__))

        relationship = cls._get_relationship(attr_name)

        if relationship is not None:
            await self._set_relationship(relationship, attr_name, value, session, input_)

        else:
            setattr(self, attr_name, value)

    async def _set_relationship(self, relationship, attr_name, values_list, session, input_):
        cls = type(self)        
        rel_model = cls.get_model_from_rel(relationship)

        if relationship.prop.uselist is not True:
            if isinstance(values_list, list):
                raise SwaggerItModelError("Relationship '{}' don't use lists.".format(attr_name), input_)
            values_list = [values_list]

        rel_insts = await self._get_instances_from_values(session, rel_model, values_list)

        for rel_values, rel_inst in zip(values_list, rel_insts):
            await self._do_nested_operation(rel_values, rel_inst,
                                            attr_name, relationship, session, input_)

    async def _get_instances_from_values(self, session, rel_model, rels_values):
        ids_to_get = self._get_ids_from_rels_values(rel_model, rels_values)
        if not ids_to_get:
            return []

        # attribution made just to keep the reference on session identity_map
        instances = await rel_model.get(session, ids_to_get, todict=False)

        rels_ints = []
        for rel_ids in ids_to_get:
            rel_inst = await rel_model.get(session, rel_ids, todict=False)
            rel_inst = rel_inst[0] if rel_inst else None
            rels_ints.append(rel_inst)

        return rels_ints

    def _get_ids_from_rels_values(self, rel_model, rels_values):
        ids = []
        for rel_value in rels_values:
            ids_values = rel_model.get_ids_from_values(rel_value)
            ids.append(ids_values)

        return ids

    async def _do_nested_operation(self, rel_values, rel_inst,
                    attr_name, relationship, session, input_):
        operation = rel_values.pop('_operation', 'get')

        if rel_inst is None and operation != 'insert':
            raise SwaggerItModelError(
                "Can't execute nested '{}' operation".format(operation), input_)

        if operation == 'get':
            self._do_get(attr_name, relationship, rel_inst)

        elif operation == 'update':
            self._do_get(attr_name, relationship, rel_inst)
            await rel_inst.init(session, input_, **rel_values)

        elif operation == 'delete':
            rel_model = type(rel_inst)
            await rel_model.delete(session, rel_inst.get_ids_map(), commit=False)

        elif operation == 'remove':
            self._do_remove(attr_name, relationship, rel_inst, input_)

        elif operation == 'insert':
            await self._do_insert(session, attr_name, relationship, rel_values)

    def _do_get(self, attr_name, relationship, rel_inst):
        if relationship.prop.uselist is True:
            if rel_inst not in getattr(self, attr_name):
                getattr(self, attr_name).append(rel_inst)

        else:
            setattr(self, attr_name, rel_inst)

    def get_ids_map(self, keys=None):
        if keys is None:
            keys = type(self).__primaries_keys__.keys()

        pk_names = sorted(keys)
        return {id_name: getattr(self, id_name) for id_name in pk_names}

    def _do_remove(self, attr_name, relationship, rel_inst, input_):
        rel_model = type(rel_inst)
        if relationship.prop.uselist is True:
            if rel_inst in getattr(self, attr_name):
                getattr(self, attr_name).remove(rel_inst)
            else:
                columns_str = ', '.join(rel_model.__primaries_keys__)
                ids_str = ', '.join([str(id_) for id_ in type(rel_inst).get_instance_ids_values(rel_inst)])
                error_message = "can't remove model '{}' on column(s) '{}' with value(s) {}"
                error_message = error_message.format(rel_model.__key__, columns_str, ids_str)
                raise SwaggerItModelError(error_message, input_)
        else:
            setattr(self, attr_name, None)

    async def _do_insert(self, session, attr_name, relationship, rel_values):
        rel_model = type(self).get_model_from_rel(relationship)
        rel_inst = await rel_model.new(session, **rel_values)

        if relationship.prop.uselist is not True:
            setattr(self, attr_name, rel_inst)
        else:
            if rel_inst not in getattr(self, attr_name):
                getattr(self, attr_name).append(rel_inst)

    def _validate(self):
        pass

    def get_related(self, session):
        related = set()
        cls = type(self)
        for relationship in cls.__backrefs__:
            related_model_insts = self._get_related_model_insts(
                session, relationship, parent=True)
            related.update(related_model_insts)

        return related

    def _get_related_model_insts(self, session, relationship, parent=False):
        cls = type(self)
        rel_model = cls.get_model_from_rel(relationship, parent=parent)

        filters = cls.build_filters_by_ids([self.get_ids_map()])
        result = set(rel_model._build_query(session).join(
            relationship).filter(filters).all())
        return result

    def todict(self, schema=None):
        if schema is None:
            schema = type(self).__todict_schema__

        dict_inst = self._todict(schema)
        self._format_output_json(dict_inst, schema)
        return dict_inst

    def _todict(self, schema=None):
        dict_inst = dict()
        self._todict_columns(dict_inst, schema)
        self._todict_relationships(dict_inst, schema)

        return dict_inst

    def _format_output_json(self, dict_inst, schema):
        pass

    def _todict_columns(self, dict_inst, schema):
        for col in type(self).__columns__:
            col_name = str(col.name)
            if self._attribute_in_schema(col_name, schema):
                dict_inst[col_name] = getattr(self, col_name)

    def _attribute_in_schema(self, attr_name, schema):
        return (attr_name in schema and schema[attr_name]) or (not attr_name in schema)

    def _todict_relationships(self, dict_inst, schema):
        for rel_name, rel in type(self).__relationships__.items():
            if self._attribute_in_schema(rel_name, schema):
                rel_schema = schema.get(rel_name)
                rel_schema = rel_schema if isinstance(
                    rel_schema, dict) else None
                attr = getattr(self, rel_name)
                relationships = None
                if rel.prop.uselist is True:
                    relationships = [rel.todict(rel_schema) for rel in attr]
                elif attr is not None:
                    relationships = attr.todict(rel_schema)

                dict_inst[rel_name] = relationships
