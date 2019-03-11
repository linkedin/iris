# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

import hmac
import hashlib
import urllib.parse
import base64

oneclick_email_markup = '''
<script type="application/ld+json">
{
  "@context": "http://schema.org",
    "@type": "EmailMessage",
    "potentialAction": {
      "@type": "ConfirmAction",
      "name": "Claim",
      "handler": {
        "@type": "HttpActionHandler",
        "url": "%(url)s"
      }
    },
    "description": "Claim incident %(incident_id)s"
}
</script>
'''


def generate_oneclick_url(config, data):
    keys = ('msg_id', 'email_address', 'cmd')  # Order here needs to match order in iris-relay
    HMAC = hmac.new(config['gmail_one_click_url_key'].encode('utf-8'),
                    (' '.join(str(data[key]) for key in keys).encode('utf-8')), hashlib.sha512)
    data['token'] = base64.urlsafe_b64encode(HMAC.digest())
    return config['gmail_one_click_url_endpoint'] + '?' + urllib.parse.urlencode(data)
