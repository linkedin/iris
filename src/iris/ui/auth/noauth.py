# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.
import hashlib

class Authenticator:
    def __init__(self, config):
        pass

    def authenticate(self, username, password):
        login_passwd = '7880088a75388735ba61042b143f468f'
        hashpass = hashlib.md5(password.encode('utf-8')).hexdigest()
        if username == 'admin' and login_passwd == hashpass:
            return True
        else:
            return False
