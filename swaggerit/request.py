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


from collections import namedtuple


_SwaggerRequest = namedtuple('SwaggerRequest', [
    'url', 'method', 'path_params', 'query',
     'headers', 'body', 'body_schema', 'context'
])


class SwaggerRequest(_SwaggerRequest):

    def __new__(cls, url, method, *, path_params=None, query=None,
                headers=None, body=None, body_schema=None, context=None):
        return _SwaggerRequest.__new__(
            cls, url, method,
            path_params={} if path_params is None else path_params,
            query={} if query is None else query,
            headers={} if headers is None else headers,
            body=body,
            body_schema=body_schema,
            context=context
        )
