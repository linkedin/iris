REST API
========

.. _hmac-auth-label:

HMAC Auth
---------

API requests which require API key auth will have an extra
:code:`AUTHORIZATION` HTTP header. It looks like this:

.. code-block:: none

  AUTHORIZATION: hmac $application:$payload

:code:`$payload` is a base64 encoded hmac sha512 digest of the following string
with the app's API key. In the resulting base64 string, instances of :code:`+`
are replaced with :code:`-` and :code:`/` are replaced with :code:`_`.

.. code-block:: none

  HMAC($api_key, "$window $httpMethod $path $body")

:code:`$window` is the current unix timestamp in seconds, divided by 5, floor'd.

:code:`$httpMethod` is generally :code:`POST`

:code:`$path` is the path portion of the URL, such as :code:`/v0/incidents`

:code:`$body` is generally the json-formatted post body.

Example client implementations:

* `Python <https://github.com/houqp/iris-python-client>`_
* `NodeJS <https://github.com/kripplek/node-iris>`_


Query Filters
-------------
Iris has a number of search endpoints allowing filtering based on data
attributes. For each allowable attribute, filters are defined via the
query string, with syntax in the form of
:code:`$ATTRIBUTE__$OPERATOR=$ARGUMENT` e.g. :code:`created__ge=123`.
The following operators are allowed:

  - "eq": :code:`$ATTRIBUTE == $ARGUMENT`
  - "in": :code:`$ATTRIBUTE` is contained in :code:`$ARGUMENT`, which must be a list
  - "ne": :code:`$ATTRIBUTE != $ARGUMENT`
  - "gt": :code:`$ATTRIBUTE > $ARGUMENT`
  - "ge": :code:`$ATTRIBUTE >= $ARGUMENT`
  - "lt": :code:`$ATTRIBUTE < $ARGUMENT`
  - "le": :code:`$ATTRIBUTE <= $ARGUMENT`
  - "contains": :code:`$ATTRIBUTE` contains the substring :code:`$ARGUMENT`. Only defined on string-like attributes
  - "startswith": :code:`$ATTRIBUTE` starts with :code:`$ARGUMENT`. Only defined on string-like attributes
  - "endswith": :code:`$ATTRIBUTE` ends with :code:`$ARGUMENT`. Only defined on string-like attributes

If no operator is defined (e.g. :code:`id=123`), the operator
is assumed to be "eq" (equality).


Routes
------

.. autofalcon:: iris.doc_helper:app
