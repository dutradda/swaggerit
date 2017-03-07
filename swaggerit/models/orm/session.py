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


from sqlalchemy.orm import sessionmaker, Session as SessionSA
from sqlalchemy.orm.query import Query
from sqlalchemy import event
from collections import defaultdict
import ujson
import asyncio


class _SessionBase(SessionSA):

    def __init__(
            self, bind=None, autoflush=True,
            expire_on_commit=True, _enable_transaction_accounting=True,
            autocommit=False, twophase=False, weak_identity_map=True,
            binds=None, extension=None, info=None, query_cls=Query,
            redis_bind=None, elsearch_bind=None, loop=None, redis_bind_sync=None):
        self.redis_bind = redis_bind
        self.elsearch_bind = elsearch_bind
        self.user = None
        self.loop = loop
        self.redis_bind_sync = redis_bind_sync
        self._clean_redis_sets()
        SessionSA.__init__(
            self, bind=bind, autoflush=autoflush, expire_on_commit=expire_on_commit,
            _enable_transaction_accounting=_enable_transaction_accounting,
            autocommit=autocommit, twophase=twophase, weak_identity_map=weak_identity_map,
            binds=binds, extension=extension, info=info, query_cls=query_cls)

    def _clean_redis_sets(self):
        self._insts_to_hdel = set()
        self._insts_to_hmset = set()

    async def commit(self):
        try:
            SessionSA.commit(self)
            if self.redis_bind is not None:
                await self._exec_hdel(self._insts_to_hdel)
                await self._update_objects_on_redis()
        finally:
            self._clean_redis_sets()

    def delete(self, instance):
        self._insts_to_hmset.update(instance.get_related(self))
        return SessionSA.delete(self, instance)

    async def _update_objects_on_redis(self):
        insts_to_hmset = set.union(self._insts_to_hdel, self._insts_to_hmset)
        insts_to_hmset_count = 0

        while len(insts_to_hmset) != insts_to_hmset_count:
            insts_to_hmset_count = len(insts_to_hmset)
            insts_to_hmset_copy = insts_to_hmset.copy()
            [insts_to_hmset.update(inst.get_related(self)) for inst in insts_to_hmset_copy]

        insts_to_hmset.difference_update(self._insts_to_hdel)
        await self._exec_hmset_dict(insts_to_hmset)

    async def _exec_hdel(self, insts):
        models_keys_insts_keys_map = defaultdict(set)

        for inst in insts:
            model = type(inst)
            if not model.__use_redis__:
                continue

            filters_names_set = await self._get_filters_names_set(inst)
            for filters_names in filters_names_set:
                model_redis_key = model.get_key(filters_names.decode())
                inst_redis_key = model.get_instance_key(inst)
                models_keys_insts_keys_map[model_redis_key].add(inst_redis_key)

        for model_key, insts_keys in models_keys_insts_keys_map.items():
            await self.redis_bind.hdel(model_key, *insts_keys)

    async def _get_filters_names_set(self, inst):
        filters_names_key = type(inst).get_filters_names_key()
        filters_names = set(await self.redis_bind.smembers(filters_names_key))
        filters_names.add(type(inst).__key__.encode())
        return filters_names

    async def _exec_hmset_dict(self, insts):
        models_keys_insts_keys_insts_map = defaultdict(dict)
        models_keys_insts_keys_map = defaultdict(set)

        for inst in insts:
            model = type(inst)
            if not model.__use_redis__:
                continue

            filters_names_set = await self._get_filters_names_set(inst)
            for filters_names in filters_names_set:
                model_redis_key = model.get_key(filters_names.decode())
                inst_redis_key = model.get_instance_key(inst)

                inst_old_redis_key = getattr(inst, 'old_redis_key', None)
                if inst_old_redis_key is not None and inst_old_redis_key != inst_redis_key:
                    models_keys_insts_keys_map[model_redis_key].add(inst_old_redis_key)

                models_keys_insts_keys_insts_map[model_redis_key][inst_redis_key] = ujson.dumps(inst.todict())

        for model_key, insts_keys_insts_map in models_keys_insts_keys_insts_map.items():
            await self.redis_bind.hmset_dict(model_key, insts_keys_insts_map)

        for model_key, insts_keys in models_keys_insts_keys_map.items():
            await self.redis_bind.hdel(model_key, *insts_keys)

    def mark_for_hdel(self, inst):
        self._insts_to_hdel.add(inst)

    def mark_for_hmset_dict(self, inst):
        self._insts_to_hmset.add(inst)


Session = sessionmaker(class_=_SessionBase)


@event.listens_for(Session, 'persistent_to_deleted')
def deleted_from_database(session, instance):
    if session.redis_bind is not None and instance is not None:
        session.mark_for_hdel(instance)


@event.listens_for(Session, 'pending_to_persistent')
def added_to_database(session, instance):
    if session.redis_bind is not None and instance is not None:
        session.mark_for_hmset_dict(instance)
