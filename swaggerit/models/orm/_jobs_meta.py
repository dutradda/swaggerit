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


from swaggerit.models._swaggerit_meta import _ModelSwaggerItMeta
from swaggerit.models._base import _ModelBaseMeta
from swaggerit.utils import set_method
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from collections import defaultdict
from datetime import datetime
import random
import asyncio


class _ModelJobsMeta(_ModelSwaggerItMeta):

    def __init__(cls, name, bases_classes, attributes):
        _ModelSwaggerItMeta.__init__(cls, name, bases_classes, attributes)
        _init(cls)


def _init(obj):
    set_method(obj, _create_job)
    set_method(obj, _job_watcher)
    set_method(obj, _set_job)
    set_method(obj, _build_jobs_key)
    set_method(obj, _build_last_job_key)
    set_method(obj, _get_job)
    set_method(obj, _get_all_jobs)
    set_method(obj, _copy_session)

def _create_job(obj, func, jobs_id, req, session, *arg, **kwargs):
    job_hash = '{:x}'.format(random.getrandbits(128))
    job = partial(func, req, session, *arg, **kwargs)
    session.loop.run_in_executor(None, obj._job_watcher, jobs_id, job_hash, job, session)
    return obj._build_response(201, body=obj._pack_obj({'job_hash': job_hash}))

def _job_watcher(obj, jobs_id, job_hash, job, session):
    asyncio.run_coroutine_threadsafe(
        obj._set_job(jobs_id, job_hash, {'status': 'running'}, session),
        session.loop
    ).result()
    start_time = datetime.now()

    try:
        if asyncio.iscoroutinefunction(job.func):
            result = asyncio.run_coroutine_threadsafe(job(), session.loop).result()
        else:
            executor = ThreadPoolExecutor(1)
            job = executor.submit(job)
            result = job.result()
            executor.shutdown()

    except Exception as error:
        result = {'name': error.__class__.__name__, 'message': str(error)}
        status = 'error'
        obj._logger.exception('From job {}:{}'.format(jobs_id, job_hash))

    else:
        status = 'done'

    end_time = datetime.now()
    time_info = {
        'start': str(start_time)[:-3],
        'end': str(end_time)[:-3],
        'elapsed': str(end_time - start_time)[:-3]
    }
    job_obj = {'status': status, 'result': result, 'time_info': time_info}

    asyncio.run_coroutine_threadsafe(
        obj._set_job(jobs_id, job_hash, job_obj, session),
        session.loop
    ).result()
    session.bind.close()
    session.close()

async def _set_job(obj, jobs_id, job_hash, job_obj, session):
    key = obj._build_jobs_key(jobs_id)
    last_job_key = obj._build_last_job_key(jobs_id)
    job_obj = obj._pack_obj(job_obj)

    await session.redis_bind.hset(key, job_hash, job_obj)
    if await session.redis_bind.ttl(key) < 0:
        await session.redis_bind.expire(key, 7*24*60*60)
    await session.redis_bind.set(last_job_key, job_obj)

def _build_jobs_key(obj, jobs_id):
    return jobs_id + '_jobs'

def _build_last_job_key(obj, jobs_id):
    return jobs_id + '_last'

async def _get_job(obj, jobs_id, req, session):
    job_hash = req.query.get('job_hash')

    if job_hash is None:
        job_obj = await obj._get_all_jobs(jobs_id, req, session)

    elif job_hash == 'last':
        job_obj = await session.redis_bind.get(obj._build_last_job_key(jobs_id))

    else:
        job_obj = await session.redis_bind.hget(obj._build_jobs_key(jobs_id), job_hash)

    if job_obj is None:
        return obj._build_response(404)
    else:
        return obj._build_response(200, body=job_obj.decode())

async def _get_all_jobs(obj, jobs_id, req, session):
    jobs = await session.redis_bind.hgetall(obj._build_jobs_key(jobs_id))

    if not jobs:
        return None

    else:
        all_jobs = defaultdict(dict)

        for job_id, job in jobs.items():
            job = obj._unpack_obj(job)
            all_jobs[job.pop('status')][job_id] = job

        return obj._pack_obj(all_jobs).encode()

def _copy_session(obj, session):
    return type(session)(bind=session.bind.engine.connect(),
                         redis_bind=session.redis_bind,
                         elsearch_bind=session.elsearch_bind,
                         loop=session.loop)
