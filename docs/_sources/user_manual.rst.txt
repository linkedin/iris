Iris user manual
================

Terminology
-----------

Message
```````

A message has a mode, a destination, and a text body. Messages are created when an incident is active, per the settings in the incident's plan, formatted using the plan's template.

Plan
````

Plans are used to create incidents and contain the escalation steps. Eg: Attempt reaching user 3 times, before escalating to the rest of their team.

Incident
````````

An incident is an ongoing event which escalates to users+teams, per configuration in the plan.

Template
````````

Templates are used by plans to structure and format messages. They use jinja2 to interpolate variables from the currently firing incident.

Claim
`````

Claiming an incident deactivates it and marks it as being owned by the user who claimed it.
