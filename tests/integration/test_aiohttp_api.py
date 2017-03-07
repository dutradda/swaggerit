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


from tests.integration.fixtures import ModelSQLAlchemyRedisBase
import pytest
import sqlalchemy as sa


class Model2AioHttp(ModelSQLAlchemyRedisBase):
    __tablename__ = 'model2_aiohttp'
    __table_args__ = {'mysql_engine': 'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)


class Model1AioHttp(ModelSQLAlchemyRedisBase):
    __tablename__ = 'model1_aiohttp'
    __table_args__ = {'mysql_engine': 'innodb'}
    id = sa.Column(sa.Integer, primary_key=True)
    m2_id = sa.Column(sa.ForeignKey('model2_aiohttp.id'))
    model2 = sa.orm.relationship('Model2AioHttp')

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


@pytest.fixture
def models():
    yield [Model1AioHttp]

    Model1AioHttp.__api__ = None


class TestAioHttpAPI(object):

    async def test_insert(self, client, session):
        headers = {'Content-Type': 'application/json'}
        resp = await (await client).post( '/model1', data=b'[{}]', headers=headers)
        assert resp.status == 201
        assert await resp.json() == [{'id': 1, 'm2_id': None, 'model2': None}]

    async def test_get_swagger_json(self, client, session):
        resp = await (await client).get( '/doc/swagger.json')
        assert resp.status == 200
        assert await resp.json() == {
            'swagger': '2.0',
            'info': {'title': 'Test API', 'version': '1.0.0'},
            'paths': {
                '/model1/{id}/': {
                    'patch': {
                        'parameters': [{
                            'name': 'body',
                            'schema': {'type': 'object'},
                            'in': 'body'
                        },{
                            'name': 'id',
                            'required': True,
                            'in': 'path',
                            'type': 'integer'
                        }],
                        'responses': {'200': {'description': 'test'}},
                        'operationId': 'Model1AioHttp.swagger_update'
                    },
                    'options': {
                        'responses': {
                            '204': {
                                'headers': {'Allow': {'type': 'string'}},
                                'description': 'No Content'
                            }
                        },
                        'operationId': 'Model1AioHttp.options_model1_id'
                    }
                },
                '/model1/': {
                    'post': {
                        'parameters': [{
                            'name': 'body',
                            'schema': {'type': 'array'},
                            'in': 'body'
                        }],
                        'responses': {'200': {'description': 'test'}},
                        'operationId': 'Model1AioHttp.swagger_insert'
                    },
                    'options': {
                        'responses': {
                            '204': {
                                'headers': {'Allow': {'type': 'string'}},
                                'description': 'No Content'}
                            },
                        'operationId': 'Model1AioHttp.options_model1'}
                    }
                }
            }
