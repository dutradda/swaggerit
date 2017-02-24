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
from collections import OrderedDict, deque
from copy import deepcopy
import ujson


class ModelRedisElSearchMeta(_ModelRedisBaseMeta):
    CHUNKS = 100
    __use_elsearch__ = False

    async def insert(cls, session, objs, **kwargs):
        input_ = deepcopy(objs)
        objs = cls._to_list(objs)
        ids_objs_map = dict()
        counter = 0

        for obj in objs:
            obj_key = cls.get_instance_key(obj)
            ids_objs_map[obj_key] = cls._pack_obj(obj)
            counter += 1

            if counter == cls.CHUNKS:
                await session.redis_bind.hmset_dict(cls.__key__, ids_objs_map)

                if cls.__use_elsearch__:
                    await session.elsearch_bind.bulk_create_dict(cls.__key__, ids_objs_map)

                ids_objs_map = dict()
                counter = 0

        if ids_objs_map:
            await session.redis_bind.hmset_dict(cls.__key__, ids_objs_map)

            if cls.__use_elsearch__:
                await session.elsearch_bind.bulk_create_dict(cls.__key__, ids_objs_map)

        return objs

    async def update(cls, session, objs, ids=None, **kwargs):
        input_ = deepcopy(objs)

        objs = cls._to_list(objs)
        if ids:
            keys_objs_map = cls._build_keys_objs_map_with_ids(objs, ids)
        else:
            keys_objs_map = OrderedDict([(cls.get_instance_key(obj), obj) for obj in objs])

        keys = set(keys_objs_map.keys())
        keys.difference_update(set(await session.redis_bind.hkeys(cls.__key__)))
        keys.intersection_update(keys)
        invalid_keys = keys

        for key in invalid_keys:
            keys_objs_map.pop(key, None)

        keys_objs_to_del = dict()

        if keys_objs_map:
            set_map = OrderedDict()
            counter = 0
            for key in set(keys_objs_map.keys()):
                obj = keys_objs_map[key]
                if obj.get('_operation') == 'delete':
                    keys_objs_to_del[key] = obj
                    keys_objs_map.pop(key)
                    continue

                set_map[key] = cls._pack_obj(obj)
                counter += 1

                if counter == cls.CHUNKS:
                    await session.redis_bind.hmset_dict(cls.__key__, set_map)

                    if cls.__use_elsearch__:
                        await session.elsearch_bind.bulk_update_dict(cls.__key__, set_map)

                    set_map = OrderedDict()
                    counter = 0

            if set_map:
                await session.redis_bind.hmset_dict(cls.__key__, set_map)

                if cls.__use_elsearch__:
                    await session.elsearch_bind.bulk_update_dict(cls.__key__, set_map)

        if keys_objs_to_del:
            await session.redis_bind.hdel(cls.__key__, *keys_objs_to_del.keys())

            if cls.__use_elsearch__:
                await session.elsearch_bind.bulk_delete(cls.__key__, keys_objs_to_del.keys())

        return list(keys_objs_map.values()) or list(keys_objs_to_del.values())

    def _build_keys_objs_map_with_ids(cls, objs, ids):
        ids = cls._to_list(ids)
        keys_objs_map = OrderedDict()

        for key, obj in zip(ids, objs):
            keys_objs_map[key.encode()] = obj

        return keys_objs_map

    async def delete(cls, session, ids, **kwargs):
        keys = cls._to_list(ids)
        if keys:
            ret = await session.redis_bind.hdel(cls.__key__, *keys)

            if cls.__use_elsearch__:
                await session.elsearch_bind.bulk_delete(cls.__key__, keys)

            return ret

    async def get(cls, session, ids=None, limit=None, offset=None, **kwargs):
        if limit is not None and offset is not None:
            limit += offset

        elif ids is None and limit is None and offset is None:
            return cls._unpack_objs(await session.redis_bind.hgetall(cls.__key__))

        if ids is None:
            keys = [k for k in await session.redis_bind.hkeys(cls.__key__)][offset:limit]
            if keys:
                return cls._unpack_objs(await session.redis_bind.hmget(cls.__key__, *keys))
            else:
                return []
        else:
            ids = cls._to_list(ids)
            return cls._unpack_objs(await session.redis_bind.hmget(cls.__key__, *ids[offset:limit]))

    async def search(cls, session, pattern, page=0, size=100):
        if cls.__use_elsearch__:
            result = await session.elsearch_bind.search(cls.__key__, pattern, page, size)
            result = result.get('hits', {}).get('hits', [])
            final_result = deque()

            while result:
                final_result.appendleft(result.pop()['_source'])

            return final_result

        else:
            return []
