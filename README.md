[![Build Status](https://travis-ci.org/dutradda/swaggerit.svg?branch=master)](https://travis-ci.org/dutradda/swaggerit)
[![Coverage Status](https://coveralls.io/repos/github/dutradda/swaggerit/badge.svg?branch=master)](https://coveralls.io/github/dutradda/swaggerit?branch=master)

# swaggerit
Create a swagger API from a set of classes


### Main features:

* Request validation and casting types according to the specification.
* ORM with sqlalchemy basic operations insert/update/delete/get/get_many/get_all.
* sqlalchemy/redis integration, keeping the database in memory updated, the ACID is guaranteed by relational database. The swaggerit does all the synchronization.
* ORM only with redis basic operations insert/update/delete/get/get_many/get_all.
* Asynchronous jobs submissions, than you can do a get request to know the status/result of it.
