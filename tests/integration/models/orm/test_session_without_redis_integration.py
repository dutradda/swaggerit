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
import pytest
from unittest import mock


class TestSessionCommitWithoutRedis(object):

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_set_without_redis(self, redis, session, request):
        met_bkp = redis.hgetall
        def fin():
            redis.hgetall = met_bkp
        request.addfinalizer(fin)
        redis.hgetall = mock.MagicMock()

        session.redis_bind = None
        session.add(await Model1.new(session, id=1))
        await session.commit()
        assert redis.hgetall.called == False

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_delete_without_redis(self, redis, session, request):
        met_bkp = redis.hdel
        def fin():
            redis.hdel = met_bkp
        request.addfinalizer(fin)
        redis.hdel = mock.MagicMock()

        session.redis_bind = None
        m1 = await Model1.new(session, id=1)
        session.add(m1)
        await session.commit()
        session.delete(m1)
        await session.commit()
        assert redis.hdel.called == False


class TestSessionCommitRedisWithoutUseRedisFlag(object):

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_instance_is_not_setted_on_redis(self, session, redis, request):
        met_bkp = redis.hmset
        def fin():
            redis.hmset = met_bkp
        request.addfinalizer(fin)
        redis.hmset = mock.MagicMock()

        session.add(await Model12.new(session, id=1))
        await session.commit()

        assert redis.hmset.call_args_list == []

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_instance_is_not_deleted_from_redis(self, session, redis, request):
        met_bkp = redis.hdel
        def fin():
            redis.hdel = met_bkp
        request.addfinalizer(fin)
        redis.hdel = mock.MagicMock()

        inst1 = await Model12.new(session, id=1)
        session.add(inst1)
        await session.commit()

        session.delete(inst1)
        await session.commit()

        assert redis.hdel.call_args_list == []
