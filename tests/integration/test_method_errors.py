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


from swaggerit.method import SwaggerMethod
from swaggerit.request import SwaggerRequest
from tests.integration.fixtures import ModelSQLAlchemyRedisBase
import pytest
import ujson
import asyncio
import sqlalchemy as sa


class Model2Swagger(ModelSQLAlchemyRedisBase):
    __tablename__ = 'model2_swagger'
    __table_args__ = {'mysql_engine': 'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)


class Model1Swagger(ModelSQLAlchemyRedisBase):
    __tablename__ = 'model1_swagger'
    __table_args__ = {'mysql_engine': 'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    m2_id = sa.Column(sa.ForeignKey('model2_swagger.id'))
    model2_ = sa.orm.relationship('Model2Swagger')

    __swagger_json__ = {
        'paths': {
            '/model1/': {
                'post': {
                    'operationId': 'swagger_insert',
                    'responses': {'200': {'description': 'test'}},
                    'parameters': [{
                        'name': 'body',
                        'in': 'body',
                        'schema': {'type': 'array'}
                    }]
                }
            },
            '/model1/{id}/': {
                'patch': {
                    'operationId': 'swagger_update',
                    'responses': {'200': {'description': 'test'}},
                    'parameters': [{
                        'name': 'body',
                        'in': 'body',
                        'schema': {'type': 'object'}
                    },{
                        'name': 'id',
                        'in': 'path',
                        'required': True,
                        'type': 'integer'
                    }]
                }
            }
        }
    }


@pytest.fixture(scope='module')
def post_method():
    return SwaggerMethod(
        Model1Swagger.swagger_insert,
        Model1Swagger.__swagger_json__['paths']['/model1/']['post'],
        {}, '')


@pytest.fixture
def stream(loop):
    return asyncio.StreamReader(loop=loop)


class TestMethodErrorHandlingPost(object):

    async def test_integrity_error_handling_with_duplicated_key(self, post_method, stream, session):
        stream.feed_data(ujson.dumps([{'id': 1}, {'id': 1}]).encode())
        stream.feed_eof()
        request = SwaggerRequest('/model1/', 'post', body=stream, headers={'content-type': 'application/json'})
        resp = await post_method(request, session)

        assert resp.status_code == 400
        assert ujson.loads(resp.body) == {
            'params': [{'id': 1, 'm2_id': None}, {'id': 1, 'm2_id': None}],
            'database message': {
                'message': "Duplicate entry '1' for key 'PRIMARY'",
                'code': 1062
            }
        }

    async def test_integrity_error_handling_with_foreign_key(self, post_method, stream, session):
        stream.feed_data(ujson.dumps([{'m2_id': 1}]).encode())
        stream.feed_eof()
        request = SwaggerRequest('/model1/', 'post', body=stream, headers={'content-type': 'application/json'})
        resp = await post_method(request, session)

        assert resp.status_code == 400
        assert ujson.loads(resp.body) == {
            'params': {'m2_id': 1},
            'database message': {
                'message':  'Cannot add or update a child row: '
                            'a foreign key constraint fails '
                            '(`swaggerit_test`.`model1_swagger`, '
                            'CONSTRAINT `model1_swagger_ibfk_1` FOREIGN '
                            'KEY (`m2_id`) REFERENCES `model2_swagger` '
                            '(`id`))',
                'code': 1452
            }
        }

    async def test_json_validation_error_handling(self, post_method, stream, session):
        stream.feed_data(b'"test"')
        stream.feed_eof()
        request = SwaggerRequest('/model1/', 'post', body=stream, headers={'content-type': 'application/json'})
        resp = await post_method(request, session)

        assert resp.status_code == 400
        assert ujson.loads(resp.body) == {
            'instance': 'test',
            'message': "'test' is not of type 'array'. Failed validating instance for schema['type']",
            'schema': {
                'type': 'array'
            }
        }

    async def test_json_error_handling(self, post_method, stream, session):
        stream.feed_data(b'test')
        stream.feed_eof()
        request = SwaggerRequest('/model1/', 'post', body=stream, headers={'content-type': 'application/json'})
        resp = await post_method(request, session)

        assert resp.status_code == 400
        assert ujson.loads(resp.body) == {
            'instance': 'test',
            'message': "Unexpected character found when decoding 'true'"
        }

    async def test_model_base_error_handling_with_post_and_with_nested_delete(self, post_method, stream, session):
        body = [{'model2_': {'id': 1, '_operation': 'delete'}}]
        stream.feed_data(ujson.dumps(body).encode())
        stream.feed_eof()
        request = SwaggerRequest('/model1/', 'post', body=stream, headers={'content-type': 'application/json'})
        resp = await post_method(request, session)

        assert resp.status_code == 400
        assert ujson.loads(resp.body) == {
            'instance': body,
            'message': "Can't execute nested 'delete' operation"
        }

    async def test_model_base_error_handling_with_post_and_with_nested_remove(self, post_method, stream, session):
        body = [{'model2_': {'id': 1, '_operation': 'remove'}}]
        stream.feed_data(ujson.dumps(body).encode())
        stream.feed_eof()
        request = SwaggerRequest('/model1/', 'post', body=stream, headers={'content-type': 'application/json'})
        resp = await post_method(request, session)

        assert resp.status_code == 400
        assert ujson.loads(resp.body) == {
            'instance': body,
            'message': "Can't execute nested 'remove' operation"
        }

    async def test_model_base_error_handling_with_post_and_with_nested_update(self, post_method, stream, session):
        body = [{'model2_': {'id': 1, '_operation': 'update'}}]
        stream.feed_data(ujson.dumps(body).encode())
        stream.feed_eof()
        request = SwaggerRequest('/model1/', 'post', body=stream, headers={'content-type': 'application/json'})
        resp = await post_method(request, session)

        assert resp.status_code == 400
        assert ujson.loads(resp.body) == {
            'instance': body,
            'message': "Can't execute nested 'update' operation"
        }


@pytest.fixture(scope='module')
def patch_method():
    return SwaggerMethod(
        Model1Swagger.swagger_update,
        Model1Swagger.__swagger_json__['paths']['/model1/{id}/']['patch'],
        {}, '')


class TestMethodErrorHandlingPatch(object):

    async def test_model_base_error_handling_with_patch_and_with_nested_delete(self, patch_method, post_method, stream, session):
        stream.feed_data(b'[{}]')
        stream.feed_eof()
        request = SwaggerRequest('/model1/1/', 'patch', body=stream, headers={'content-type': 'application/json'})
        await post_method(request, session)

        stream = asyncio.StreamReader(loop=session.loop)
        body = {'model2_': {'id': 1, '_operation': 'delete'}}
        stream.feed_data(ujson.dumps(body).encode())
        stream.feed_eof()
        request = SwaggerRequest('/model1/1/', 'patch', path_params={'id': 1}, body=stream, headers={'content-type': 'application/json'})
        resp = await patch_method(request, session)

        assert resp.status_code == 400
        assert ujson.loads(resp.body) == {
            'instance': [body],
            'message': "Can't execute nested 'delete' operation"
        }

    async def test_model_base_error_handling_with_patch_and_with_nested_remove(self, patch_method, post_method, stream, session):
        stream.feed_data(b'[{}]')
        stream.feed_eof()
        request = SwaggerRequest('/model1/1/', 'patch', body=stream, headers={'content-type': 'application/json'})
        await post_method(request, session)

        stream = asyncio.StreamReader(loop=session.loop)
        body = {'model2_': {'id': 1, '_operation': 'remove'}}
        stream.feed_data(ujson.dumps(body).encode())
        stream.feed_eof()
        request = SwaggerRequest('/model1/1/', 'patch', path_params={'id': 1}, body=stream, headers={'content-type': 'application/json'})
        resp = await patch_method(request, session)

        assert resp.status_code == 400
        assert ujson.loads(resp.body) == {
            'instance': [body],
            'message': "Can't execute nested 'remove' operation"
        }

    async def test_model_base_error_handling_with_patch_and_with_nested_update(self, patch_method, post_method, stream, session):
        stream.feed_data(b'[{}]')
        stream.feed_eof()
        request = SwaggerRequest('/model1/1/', 'patch', body=stream, headers={'content-type': 'application/json'})
        await post_method(request, session)

        stream = asyncio.StreamReader(loop=session.loop)
        body = {'model2_': {'id': 1, '_operation': 'update'}}
        stream.feed_data(ujson.dumps(body).encode())
        stream.feed_eof()
        request = SwaggerRequest('/model1/1/', 'patch', path_params={'id': 1}, body=stream, headers={'content-type': 'application/json'})
        resp = await patch_method(request, session)

        assert resp.status_code == 400
        assert ujson.loads(resp.body) == {
            'instance': [body],
            'message': "Can't execute nested 'update' operation"
        }
