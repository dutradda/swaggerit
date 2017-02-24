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



from swaggerit.models.orm.factory import FactoryOrmModels
from time import sleep
import pytest


ModelTest = FactoryOrmModels.make_redis_elsearch('ModelTest', ['id'], use_elsearch=True)


@pytest.fixture
def obj():
	return {
        'id': 1,
        'field1': 'test',
        'field2': {
            'fid': '1'
        }
    }


class TestModelRedisElSearchPost(object):

    async def test_insert(self, obj, session):
        assert await ModelTest.insert(session, obj) == [obj]

    async def test_insert_with_list(self, obj, session):
        assert await ModelTest.insert(session, [obj]) == [obj]

    async def test_update(self, obj, session):
        await ModelTest.insert(session, obj)
        obj['field1'] = 'testing'
        assert await ModelTest.update(session, obj) == [obj]

    async def test_update_with_ids(self, obj, session):
        await ModelTest.insert(session, obj)
        obj['id'] = 2
        assert await ModelTest.update(session, obj, '1') == [obj]

    async def test_delete(self, obj, session):
        await ModelTest.insert(session, obj)
        assert await ModelTest.delete(session, '1') == 1

    async def test_get(self, obj, session):
        await ModelTest.insert(session, obj)
        assert await ModelTest.get(session, '1') == [obj]

    async def test_search(self, obj, session):
        await ModelTest.insert(session, obj)
        await session.elsearch_bind.refresh_index()
        assert list(await ModelTest.search(session, 'test')) == [obj]

    async def test_search_deleted(self, obj, session):
        await ModelTest.insert(session, obj)
        await session.elsearch_bind.refresh_index()
        assert list(await ModelTest.search(session, 'test')) == [obj]

        await ModelTest.delete(session, '1')
        await session.elsearch_bind.refresh_index()
        assert list(await ModelTest.search(session, 'test')) == []

    async def test_search_updated(self, obj, session):
        await ModelTest.insert(session, obj)
        await session.elsearch_bind.refresh_index()
        assert list(await ModelTest.search(session, 'test')) == [obj]
        assert list(await ModelTest.search(session, 'testing')) == []

        obj['field1'] = 'testing'
        await ModelTest.update(session, obj)
        await session.elsearch_bind.refresh_index()
        assert list(await ModelTest.search(session, 'testing')) == [obj]
