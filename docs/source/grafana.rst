Grafana Integration
========================

Iris can easily be integrated into an existing Grafana implementation.

==================
Iris Configuration
==================

Enable the builtin Grafana webhook in Iris' configuration.

Configuration::

    webhooks:
      - grafana

Then create an application using the UI. In this example let's use the name 'grafana'.
Once you've created the application you'll be able to retrieve the application's key.
Here we'll use "abc".

==========================
Grafana Configuration
==========================

In Grafana, you can configure Iris as a notifcation channel, using the application, it's key
and the target plan as parameters in the webhook url.

Configuration::

    Name: iris-team1
    Type: webhook
    Url: http://iris:16649/v0/webhooks/grafana?application=grafana&key=abc&plan=team1
    Http Method: POST

Then simply add this notification channel to your alert in Grafana.
