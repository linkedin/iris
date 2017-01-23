# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.


class dummy(object):
    def __init__(self, config):
        pass

    def team_members(self, team_name):
        return ['foo']

    def team_manager(self, team_name):
        return ['foo']

    def team_oncall(self, team_name, oncall_type='primary'):
        return ['foo']

    def team_list(self):
        return ['foo']
