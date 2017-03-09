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


from swaggerit.exceptions import SwaggerItModelError
from swaggerit.models.orm._jobs_meta import _ModelJobsMeta
from sqlalchemy.exc import IntegrityError
from functools import partial


class _ModelSwaggerItOrmMeta(_ModelJobsMeta):

    async def _execute_operation(cls, operation, status_code, has_404=True, pack_first=False):
        try:
            objs = await operation()

        except SwaggerItModelError as error:
            error_obj = {
                'message': error.args[0]
            }
            if len(error.args) > 1:
                error_obj['instance'] = error.args[1]
            return cls._build_response(400, body=cls._pack_obj(error_obj))

        except IntegrityError as error:
            error_obj = {
                'params': error.params,
                'database message': {
                    'code': error.orig.args[0],
                    'message': error.orig.args[1]
                }
            }
            if len(error.detail):
                error_obj['details'] = error.detail
            return cls._build_response(400, body=cls._pack_obj(error_obj))

        else:
            if has_404 and not objs:
                return cls._build_response(404)
            else:
                if pack_first:
                    body = cls._pack_obj(objs[0])
                else:
                    body = cls._pack_obj(objs)
                return cls._build_response(status_code, body=body)

    async def swagger_insert(cls, req, session):
        operation = partial(cls.insert, session, req.body, **req.query)
        return await cls._execute_operation(operation, 201, False)

    async def swagger_update(cls, req, session):
        operation = partial(cls.update, session, [req.body], ids=[req.path_params], **req.query)
        return await cls._execute_operation(operation, 200, pack_first=True)

    async def swagger_update_many(cls, req, session):
        operation = partial(cls.update, session, req.body, **req.query)
        return await cls._execute_operation(operation, 200)

    async def swagger_delete(cls, req, session):
        operation = partial(cls.delete, session, ids=[req.path_params], **req.query)
        return await cls._execute_operation(operation, 204, False)

    async def swagger_delete_many(cls, req, session):
        operation = partial(cls.delete, session, ids=req.body, **req.query)
        return await cls._execute_operation(operation, 204, False)

    async def swagger_get(cls, req, session):
        operation = partial(cls.get, session, ids=[req.path_params], **req.query)
        return await cls._execute_operation(operation, 200, pack_first=True)

    async def swagger_get_many(cls, req, session):
        operation = partial(cls.get, session, **req.query)
        return await cls._execute_operation(operation, 200)

    async def swagger_get_all(cls, req, session):
        operation = partial(cls.get, session, **req.query)
        return await cls._execute_operation(operation, 200)

    async def swagger_search(cls, req, session):
        method = getattr(cls, 'search', lambda *args, **kwargs: None)
        operation = partial(method, session, **req.query)
        return await cls._execute_operation(operation, 200)
