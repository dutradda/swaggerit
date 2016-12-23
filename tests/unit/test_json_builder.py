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


from swaggerit.json_builder import JsonBuilder


class TestJsonBuilder(object):

    def test_build_boolean(self):
        assert JsonBuilder.build('true', {'type': 'boolean'}) == True

    def test_build_integer(self):
        assert JsonBuilder.build('1', {'type': 'integer'}) == 1

    def test_build_number(self):
        assert JsonBuilder.build('1.1', {'type': 'number'}) == 1.1

    def test_build_string(self):
        assert JsonBuilder.build('test', {'type': 'string'}) == 'test'

    def test_build_array(self):
        assert JsonBuilder.build('1,2,3', {'type': 'array', 'items': {'type': 'integer'}}) == [1,2,3]

    def test_build_object(self):
        schema = {
            'type': 'object',
            'properties': {
                'test': {'type': 'string'}
            }
        }
        assert JsonBuilder.build('test:test', schema) == {'test': 'test'}
