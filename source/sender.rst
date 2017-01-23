Iris sender
===========

Iris sender is the daemon that regularly polls the database for new incidents
and sends messages accordingly. It is packaged with :ref:`API <api-ref>`.


Sender tasks workflow
---------------------

.. code-block:: none

          +------------+
          |            |
          | escalation | creates new message rows
          |    task    +----------+
          |            |          |
          +------------+          |
                                  |
                           +------v----+
                           |           |
                           |   MySQL   <--------------+
                           |           |              |
            +--------+     +----+------+              |
            |        |          |                     |
            |  poll  |          |                     |
            |  task  <----------+                     |
            |        | fetches all unsent messages    |
            +---+----+ (excluding batched ones)       |
                |                                     |
       populates context                              |
      and passes into queue +---------------+         |
                |           |               |         |
                +-----------> message_queue |         |
                            |               |         |
                            +-------+-------+         |
                                    |                 |
            +-----------+           |                 |
            |           |           |                 |
            | send task <-----------+                 |
            |     &     |                             |
            | aggregate |                             |
            |   task    |                             |
            |           |                             |
            +----+------+                             |
                 |           +------------+           |
     aggregates  |           |            |           |
     and passes  +-----------> send_queue |           |
     into queue              |            |           |
                             +-----+------+           |
                                   |                  |
              +--------+           |                  |
           +--|        |           |                  |
        +--|  | worker <-----------+                  |
        |  |  | tasks  |                              |
        |  |  |        |                              |
        |  |  +--------+                              |
        |  +---------+  send messages                 |
        +----------+    and mark them as sent in database
