# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

# -*- coding:utf-8 -*-

from .. import utils
import logging
logger = logging.getLogger(__name__)

_registered_plugins = []
_plugins = None


def parse_response(msg):
    args = msg.split(' ')
    cmd = args.pop(0).lower()
    return cmd, args


class IrisPlugin(object):
    name = 'IrisDefault'
    phone_response_menu = {
        '2': {
            'title': 'Press 2 to claim.',
            'cmd': 'claim',
        },
    }

    def __init__(self, config):
        self.config = config

    @classmethod
    def get_phone_menu_text(cls):
        if cls.phone_response_menu:
            return ' '.join([item['title'] for (_, item) in
                            cls.phone_response_menu.items()])
        else:
            return ''

    def handle_response(self, mode, msg_id, source, content, batch=False):
        if mode == 'call':
            digits = content
            logger.info('%s Plugin got phone call response for message(%s): %s:',
                        self.name, msg_id, digits)
            if digits not in self.phone_response_menu:
                msg = 'Got unknown option from user: ' + digits
                logger.warning(msg)
                return msg
            cmd, args = self.phone_response_menu[digits]['cmd'], None
        else:
            logger.info('%s Plugin got %s response for message(%s): %s',
                        self.name, mode, msg_id, content)
            cmd, args = parse_response(content)
        if batch:
            cmd = 'batch_' + cmd
        return self.process_command(msg_id, source, mode, cmd, args)

    def process_iris_claim(self, msg_id, source, mode, cmd, args=None):
        iid = utils.get_incident_id_from_message_id(msg_id)
        if not iid:
            return 'Failed to match incident for message(%s).' % msg_id
        owner = utils.lookup_username_from_contact(mode, source)
        if not owner:
            return 'Failed to identify owner for the incident.'
        is_active, previous_owner = utils.claim_incident(iid, owner)
        if is_active:
            logger.info(('Failed to claim incident(%s) for message: %s. '
                         'owner: %s, mode: %s, args: %s'),
                        iid, msg_id, owner, mode, args)
            return 'Failed to claim incident for message: %s.' % str(msg_id)
        else:
            if previous_owner:
                return 'Iris incident(%s) claimed, previously claimed by %s.' % (iid, previous_owner)
            else:
                return 'Iris incident(%s) claimed.' % iid

    def process_iris_batch_claim(self, msg_id, source, mode, cmd, args=None):
        owner = utils.lookup_username_from_contact(mode, source)
        if not owner:
            return 'Failed to identify owner for the incident.'
        utils.claim_incidents_from_batch_id(msg_id, owner)
        return 'All iris incidents claimed for batch id %s.' % msg_id

    def process_claim_all(self, msg_ids, source, mode):
        owner = utils.lookup_username_from_contact(mode, source)
        if not owner:
            return 'Failed to identify owner for these incidents.'
        if not msg_ids:
            return 'No messages to claim.'
        incident_ids = utils.get_incident_ids_from_message_ids(msg_ids)
        if not incident_ids:
            return 'No messages to claim.'

        claimed, not_claimed = utils.claim_bulk_incidents(incident_ids, owner)

        msg = []
        if claimed:
            msg.append('Iris Incidents claimed (%s): %s' % (len(claimed), ', '.join(map(str, claimed))))
        if not_claimed:
            msg.append('Iris Incidents failed to claim (%s): %s' % (len(not_claimed), ', '.join(map(str, not_claimed))))

        if msg:
            return '\n'.join(msg)
        else:
            return 'Unknown claim all result'

    def process_command(self, msg_id, source, mode, cmd, args=None):
        if cmd == 'claim':
            return self.process_iris_claim(msg_id, source, mode, cmd, args)
        elif cmd == 'batch_claim':
            return self.process_iris_batch_claim(msg_id, source, mode, cmd, args)
        elif cmd == 'claim_all':
            return self.process_claim_all(msg_id, source, mode)
        else:
            return 'Unknown command.'


def init_plugins(config):
    global _plugins
    if not _plugins:
        _plugins = {}
        for plugin in _registered_plugins:
            name = plugin.name
            try:
                _plugins[name] = plugin(config.get(name, {}))
            except Exception:
                logger.exception('failed to register plugin: %s', name)
            else:
                logger.info('registered plugin: %s', name)
        _plugins[IrisPlugin.name] = IrisPlugin({})
    return _plugins


def register_plugin():
    def wrapper(plugin):
        if not issubclass(plugin, IrisPlugin):
            raise ValueError('%s is not a subclass of %s' %
                             (type(plugin), type(IrisPlugin)))
        _registered_plugins.append(plugin)
        return plugin
    return wrapper


def find_plugin(plugin_name, include_deafault=True):
    plugin = _plugins.get(plugin_name)
    if plugin:
        return plugin
    elif include_deafault:
        return _plugins[IrisPlugin.name]


# core.py itself is excluded from __init__.py
from . import *  # noqa
