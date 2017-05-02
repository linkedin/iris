Iris
========

.. _api-ref:

Iris serves as the API backend and web UI for all business logic. All other
iris components talk to its api endpoints. It is intended to not be reachable
outside your internal network.

Overview
--------

As can be seen, Iris is the crux of the entire framework:

.. code-block:: none

                                       +------------+
                           +-----------+ iris relay |
                           |           +------------+
                           v
                     +-----+----+
    +-------+        |          |
    | MySQL |-<------+   iris   |
    +-------+        |          |
        ^            +-----+----+
        |                  ^
        |                  |
        |           +------+------+
        +-----------| iris sender |
                    +-------------+


Security
--------

Since Iris will be integrated with internal infrastructure, please do not expose
Iris web and API to the public internet.

Please also make sure **only trusted** users are given access to create and
update templates since those templates will be rendered using Jinja. Jinja's
sandbox can be abused to evaluate arbitrary untrusted Python code.
