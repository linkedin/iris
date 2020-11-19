Configuration
=============

Oncall integration
------------------
Iris communicates with Oncall primarily through its role_lookup plugins, which allow it to 
determine a message recipient given a role:target pair. To use Oncall with Iris:

#. Configure Iris to communicate with Oncall by setting the "oncall-api" key in the config to
   the URL where Oncall is hosted

#. In the "role_lookups" key, include "oncall" in the list and remove "dummy"

#. Import targets from Oncall by running the following command:

.. code-block:: bash

    ./iris-sync-targets /home/iris/config/config.yaml

Slack integration
-----------------

Adding Slack bot
````````````````

Iris can send Slack messages by integrating with a Slack bot.

#. Create a Slack App

   #. Go to https://api.slack.com/apps.
   #. Click "Create New App" button on the upper right.
   #. Provide an App Name (example - iris)
   #. Choose your Slack team
   #. Click "Create App"

#. Go to "Bot Users" under "Features" and do the following:

   #. Click "Add a Bot User"
   #. Choose a default username for the bot (example - iris)
   #. Click "Add Bot User"
   #. Click "Save Changes"

#. To enable Interactive Message, click "Interactive Messages" under "Features" and do the following:

   #. Click "Enable Interactive Messages"
   #. Add a HTTPS endpoint: "https://YOUR_PUBLIC_IRIS_RELAY_URL/api/v0/slack/messages/relay"
   #. Click "Enable Interactive Messages" button

#. Click "OAuth & Permissions" under "Features" and do the folling:

   #. Under Permission Scopes, add the following:

      - incoming-webhook
      - commands
      - bot
      - channels:read
      - chat:write:bot

   #. Click "Save Changes"

   #. Under "OAuth Tokens & Redirect URLs" section:

      #. Click "Install App to Team"
      #. Redirected to a confirmation page that has all the details about the bot
      #. Choose "Slackbot" in the Post to dropdown
      #. Click "Authorize"


After completing the above steps, you should be able to find the following two secrets:

Bot User OAuth Token
  Found under "Features" -> "OAuth & Permissions" -> "OAuth Tokens & Redirect Urls" -> "Bot User OAuth Access Token"

Verification Token
  Found under "Settings" -> "Basic Information" -> "App Credentials"


Updating Iris configs
`````````````````````

The last step is to create the slack config section with those secrets for Iris and Iris relay.

In Iris config, add the following section under venders block with **Bot User OAuth Token**:

.. code-block:: yaml

    vendors:
    - type: iris_slack
      name: slack
      auth_token: BOT_USER_OAUTH_TOKEN
      base_url: 'https://slack.com/api/chat.postMessage'
      # this url config is for constructing url link for the message title
      iris_incident_url: 'https://YOUR_IRIS_URL/incidents'
      # we also support an optional proxy key here
      message_attachments:
        fallback: 'New Iris notification!'

In Iris relay config, add the following top level section with **Verification Token**:

.. code-block:: yaml

    slack:
      auth_token: VERIFICATION_TOKEN



Known issues
````````````

For message button integration, your relay should be getting POST request from
Slack every time a button is clicked. If your relay is getting GET instead of
POST, then you are running into a known bug in Slack. You will need to reset
the relay webhook state by doing the following:

#. Go to "Interactive Messages" under "Features"
#. Set HTTPS endpont to a URL under another domain. For example, you can use https://www.google.comw
#. Click "Save changes" button
#. Set HTTPS endpoint back to your relay: "https://YOUR_PUBLIC_IRIS_RELAY_URL/api/v0/slack/messages/relay"
#. Click "Save changes" button again
