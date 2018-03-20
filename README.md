# Swagger It &middot; [![Build Status](https://travis-ci.org/dutradda/swaggerit.svg?branch=master)](https://travis-ci.org/dutradda/swaggerit) [![Coverage Status](https://coveralls.io/repos/github/dutradda/swaggerit/badge.svg?branch=master)](https://coveralls.io/github/dutradda/swaggerit?branch=master) [![PyPi Last Version](https://img.shields.io/pypi/v/swaggerit.svg)](https://pypi.python.org/pypi/swaggerit) [![PyPi Develop Status](https://img.shields.io/pypi/status/swaggerit.svg)](https://pypi.python.org/pypi/swaggerit) [![Python Versions](https://img.shields.io/pypi/pyversions/swaggerit.svg)](https://pypi.python.org/pypi/swaggerit) [![License](https://img.shields.io/pypi/l/swaggerit.svg)](https://github.com/dutradda/swaggerit/blob/master/LICENSE)


Create a swagger API from a set of classes.


### Main features:

* Request validation and casting types according to the specification.
* ORM with sqlalchemy basic operations insert/update/delete/get/get_many/get_all.
* sqlalchemy/redis integration, keeping the database in memory updated, the ACID is guaranteed by relational database. The swaggerit does all the synchronization.
* ORM only with redis basic operations insert/update/delete/get/get_many/get_all.
* Asynchronous jobs submissions, than you can do a get request to know the status/result of it.


### Example of ORM sqlalchemy/redis integration:
```python
from swaggerit import FactoryOrmModels, AioHttpAPI
from aiohttp import web
import sqlalchemy as sa
import aioredis
import uvloop
import asyncio
import argparse


parser = argparse.ArgumentParser(description="swaggerit example 2 - Sqlalchemy Redis")
parser.add_argument('--port', '-p', type=int, default=10000)


ModelSQLAlchemyRedisBase = FactoryOrmModels.make_sqlalchemy_redis_base()


class Products(ModelSQLAlchemyRedisBase):
    __tablename__ = 'products'
    __swagger_json__ = {
        'paths': {
            '/products': {
                'post': {
                    'parameters': [{
                        'name': 'products_data',
                        'in': 'body',
                        'required': True,
                        'schema': {
                            'type': 'object',
                            'required': ['name', 'brand'],
                            'properties': {
                                'name': {'type': 'string'},
                                'brand': {'type': 'string'}
                            }
                        }
                    }],
                    'operationId': 'swagger_insert',
                    'responses': {'201': {'description': 'Created'}}
                },
                'get': {
                    'operationId': 'swagger_get_all',
                    'responses': {'200': {'description': 'Got All'}}
                }
            },
            '/products/{id}': {
                'parameters': [{
                    'name': 'id',
                    'in': 'path',
                    'required': True,
                    'type': 'integer'
                }],
                'get' : {
                    'operationId': 'swagger_get',
                    'responses': {'200': {'description': 'Got One'}}
                }
            }
        }
    }

    id = sa.Column(sa.Integer(), primary_key=True, autoincrement=True)
    name = sa.Column(sa.String(255), nullable=False, unique=True)
    brand = sa.Column(sa.String(255), nullable=False)


if __name__ == '__main__':
    sqlalchemy_bind = sa.create_engine('sqlite:///')
    loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)
    redis_bind = loop.run_until_complete(aioredis.create_redis(('redis', 6379), loop=loop))

    app = AioHttpAPI(
        [Products], title='Store API',
        sqlalchemy_bind=sqlalchemy_bind,
        redis_bind=redis_bind,
        loop=loop
    )
    Products.metadata.bind = sqlalchemy_bind
    Products.metadata.create_all()

    args = parser.parse_args()
    web.run_app(app, port=args.port)

```

#### Running:
```
$ python3.6 swaggerit_example.py
======== Running on http://0.0.0.0:10000 ========
(Press CTRL+C to quit)
```

#### Using:
```
$ curl -i localhost:10000/products -XPOST -H 'Content-Type: application/json' -d '{"name": "t-shirt", "brand": "open source"}'
HTTP/1.1 201 Created
Content-Type: application/json
Content-Length: 49
Server: Python/3.6 aiohttp/1.2.0

[{"id":1,"name":"t-shirt","brand":"open source"}]
```

When inserts, updates or deletes operations are made, the swaggerit updates all the related database registers in redis (if the model enables redis integration).

```
$ curl -i localhost:10000/products
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 49
Server: Python/3.6 aiohttp/1.2.0

[{"id":1,"name":"t-shirt","brand":"open source"}]
```
