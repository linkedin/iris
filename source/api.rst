Iris API
========

.. _api-ref:

Iris API is the backend for all business logic. All other iris components talk
to iris-api. It is intended to not be reachable outside your internal network.

Overview
--------

As can be seen, API is the crux of the entire framework:

.. code-block:: none

                                       +------------+
                           +-----------+ iris relay |
                           |           +------------+
                           v
                     +-----+----+        +---------------+
    +-------+        |          |        |               |
    | MySQL |-<------+ iris api | <------+ iris frontend |
    +-------+        |          |        |               |
        ^            +-----+----+        +---------------+
        |                  ^
        |                  |
        |           +------+------+
        +-----------| iris sender |
                    +-------------+
