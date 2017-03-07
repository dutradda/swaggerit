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


from swaggerit.models.orm.jobs import JobsModel
from swaggerit.aiohttp_api import AioHttpAPI
from tests.integration.conftest import api as api_, client as client_
from unittest import mock
import pytest
import random
import ujson


class ModelAioHttpJobs(JobsModel):
    __swagger_json__ = {
        'paths': {
            '/': {
                'post': {
                    'operationId': 'post_job',
                    'responses': {
                        '201': {'description': 'Created'}
                    }
                },
                'get': {
                    'parameters': [{
                        'name': 'job_hash',
                        'in': 'query',
                        'type': 'string'
                    }],
                    'operationId': 'get_job',
                    'responses': {
                        '200': {'description': 'Got'}
                    }
                }
            },
            '/sync': {
                'post': {
                    'operationId': 'post_sync_job',
                    'responses': {
                        '201': {'description': 'Created'}
                    }
                },
                'get': {
                    'parameters': [{
                        'name': 'job_hash',
                        'in': 'query',
                        'type': 'string'
                    }],
                    'operationId': 'get_sync_job',
                    'responses': {
                        '200': {'description': 'Got'}
                    }
                }
            }
        }
    }

    async def post_job(self, req, session):
        session = self._copy_session(session)
        return self._create_job(self._test, 'test', req, session, test='test')

    async def _test(self, req, session, test):
        return test

    async def get_job(self, req, session):
        resp = await self._get_job('test', req, session)
        return resp

    async def post_sync_job(self, req, session):
        session = self._copy_session(session)
        return self._create_job(self._sync_test, 'test', req, session, test='test')

    def _sync_test(self, req, session, test):
        return test

    async def get_sync_job(self, req, session):
        resp = await self._get_job('test', req, session)
        return resp


@pytest.fixture
def models():
    yield [ModelAioHttpJobs()]
    ModelAioHttpJobs.__all_models__.pop('aio_http_jobs')


class TestModelAioHttpJobs(object):

    async def test_post(self, client):
        random.seed(0)
        resp = await (await client).post('/')
        assert resp.status == 201
        assert await resp.json() == {'job_hash': 'e3e70682c2094cac629f6fbed82c07cd'}

    async def test_get_success(self, client):
        random.seed(0)
        client = await client
        await client.post('/')

        query = {'job_hash': 'e3e70682c2094cac629f6fbed82c07cd'}
        while True:
            resp = await client.get('/', params=query)
            if (await resp.json())['status'] != 'running':
                break

        assert resp.status == 200
        assert (await resp.json())['result'] == 'test'
        assert (await resp.json())['status'] == 'done'

    async def test_get_last(self, client):
        random.seed(0)
        client = await client
        await client.post('/')

        query = {'job_hash': 'last'}
        while True:
            resp = await client.get('/', params=query)
            if (await resp.json())['status'] != 'running':
                break

        assert resp.status == 200
        assert (await resp.json())['result'] == 'test'
        assert (await resp.json())['status'] == 'done'


    async def test_get_all(self, client):
        random.seed(0)
        client = await client
        await client.post('/')

        while True:
            resp = await client.get('/')
            if not 'running' in (await resp.json()):
                break

        assert resp.status == 200
        assert (await resp.json())['done']['e3e70682c2094cac629f6fbed82c07cd']['result'] == 'test'


    async def test_get_error(self, client, request):
        test_func = ModelAioHttpJobs._test
        def fin():
            ModelAioHttpJobs._test = test_func
        request.addfinalizer(fin)

        async def callback(*args, **kwargs):
            raise Exception('test')

        ModelAioHttpJobs._test = callback
        random.seed(0)
        client = await client
        await client.post( '/')

        query = {'job_hash': 'e3e70682c2094cac629f6fbed82c07cd'}
        while True:
            resp = await client.get( '/', params=query)
            if (await resp.json())['status'] != 'running':
                break

        assert resp.status == 200
        assert (await resp.json())['result'] == {'message': 'test', 'name': 'Exception'}
        assert (await resp.json())['status'] == 'error'


class TestModelAioHttpJobsSync(object):

    async def test_post(self, client):
        random.seed(0)
        resp = await (await client).post('/sync')
        assert resp.status == 201
        assert await resp.json() == {'job_hash': 'e3e70682c2094cac629f6fbed82c07cd'}

    async def test_get_success(self, client):
        random.seed(0)
        client = await client
        await client.post('/sync')

        query = {'job_hash': 'e3e70682c2094cac629f6fbed82c07cd'}
        while True:
            resp = await client.get('/sync', params=query)
            if (await resp.json())['status'] != 'running':
                break

        assert resp.status == 200
        assert (await resp.json())['result'] == 'test'
        assert (await resp.json())['status'] == 'done'

    async def test_get_last(self, client):
        random.seed(0)
        client = await client
        await client.post('/sync')

        query = {'job_hash': 'last'}
        while True:
            resp = await client.get('/sync', params=query)
            if (await resp.json())['status'] != 'running':
                break

        assert resp.status == 200
        assert (await resp.json())['result'] == 'test'
        assert (await resp.json())['status'] == 'done'

    async def test_get_all(self, client):
        random.seed(0)
        client = await client
        await client.post('/sync')

        while True:
            resp = await client.get('/sync')
            if not 'running' in (await resp.json()):
                break

        assert resp.status == 200
        assert (await resp.json())['done']['e3e70682c2094cac629f6fbed82c07cd']['result'] == 'test'

    async def test_get_error(self, client, request):
        test_func = ModelAioHttpJobs._sync_test
        def fin():
            ModelAioHttpJobs._sync_test = test_func
        request.addfinalizer(fin)

        def callback(*args, **kwargs):
            raise Exception('test')

        ModelAioHttpJobs._sync_test = callback
        random.seed(0)
        client = await client
        await client.post( '/sync')

        query = {'job_hash': 'e3e70682c2094cac629f6fbed82c07cd'}
        while True:
            resp = await client.get( '/sync', params=query)
            if (await resp.json())['status'] != 'running':
                break

        assert resp.status == 200
        assert (await resp.json())['result'] == {'message': 'test', 'name': 'Exception'}
        assert (await resp.json())['status'] == 'error'
