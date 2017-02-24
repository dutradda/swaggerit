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


long_description =\
'''Create a swagger API from a set of classes.

Main features:

- Request validation and casting types according to the specification.
- ORM with sqlalchemy basic operations insert/update/delete/get/get_many/get_all.
- sqlalchemy/redis integration, keeping the database in memory updated, the ACID is guaranteed by relational database. The swaggerit does all the synchronization.
- ORM only with redis basic operations insert/update/delete/get/get_many/get_all.
- Asynchronous jobs submissions, than you can do a get request to know the status/result of it.

https://github.com/dutradda/swaggerit
'''


install_requires = []
with open('requirements.txt') as requirements:
    install_requires = requirements.readlines()

    aioes_url = install_requires.pop()
    aioes_url = aioes_url.strip('\n')
    aioes_url += '#egg=aioes-ext-0.6.2b'

    aiohttp_swagger_url = install_requires.pop()
    aiohttp_swagger_url = aiohttp_swagger_url.strip('\n')
    aiohttp_swagger_url += '#egg=aiohttp-swagger-ext-1.1.0b'

    install_requires.append('aioes-ext')
    install_requires.append('aiohttp-swagger-ext')


tests_require = []
with open('requirements-dev.txt') as requirements_dev:
    tests_require = requirements_dev.readlines()


setup(
    name='swaggerit',
    packages=find_packages('.'),
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
    setup_requires=[
        'pytest-runner==2.9',
        'setuptools==28.3.0'
    ],
    tests_require=tests_require,
    install_requires=install_requires,
    dependency_links=[aioes_url, aiohttp_swagger_url],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
        'Topic :: Database :: Front-Ends',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
