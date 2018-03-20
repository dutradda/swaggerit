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


from version import VERSION
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys


long_description = '''
Create a swagger API from a set of classes.

Main features:

- Request validation and casting types according to the specification.
- ORM with sqlalchemy basic operations insert/update/delete/get/get_many/get_all.
- sqlalchemy/redis integration, keeping the database in memory updated, the ACID is guaranteed by
    relational database. The swaggerit does all the synchronization.
- ORM only with redis basic operations insert/update/delete/get/get_many/get_all.
- Asynchronous jobs submissions, than you can do a get request to know the status/result of it.

https://github.com/dutradda/swaggerit
'''

install_requires = [
    'SQLAlchemy==1.*',
    'jsonschema==2.*',
    'ujson==1.*',
    'hiredis==0.2.*',
    'aioredis==0.2.*',
    'aiohttp==1.*',
    'uvloop==0.7.*',
    'aiohttp-swagger==1.*',
    'aioes==0.7.*'
]

tests_require = [
    'PyMySQL',
    'pytest',
    'pytest-variables[hjson]',
    'pytest-cov',
    'pytest-aiohttp==0.1.*'
]

setup_requires = [
    'pytest-runner',
    'flake8'
]


class PyTest(TestCommand):

    user_options = [
        ('cov-html=', None, 'Generate html report'),
        ('vars=', None, 'Pytest external variables file'),
        ('filter=', None, "Pytest setence to filter (see pytest '-k' option)")
    ]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ['--cov', 'swaggerit', '-xvv']
        self.cov_html = False
        self.filter = False
        self.vars = 'pytest-vars.json'

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.pytest_args.extend(['--variables', self.vars])

        if self.cov_html:
            self.pytest_args.extend(['--cov-report', 'html'])
        else:
            self.pytest_args.extend(['--cov-report', 'term-missing'])

        if self.filter:
            self.pytest_args.extend(['-k', self.filter])

        self.pytest_args.extend(['tests'])

    def run_tests(self):
        import pytest

        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name='swaggerit',
    packages=find_packages(),
    include_package_data=True,
    version=VERSION,
    description='A Framework featuring Swagger, SQLAlchemy and Redis',
    long_description=long_description,
    author='Diogo Dutra',
    author_email='dutradda@gmail.com',
    url='https://github.com/dutradda/swaggerit',
    download_url='http://github.com/dutradda/swaggerit/archive/master.zip',
    license='MIT',
    keywords='framework swagger openapi sqlalchemy redis crud',
    install_requires=install_requires,
    tests_require=tests_require,
    setup_requires=setup_requires,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
        'Topic :: Database :: Front-Ends',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    cmdclass={'test': PyTest},
    test_suite='tests',
)
