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


from swaggerit.api import SwaggerAPI
from swaggerit.request import SwaggerRequest
from aiohttp.web import Application, Response as AioHttpResponse
from aiohttp_swagger import setup_swagger
from urllib.parse import parse_qs
from tempfile import NamedTemporaryFile
import ujson


class AioHttpAPI(SwaggerAPI, Application):

    def __init__(self, models, *, sqlalchemy_bind=None, redis_bind=None,
                 elsearch_bind=None, swagger_json_template=None, title=None,
                 version='1.0.0', authorizer=None, get_swagger_req_auth=True,
                 loop=None, debug=False, swagger_doc_url='doc'):
        Application.__init__(self, loop=loop, debug=debug)
        SwaggerAPI.__init__(
            self, models, sqlalchemy_bind,
            redis_bind, elsearch_bind,
            swagger_json_template, title,
            version, authorizer,
            get_swagger_req_auth, swagger_doc_url
        )

    def _set_handler_decorator(self, method):
        method = self._method_decorator(method)

        async def _method_wrapper(req):
            req = self._cast_request(req)
            resp = await method(req)
            return self._cast_response(resp)
        return _method_wrapper

    def _set_route(self, path, method, handler):
        self.router.add_route(method.upper(), path, handler)
        self.router.add_route(method.upper(), path + '/', handler)

    def _cast_request(self, req):
        query = {k: ','.join(v) for k, v in parse_qs(req.rel_url.query_string).items()}
        headers = {k.decode().lower(): v.decode() for k, v in req.raw_headers}
        body = req.content if req.has_body else None
        return SwaggerRequest(
            req.path, req.method.lower(),
            path_params=dict(req.match_info),
            query=query, headers=headers,
            body=body)

    def _cast_response(self, resp):
        if isinstance(resp, AioHttpResponse):
            return resp

        body = None if resp.body is None else resp.body.encode()
        return AioHttpResponse(body=body, status=resp.status_code,
                        headers=resp.headers)

    def _set_swagger_doc(self, swagger_doc_url):
        setup_swagger(self,
            swagger_url=swagger_doc_url,
            swagger_info=self.swagger_json,
            swagger_def_decor=self._swagger_doc_decorator,
            swagger_home_decor=self._swagger_doc_decorator)

    def _swagger_doc_decorator(self, func):
        async def decorator(req):
            swaggerit_req = self._cast_request(req)
            session = self._build_session()
            response = await self._authorize(swaggerit_req, session)
            if response is not None:
                return self._cast_response(response)

            return await func(req)

        return decorator

    def __getitem__(self, k):
        if k == 'SWAGGER_DEF_CONTENT':
            return ujson.dumps(self.swagger_json, escape_forward_slashes=True)
