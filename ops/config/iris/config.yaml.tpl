server:
  disable_auth: True

role_lookup: dummy
metrics: dummy

# Change these to random long values when you run this in production
user_session:
  encrypt_key: 'abc'
  sign_key: '123'

#metrics: prometheus
#prometheus:
#  iris-sync-targets:
#    server_port: 8001
#  iris-sender:
#    server_port: 8002
#
#

#metrics: influx
#influxdb:
#  connect:
#    host: localhost
#    port: 8086
#    database: iris

db: &db
  conn:
    kwargs:
      scheme: mysql+pymysql

      # fill these in:
      user: ${mysql_db_user}
      password: ${mysql_db_pass}
      host: ${mysql_db_host}
      database: ${mysql_db_database_name}
      charset: utf8
    str: "%(scheme)s://%(user)s:%(password)s@%(host)s/%(database)s?charset=%(charset)s"
  query_limit: 500
  kwargs:
    pool_recycle: 3600
    echo: False
    pool_size: 100
    max_overflow: 100
    pool_timeout: 60
sender:
  debug: True
  host: 127.0.0.1
  port: 2321

vendors: []
#  - type: iris_twilio
#    name: twilio_1
#    account_sid: ''
#    auth_token: ''
#    twilio_number: ''
#    relay_base_url: ''

healthcheck_path: /home/iris/var/healthcheck_control
