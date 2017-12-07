Alertmanager Integration
========================

Iris can easily be integrated into an existing (Prometheus) Alertmanager implementation.

==================
Iris Configuration
==================

Enable the builtin Alertmanager webhook in Iris' configuration.

Configuration::

    webhooks:
      - alertmanager

Then create an application using the UI. In this example let's use the name 'alertmanager'.
Once you've created the application you'll be able to retrieve the application's key.
Here we'll use "abc".

==========================
Alertmanager Configuration
==========================

In alertmanager, you can configure Iris as a receiver, using the application and it's key
as parameters.

Configuration::

    receivers:
    - name: 'iris-team1'
      webhook_configs:
        - url: http://iris:16649/v0/webhooks/alertmanager?application=alertmanager&key=abc

Then create a rule which includes the label "iris_plan". This label will point to a plan
you created in Iris.

Alert Rule::

   ALERT some_metric_high
     IF some_metric > 2
     FOR 1m
     LABELS { iris_plan = "teamA" }
     ANNOTATIONS {
       summary = "Oh my, a problem {{ $labels.instance }}",
       description = "{{ $labels.instance }} - {{ $labels.job }} :: Dear oh dear. {{ $value }}",
     }
