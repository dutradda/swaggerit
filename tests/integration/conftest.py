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


from swaggerit.aiohttp_api import AioHttpAPI
from swaggerit.models.orm.session import Session
from swaggerit.models.orm.binds import ElSearchBind
from tests.integration.fixtures import ModelSQLAlchemyRedisBase
from sqlalchemy import create_engine
from aioredis import create_redis
from time import sleep
import pytest
import pymysql
import uvloop
import asyncio


@pytest.fixture(scope='session')
def loop():
    loop = uvloop.new_event_loop()
    # loop = asyncio.new_event_loop() # just for debugging
    asyncio.set_event_loop(loop)
    return loop


@pytest.fixture(scope='session')
def redis(variables, loop):
    coro = create_redis(
        (variables['redis']['host'], variables['redis']['port']),
        db=variables['redis']['db'],
        loop=loop
    )
    return loop.run_until_complete(coro)


@pytest.fixture()
def elsearch(variables, loop):
    es = ElSearchBind(**variables['elsearch'])
    loop.run_until_complete(es.create_index())
    loop.run_until_complete(es.flush_index())
    return es


@pytest.fixture(scope='session')
def pymysql_conn(variables):
    database = variables['database'].pop('database')
    conn = pymysql.connect(**variables['database'])

    with conn.cursor() as cursor:
        try:
            cursor.execute('drop database {};'.format(database))
        except:
            pass
        cursor.execute('create database {};'.format(database))
        cursor.execute('use {};'.format(database))
    conn.commit()
    variables['database']['database'] = database

    return conn


@pytest.fixture(scope='session')
def engine(variables, pymysql_conn):
    if variables['database']['password']:
        url = 'mysql+pymysql://{user}:{password}'\
            '@{host}:{port}/{database}'.format(**variables['database'])
    else:
        variables['database'].pop('password')
        url = 'mysql+pymysql://{user}'\
            '@{host}:{port}/{database}'.format(**variables['database'])
        variables['database']['password'] = None

    return create_engine(url)


@pytest.fixture
def session(variables, redis, elsearch, engine, pymysql_conn, loop):
    ModelSQLAlchemyRedisBase.metadata.bind = engine
    ModelSQLAlchemyRedisBase.metadata.create_all()

    with pymysql_conn.cursor() as cursor:
        cursor.execute('SET FOREIGN_KEY_CHECKS = 0;')
        for table in ModelSQLAlchemyRedisBase.metadata.tables.values():
            cursor.execute('delete from {};'.format(table))

            try:
                cursor.execute('alter table {} auto_increment=1;'.format(table))
            except:
                pass
        cursor.execute('SET FOREIGN_KEY_CHECKS = 1;')
    pymysql_conn.commit()
    loop.run_until_complete(redis.flushdb())
    session = Session(bind=engine, redis_bind=redis, loop=loop, elsearch_bind=elsearch)
    yield session
    session.close()


@pytest.fixture
def models():
    return []


@pytest.fixture
def api(engine, redis, models, loop):
    models_ = [model for model in models if hasattr(model, '__api__')]
    return AioHttpAPI(models_, sqlalchemy_bind=engine,
                      redis_bind=redis, title='Test API', loop=loop)


@pytest.fixture
def client(api, test_client):
    return test_client(api)
