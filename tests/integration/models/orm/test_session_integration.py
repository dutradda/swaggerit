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


from tests.integration.models.orm.fixtures import *
from unittest import mock
import pytest
import ujson


class ExceptionTest(Exception):
    pass


async def raises(*args, **kwargs):
    raise ExceptionTest()


class TestSessionCommitRedisSet(object):

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_instance_is_seted_on_redis(self, session, redis):
        session.add(await Model10.new(session, id=1))
        await session.commit()

        assert await redis.hgetall(Model10.__key__) == {b'1': ujson.dumps({'id': 1}).encode()}

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_two_instance_are_seted_on_redis(self, session, redis):
        session.add(await Model10.new(session, id=1))
        session.add(await Model10.new(session, id=2))
        await session.commit()

        assert await redis.hgetall(Model10.__key__) == {
            b'1': ujson.dumps({'id': 1}).encode(),
            b'2': ujson.dumps({'id': 2}).encode()
        }

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_two_commits_sets_redis_correctly(self, session, redis):
        session.add(await Model10.new(session, id=1))
        await session.commit()

        assert await redis.hgetall(Model10.__key__) == {
            b'1': ujson.dumps({b'id': 1}).encode()
        }

        session.add(await Model10.new(session, id=2))
        await session.commit()

        assert await redis.hgetall(Model10.__key__) == {
            b'1': ujson.dumps({b'id': 1}).encode(),
            b'2': ujson.dumps({b'id': 2}).encode()
        }

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_error_right_raised(self, session, redis, request):
        met_bkp = redis.hmset_dict
        def fin():
            redis.hmset_dict = met_bkp
        request.addfinalizer(fin)

        session.add(await Model10.new(session, id=1))
        redis.hmset_dict = raises

        with pytest.raises(ExceptionTest):
            await session.commit()

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_istances_are_seted_on_redis_with_two_models_correctly(
            self, session, redis):
        session.add(await Model10.new(session, id=1))
        session.add(await Model11.new(session, id=1))
        session.add(await Model10.new(session, id=2))
        session.add(await Model11.new(session, id=2))
        await session.commit()

        assert await redis.hgetall(Model10.__key__) == {
            b'1': ujson.dumps({b'id': 1}).encode(),
            b'2': ujson.dumps({b'id': 2}).encode()
        }
        assert await redis.hgetall(Model11.__key__) == {
            b'1': ujson.dumps({b'id': 1}).encode(),
            b'2': ujson.dumps({b'id': 2}).encode()
        }

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_two_commits_sets_redis_with_two_models_correctly(
            self, session, redis):
        session.add(await Model10.new(session, id=1))
        session.add(await Model11.new(session, id=1))
        await session.commit()

        assert await redis.hgetall(Model10.__key__) == {
            b'1': ujson.dumps({b'id': 1}).encode()
        }
        assert await redis.hgetall(Model11.__key__) == {
            b'1': ujson.dumps({b'id': 1}).encode()
        }

        session.add(await Model10.new(session, id=2))
        session.add(await Model11.new(session, id=2))
        await session.commit()

        assert await redis.hgetall(Model10.__key__) == {
            b'1': ujson.dumps({b'id': 1}).encode(),
            b'2': ujson.dumps({b'id': 2}).encode()
        }
        assert await redis.hgetall(Model11.__key__) == {
            b'1': ujson.dumps({b'id': 1}).encode(),
            b'2': ujson.dumps({b'id': 2}).encode()
        }


class TestSessionCommitRedisDelete(object):

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_instance_is_deleted_from_redis(self, session, redis):
        inst1 = await Model10.new(session, id=1)
        session.add(inst1)
        await session.commit()

        assert await redis.hgetall(Model10.__key__) == {
            b'1': ujson.dumps({b'id': 1}).encode()
        }

        session.delete(inst1)
        await session.commit()

        assert await redis.hgetall(Model10.__key__) == {}

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_two_instance_are_deleted_from_redis(self, session, redis):
        inst1 = await Model10.new(session, id=1)
        inst2 = await Model10.new(session, id=2)
        session.add_all([inst1, inst2])
        await session.commit()

        assert await redis.hgetall(Model10.__key__) == {
            b'1': ujson.dumps({b'id': 1}).encode(),
            b'2': ujson.dumps({b'id': 2}).encode()
        }

        session.delete(inst1)
        session.delete(inst2)
        await session.commit()

        assert await redis.hgetall(Model10.__key__) == {}

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_two_commits_delete_redis_correctly(self, session, redis):
        inst1 = await Model10.new(session, id=1)
        inst2 = await Model10.new(session, id=2)
        session.add_all([inst1, inst2])
        await session.commit()

        assert await redis.hgetall(Model10.__key__) == {
            b'1': ujson.dumps({b'id': 1}).encode(),
            b'2': ujson.dumps({b'id': 2}).encode()
        }

        session.delete(inst1)
        await session.commit()

        assert await redis.hgetall(Model10.__key__) == {
            b'2': ujson.dumps({b'id': 2}).encode()
        }

        session.delete(inst2)
        await session.commit()

        assert await redis.hgetall(Model10.__key__) == {}

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_error_right_raised(self, session, redis, request):
        met_bkp = redis.hdel
        def fin():
            redis.hdel = met_bkp
        request.addfinalizer(fin)

        inst1 = await Model10.new(session, id=1)
        session.add(inst1)
        await session.commit()
        session.delete(inst1)
        redis.hdel = raises
        with pytest.raises(ExceptionTest):
            await session.commit()

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_istances_are_seted_on_redis_with_two_models_correctly(
            self, session, redis):
        inst1 = await Model10.new(session, id=1)
        inst2 = await Model10.new(session, id=2)
        inst3 = await Model11.new(session, id=1)
        inst4 = await Model11.new(session, id=2)
        session.add_all([inst1, inst2, inst3, inst4])
        await session.commit()

        assert await redis.hgetall(Model10.__key__) == {
            b'1': ujson.dumps({b'id': 1}).encode(),
            b'2': ujson.dumps({b'id': 2}).encode()
        }
        assert await redis.hgetall(Model11.__key__) == {
            b'1': ujson.dumps({b'id': 1}).encode(),
            b'2': ujson.dumps({b'id': 2}).encode()
        }

        session.delete(inst1)
        session.delete(inst2)
        session.delete(inst3)
        session.delete(inst4)
        await session.commit()

        assert await redis.hgetall(Model10.__key__) == {}
        assert await redis.hgetall(Model11.__key__) == {}

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_two_commits_delete_redis_with_two_models_correctly(
            self, session, redis):
        inst1 = await Model10.new(session, id=1)
        inst2 = await Model10.new(session, id=2)
        inst3 = await Model11.new(session, id=1)
        inst4 = await Model11.new(session, id=2)
        session.add_all([inst1, inst2, inst3, inst4])
        await session.commit()

        assert await redis.hgetall(Model10.__key__) == {
            b'1': ujson.dumps({b'id': 1}).encode(),
            b'2': ujson.dumps({b'id': 2}).encode()
        }
        assert await redis.hgetall(Model11.__key__) == {
            b'1': ujson.dumps({b'id': 1}).encode(),
            b'2': ujson.dumps({b'id': 2}).encode()
        }

        session.delete(inst1)
        session.delete(inst3)
        await session.commit()

        assert await redis.hgetall(Model10.__key__) == {
            b'2': ujson.dumps({b'id': 2}).encode()
        }
        assert await redis.hgetall(Model11.__key__) == {
            b'2': ujson.dumps({b'id': 2}).encode()
        }

        session.delete(inst2)
        session.delete(inst4)
        await session.commit()

        assert await redis.hgetall(Model10.__key__) == {}
        assert await redis.hgetall(Model11.__key__) == {}
