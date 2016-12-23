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


from tests.integration.models.orm.fixtures import Model13
from unittest import mock
from asyncio import coroutine
import pytest
import ujson


def CoroMock():
    coro = mock.MagicMock(name="CoroutineResult")
    corofunc = mock.MagicMock(name="CoroutineFunction", side_effect=coroutine(coro))
    corofunc.coro = coro
    return corofunc


class TestModelBaseGet(object):

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_query_get_calls_hmget_correctly(self, session, redis, request):
        met_bkp = redis.hmget
        def fin():
            redis.hmget = met_bkp
        request.addfinalizer(fin)
        redis.hmget = CoroMock()

        await Model13.get(session, {'id': 1})
        assert redis.hmget.call_args_list == [mock.call('Model13', b'1')]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_query_get_calls_hmget_correctly_with_two_ids(self, session, redis, request):
        met_bkp = redis.hmget
        def fin():
            redis.hmget = met_bkp
        request.addfinalizer(fin)
        redis.hmget = CoroMock()

        await Model13.get(session, [{'id': 1}, {'id': 2}])
        assert redis.hmget.call_args_list == [mock.call('Model13', b'1', b'2')]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_query_get_builds_redis_left_ids_correctly_with_result_found_on_redis_with_one_id(
            self, session, redis, request):
        met_bkp = redis.hmget
        def fin():
            redis.hmget = met_bkp
        request.addfinalizer(fin)
        redis.hmget = CoroMock()

        session.add(await Model13.new(session, id=1))
        await session.commit()
        redis.hmget.coro.return_value = [None]
        assert await Model13.get(session, {'id': 1}) == [{'id': 1}]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_query_get_builds_redis_left_ids_correctly_with_no_result_found_on_redis_with_two_ids(
            self, session, redis, request):
        met_bkp = redis.hmget
        def fin():
            redis.hmget = met_bkp
        request.addfinalizer(fin)
        redis.hmget = CoroMock()

        session.add_all([await Model13.new(session, id=1), await Model13.new(session, id=2)])
        await session.commit()
        redis.hmget.coro.return_value = [None, None]
        assert await Model13.get(session, [{'id': 1}, {'id': 2}]) == [{'id': 1}, {'id': 2}]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_query_get_builds_redis_left_ids_correctly_with_no_result_found_on_redis_with_three_ids(
            self, session, redis, request):
        met_bkp = redis.hmget
        def fin():
            redis.hmget = met_bkp
        request.addfinalizer(fin)
        redis.hmget = CoroMock()

        session.add_all([await Model13.new(session, id=1), await Model13.new(session, id=2), await Model13.new(session, id=3)])
        await session.commit()
        redis.hmget.coro.return_value = [None, None, None]
        assert await Model13.get(session, [{'id': 1}, {'id': 2}, {'id': 3}]) == \
            [{'id': 1}, {'id': 2}, {'id': 3}]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_query_get_builds_redis_left_ids_correctly_with_no_result_found_on_redis_with_four_ids(
            self, session, redis, request):
        met_bkp = redis.hmget
        def fin():
            redis.hmget = met_bkp
        request.addfinalizer(fin)
        redis.hmget = CoroMock()

        session.add_all([await Model13.new(session, id=1), await Model13.new(session, id=2), await Model13.new(session, id=3), await Model13.new(session, id=4)])
        await session.commit()
        redis.hmget.coro.return_value = [None, None, None, None]
        assert await Model13.get(session, [{'id': 1}, {'id': 2}, {'id': 3}, {'id': 4}]) == \
            [{'id': 1}, {'id': 2}, {'id': 3}, {'id': 4}]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_if_query_get_builds_redis_left_ids_correctly_with_one_not_found_on_redis(
            self, session, redis, request):
        met_bkp = redis.hmget
        def fin():
            redis.hmget = met_bkp
        request.addfinalizer(fin)
        redis.hmget = CoroMock()

        session.add(await Model13.new(session, id=1))
        await session.commit()
        redis.hmget.coro.return_value = [None, ujson.dumps({'id': 2})]
        assert await Model13.get(session, [{'id': 1}, {'id': 2}]) == [{'id': 1}, {'id': 2}]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_with_ids_and_limit(self, session, redis, request):
        met_bkp = redis.hmget
        def fin():
            redis.hmget = met_bkp
        request.addfinalizer(fin)
        redis.hmget = CoroMock()

        session.add_all([await Model13.new(session, id=1), await Model13.new(session, id=2), await Model13.new(session, id=3)])
        await session.commit()
        await Model13.get(session, [{'id': 1}, {'id': 2}, {'id': 3}, {'id': 4}], limit=2)
        assert redis.hmget.call_args_list == [mock.call('Model13', b'1', b'2')]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_with_ids_and_offset(self, session, redis, request):
        met_bkp = redis.hmget
        def fin():
            redis.hmget = met_bkp
        request.addfinalizer(fin)
        redis.hmget = CoroMock()

        session.add_all([await Model13.new(session, id=1), await Model13.new(session, id=2), await Model13.new(session, id=3)])
        await session.commit()
        await Model13.get(session, [{'id': 1}, {'id': 2}, {'id': 3}, {'id': 4}], offset=2)
        assert redis.hmget.call_args_list == [mock.call('Model13', b'3', b'4')]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_with_ids_and_limit_and_offset(self, session, redis, request):
        met_bkp = redis.hmget
        def fin():
            redis.hmget = met_bkp
        request.addfinalizer(fin)
        redis.hmget = CoroMock()

        session.add_all([await Model13.new(session, id=1), await Model13.new(session, id=2), await Model13.new(session, id=3)])
        await session.commit()
        await Model13.get(session, [{'id': 1}, {'id': 2}, {'id': 3}, {'id': 4}], limit=2, offset=1)
        assert redis.hmget.call_args_list == [mock.call('Model13', b'2', b'3')]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_with_missing_id(self, session, redis, request):
        met_bkp = redis.hmget
        def fin():
            redis.hmget = met_bkp
        request.addfinalizer(fin)
        redis.hmget = CoroMock()

        session.add(await Model13.new(session, id=1))
        await session.commit()
        redis.hmget.coro.return_value = [None, None]
        assert await Model13.get(session, [{'id': 1}, {'id': 2}]) == [{'id': 1}]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_with_missing_all_ids(self, session, redis, request):
        met_bkp = redis.hmget
        def fin():
            redis.hmget = met_bkp
        request.addfinalizer(fin)
        redis.hmget = CoroMock()

        redis.hmget.coro.return_value = [None, None]
        assert await Model13.get(session, [{'id': 1}, {'id': 2}]) == []

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_without_ids(self, session, redis, request):
        await Model13.insert(session, {})
        assert await Model13.get(session) == [{'id': 1}]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_without_ids_and_with_limit(self, session, redis, request):
        await Model13.insert(session, [{}, {}, {}])
        assert await Model13.get(session, limit=2) == [{'id': 1}, {'id': 2}]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_without_ids_and_with_offset(self, session, redis, request):
        await Model13.insert(session, [{}, {}, {}])
        assert await Model13.get(session, offset=1) == [{'id': 2}, {'id': 3}]

    @pytest.mark.asyncio(forbid_global_loop=False)
    async def test_without_ids_and_with_limit_and_offset(self, session, redis, request):
        await Model13.insert(session, [{}, {}, {}])
        assert await Model13.get(session, limit=1, offset=1) == [{'id': 2}]
