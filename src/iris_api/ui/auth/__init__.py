# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.


def login_user(req, username):
    session = req.env['beaker.session']
    session['user'] = username
    session.save()


def logout_user(req):
    session = req.env['beaker.session']
    session.pop('user', None)
    session.delete()
