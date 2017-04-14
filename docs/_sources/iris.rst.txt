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
