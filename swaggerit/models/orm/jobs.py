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


from swaggerit.models.orm._jobs_meta import (
    _create_job, _job_watcher, _set_job, _build_jobs_key,
    _build_last_job_key, _get_job, _get_all_jobs, _copy_session
)
from swaggerit.models.swaggerit import SwaggerItModel
from types import MethodType


class JobsModel(SwaggerItModel):

    def __init__(self):
        SwaggerItModel.__init__(self)

    def _create_job(cls, func, jobs_id, req, session, *arg, **kwargs):
        return _create_job(cls, func, jobs_id, req, session, *arg, **kwargs)

    def _job_watcher(cls, jobs_id, job_hash, job, session):
        return _job_watcher(cls, jobs_id, job_hash, job, session)

    async def _set_job(cls, jobs_id, job_hash, job_obj, session):
        return await _set_job(cls, jobs_id, job_hash, job_obj, session)

    def _build_jobs_key(cls, jobs_id):
        return _build_jobs_key(cls, jobs_id)

    def _build_last_job_key(cls, jobs_id):
        return _build_last_job_key(cls, jobs_id)

    async def _get_job(cls, jobs_id, req, session):
        return await _get_job(cls, jobs_id, req, session)

    async def _get_all_jobs(cls, jobs_id, req, session):
        return await _get_all_jobs(cls, jobs_id, req, session)

    def _copy_session(cls, session):
        return _copy_session(cls, session)
