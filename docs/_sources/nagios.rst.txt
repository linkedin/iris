Nagios Integration
==================

Iris can easily be integrated into an existing Nagios implementation.


====================
Iris Configuration
====================

To support communication from Nagios, an Iris application plugin needs to
be created. The example plugin defines a basic application named Nagios
to handle requests. This plugin can be extended further to handle sending
acknowledgements back to Nagios.

Example Nagios Plugin
---------------------

Code::

    from __future__ import absolute_import
    import logging

    from iris.plugins.core import register_plugin, IrisPlugin


    logger = logging.getLogger(__name__)


    @register_plugin()
    class Nagios(IrisPlugin):
        name = 'Nagios'
        phone_response_menu = {
            '2': {
                'title': 'Press 2 to claim.',
                'cmd': 'claim',
            },
        }

        def process_command(self, msg_id, source, mode, cmd, args=None):
            if cmd == 'claim':
                return self.process_iris_claim(msg_id, source, mode, cmd, args)
            elif cmd == 'batch_claim':
                return self.process_iris_batch_claim(msg_id, source, mode, cmd, args)
            elif cmd == 'claim_all':
                return self.process_claim_all(msg_id, source, mode)
            else:
                return 'Unknown command.'

Application Variables
---------------------

Nagios has a concept of "host" and "service" alerts, defined by the type
of check that is being performed. While Iris can receive any type of
notification, carrying the context of "host" and "service" from Nagios
into the Nagios application can be useful when building robust templates.


Suggested Variables::

    hostname
    hostnotes
    hostnotesurl
    hostoutput
    hoststate
    notificationtype
    servicedescription
    servicename
    servicenotes
    servicenotesurl
    serviceoutput
    servicestate



====================
Nagios Configuration
====================

Sending Messages from Nagios
----------------------------
Nagios requires a custom script for sending notifications to Iris. Nagios
supports custom notification logic through the "commands" configuration,
where by default it sends notifications via e-mails. Creating additional
command definitions allows for the separate notification for host and
service checks, where the same or different plan may be applied to both checks.

Command definitions should be setup for both host and service checks, only
to provide context between host-level checks and service-level checks.



Nagios Contact Definition
-------------------------

Iris can be used for some or all notifications by Nagios. Regardless of how
messages are sent, a contact definition will need to be setup in the contacts.cfg
configuration in Nagios.


Example Contact Definition::

    #
    # Iris contact definition
    #

    define contact{
                contact_name                    iris
                alias                           Contact for Iris
                service_notification_period     24x7
                host_notification_period        24x7
                service_notification_options    w,u,c
                host_notification_options       d,u,f
                service_notification_commands   notify-service-by-iris
                host_notification_commands      notify-host-by-iris
            }


Nagios Service Defininition
---------------------------

If the example Nagios application plugin is being used, it will be
required to remove notification intervals (set to 0) so multiple
Iris events are not generated.
