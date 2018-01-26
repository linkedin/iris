Installation
============


Getting started with Docker
---------------------------

.. _repository: https://github.com/jrgp/iris-docker-compose

We have built a docker compose setup for you to spin up Iris cluster in one
command. Please clone the docker compose repository_ and follow the readme
there.

User management
---------------

.. _iris-admin: https://github.com/jrgp/iris-admin

At LinkedIn, user management is done in an Active Directory server external
to the Iris/Oncall system. We use the ``sync_targets.py script`` in ``src/iris/bin``
for our user management, syncing Iris's list of users from Oncall. If this
is too heavyweight for your use-case (or you're just starting to work with
Iris), we have a small user administration tool that can populate the Iris
database without setting up this sync script: iris-admin_.

Integrating Iris and Oncall
---------------------------

.. _Oncall: https://github.com/linkedin/oncall

Iris uses Oncall for two primary functions: user management and role lookup.

User management with Oncall is controlled via the ``sync_targets.py`` script in
``src/iris/bin``. This is configured with the ``oncall-api`` key in the Iris
config file. In our provided example ``config.dev.yaml``, this is set to
``localhost:8080``. Running the target sync script will sync all teams, users,
and user contact info from Oncall into Iris.

For role lookup, Iris queries Oncall with the ``oncall`` class in
``src/iris/role_lookup/oncall.py``. In an Iris plan, users can specify roles
such as "oncall-primary" and "oncall-secondary". Then, in the Iris sender,
Iris will look up the current on-call for the specified team using a REST API
call to Oncall. This is again configured with the ``oncall-api`` key in the 
Iris config file.

Development Setup of Iris and Oncall
------------------------------------
.. _oncall-admin: https://github.com/dwang159/oncall-admin

1. Set up MySQL for both Iris and Oncall. In both projects, database schemas and dummy data can be found in the ``db`` directory. These can be loaded with ``mysql -u  user -p < schema_0.sql``, and so on for the other sql files. You may need to toggle the ``ONLY_FULL_GROUP_BY`` MySQL mode with the query: ``SET GLOBAL sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));``

#. For both projects, install required dependencies in a virtualenv, then run them locally using ``make``.

#. Manage Oncall users, either using the LDAP sync script or with oncall-admin_. Load users and contact info into Oncall, then use the Oncall UI (hosted on ``localhost:8080`` by default) to create teams and on-call events/rotations.

#. Modify the Iris config file, changing the ``oncall-api`` key to the location where Oncall is being hosted (``localhost:8080`` by default). In addition, in the ``role_lookups`` key, uncomment the oncall line.

#. Using the Iris virtualenv, run the ``sync_targets.py`` script using ``make targets``. This should sync users from Oncall to Iris.

#. To test integration, use the Iris frontend (hosted at ``localhost:16649`` by default) to create an Iris plan using the "oncall-primary" role with a team defined in Oncall. Ensure this team has an active primary event in Oncall, then test the plan in the Iris UI. Running the Iris sender (``make sender``) should then result in  logged message sent to the primary on-call of the test team. 
